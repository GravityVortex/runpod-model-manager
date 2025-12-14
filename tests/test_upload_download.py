#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件上传和下载功能（S3 API）

核心场景：把本地的某个文件上传到 RunPod Volume，然后再下载回来，并校验内容一致。
"""
import os
import sys
import tempfile
import shutil
import argparse
import hashlib
import uuid
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.s3_config import S3Config


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_s3_config(
    profile: str,
    datacenter: str | None,
    volume_id: str | None,
    endpoint_url: str | None,
) -> S3Config:
    config = S3Config(profile)
    if datacenter:
        config.config["datacenter"] = datacenter
    if volume_id:
        config.config["volume_id"] = volume_id
    if endpoint_url:
        config.config["endpoint_url"] = endpoint_url
    return config


def create_s3_client(config: S3Config):
    try:
        import boto3
        import botocore.config
        import urllib3
    except ImportError as e:
        raise ImportError("需要安装 boto3: pip install boto3") from e

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    boto_config = botocore.config.Config(
        signature_version="s3v4",
        retries={"max_attempts": 3, "mode": "standard"},
    )
    return boto3.client(
        "s3",
        aws_access_key_id=config.access_key,
        aws_secret_access_key=config.secret_key,
        region_name=config.get_region(),
        endpoint_url=config.get_endpoint_url(),
        config=boto_config,
        verify=False,
    )


def test_s3_config(config: S3Config):
    """测试 S3 配置加载"""
    print("\n" + "="*60)
    print("测试 1: S3 配置加载")
    print("="*60)
    
    if not config.is_configured():
        if not (config.access_key or config.secret_key or config.volume_id):
            print("⏭️  未配置 S3，跳过 S3 上传/下载测试")
            return None
        print("❌ S3 未配置或 S3 API 不可用")
        print("\n请配置 S3 凭证:")
        print("1. 创建 ~/.runpod_s3_config 文件")
        print("2. 或设置环境变量:")
        print("   export RUNPOD_S3_ACCESS_KEY=...")
        print("   export RUNPOD_S3_SECRET_KEY=...")
        print("   export RUNPOD_DATACENTER=...")
        print("   export RUNPOD_VOLUME_ID=...")
        print("   (可选) export RUNPOD_S3_ENDPOINT_URL=https://s3api-<datacenter>.runpod.io/")
        return False
    
    print(f"✅ S3 配置已加载")
    print(f"   Endpoint: {config.get_endpoint_url()}")
    print(f"   Region: {config.get_region()}")
    print(f"   Volume ID: {config.volume_id}")
    if not config.config.get("endpoint_url") and not config.is_datacenter_supported():
        print(f"⚠️  {config.get_unsupported_datacenter_message()}")
    return True


def test_s3_roundtrip(
    config: S3Config,
    local_file: Path | None,
    remote_key: str | None,
    models_subdir: str,
    keep_remote: bool,
):
    """测试：上传本地文件 -> 再下载 -> 校验内容一致"""
    print("\n" + "="*60)
    print("测试 2: S3 文件往返 (上传 + 下载 + 校验)")
    print("="*60)

    if not config.is_configured():
        print("❌ S3 未配置")
        return False

    try:
        from src.s3_uploader import upload_file, _build_remote_path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if local_file is None:
                local_file = temp_path / "test_upload_download_local_file.bin"
                local_file.write_bytes(os.urandom(128 * 1024))

            local_file = local_file.expanduser().resolve()
            if not local_file.exists() or not local_file.is_file():
                print(f"❌ 本地文件不存在: {local_file}")
                return False

            local_hash = sha256_file(local_file)
            if remote_key is None:
                remote_key = f"test_upload_download/{uuid.uuid4().hex}/{local_file.name}"

            # 使用新的上传模块
            success = upload_file(
                local_path=str(local_file),
                remote_key=remote_key,
                models_subdir=models_subdir,
                verbose=True
            )
            
            if not success:
                print("❌ 上传失败")
                return False

            # 下载并校验
            download_path = temp_path / "downloaded_file"
            full_remote_key = _build_remote_path(models_subdir, remote_key)
            
            s3_client = create_s3_client(config)
            print(f"\n📥 下载: s3://{config.volume_id}/{full_remote_key}")
            print(f"   -> {download_path}")
            s3_client.download_file(config.volume_id, full_remote_key, str(download_path))

            if not download_path.exists():
                print("❌ 下载后文件不存在")
                return False

            downloaded_hash = sha256_file(download_path)
            if downloaded_hash != local_hash:
                print("❌ 校验失败：下载文件内容与上传文件不一致")
                print(f"   local_sha256={local_hash}")
                print(f"   downl_sha256={downloaded_hash}")
                return False

            print("\n✅ 往返成功：上传/下载一致")
            print(f"   sha256={local_hash}")

            if not keep_remote:
                try:
                    s3_client.delete_object(Bucket=config.volume_id, Key=full_remote_key)
                    print("🧹 已清理远端测试文件")
                except Exception as e:
                    print(f"⚠️  清理远端测试文件失败（可忽略）: {e}")
            return True
    except Exception as e:
        print(f"\n❌ S3 往返测试失败: {e}")
        try:
            import botocore.exceptions
            if isinstance(e, botocore.exceptions.SSLError):
                print("提示：当前 S3 endpoint TLS 握手失败。通常是该 datacenter 未开通 S3 API 或 endpoint 不可用。")
                print("建议：在支持 S3 API 的 datacenter 创建新的 Volume，并更新 datacenter + volume_id 后重试。")
        except Exception:
            pass
        return False


def main():
    """运行所有测试"""
    parser = argparse.ArgumentParser(description="RunPod 文件上传/下载测试")
    parser.add_argument(
        "--require-s3",
        action="store_true",
        help="要求 S3 API 可用，否则视为失败（用于确认上传/下载链路）",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="runpods3",
        help="~/.runpod_s3_config 中的 profile 名称（默认: runpods3）",
    )
    parser.add_argument(
        "--datacenter",
        type=str,
        default=None,
        help="覆盖 datacenter（例如 US-IL-1）",
    )
    parser.add_argument(
        "--volume-id",
        type=str,
        default=None,
        help="覆盖 volume_id（例如 dkhgi7iqpu）",
    )
    parser.add_argument(
        "--endpoint-url",
        type=str,
        default=None,
        help="覆盖 endpoint_url（例如 https://s3api-us-il-1.runpod.io/）",
    )
    parser.add_argument(
        "--local-file",
        type=str,
        default=None,
        help="要上传的本地文件路径（不传则自动生成一个临时文件）",
    )
    parser.add_argument(
        "--remote-key",
        type=str,
        default=None,
        help="远端 object key（不传则自动生成，形如 test_upload_download/<uuid>/<filename>）",
    )
    parser.add_argument(
        "--keep-remote",
        action="store_true",
        help="不删除远端测试文件（默认会清理）",
    )
    parser.add_argument(
        "--models-subdir",
        type=str,
        default="/workspace/models",
        help="子目录前缀（默认: /workspace/models）",
    )
    args = parser.parse_args()

    print("="*60)
    print("RunPod 文件上传/下载测试")
    print("="*60)
    
    results = {}

    config = load_s3_config(
        profile=args.profile,
        datacenter=args.datacenter,
        volume_id=args.volume_id,
        endpoint_url=args.endpoint_url,
    )
    
    # 测试 1: S3 配置
    results['s3_config'] = test_s3_config(config)

    if args.require_s3 and not results['s3_config']:
        results['s3_config'] = False
    
    if not results['s3_config']:
        results['s3_roundtrip'] = None
    else:
        local_file = Path(args.local_file) if args.local_file else None
        results['s3_roundtrip'] = test_s3_roundtrip(
            config=config,
            local_file=local_file,
            remote_key=args.remote_key,
            models_subdir=args.models_subdir,
            keep_remote=args.keep_remote,
        )
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⏭️  跳过"
        elif result:
            status = "✅ 通过"
        else:
            status = "❌ 失败"
        print(f"{status} - {test_name}")
    
    # 返回状态码
    failed = [k for k, v in results.items() if v is False]
    if failed:
        print(f"\n❌ {len(failed)} 个测试失败")
        sys.exit(1)
    else:
        print(f"\n✅ 所有测试通过")
        sys.exit(0)


if __name__ == '__main__':
    main()
