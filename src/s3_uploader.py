#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunPod S3 上传工具
提供可在代码中调用的上传方法，支持详细日志输出
"""
import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict

from src.s3_config import S3Config


def _sha256_file(path: Path) -> str:
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def _create_s3_client(config: S3Config):
    """创建 S3 客户端"""
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


def _build_remote_path(models_subdir: str, remote_key: str) -> str:
    """构建完整的远程路径"""
    subdir = models_subdir.strip('/')
    key = remote_key.strip('/')
    if subdir:
        return f"{subdir}/{key}"
    return key


class _ProgressCallback:
    """上传进度回调"""
    def __init__(self, file_size: int, verbose: bool = True):
        self.file_size = file_size
        self.verbose = verbose
        self.uploaded = 0
        self.start_time = time.time()
        self.last_print_time = 0

    def __call__(self, bytes_amount):
        self.uploaded += bytes_amount
        if not self.verbose:
            return
        
        current_time = time.time()
        if current_time - self.last_print_time < 1.0 and self.uploaded < self.file_size:
            return
        
        self.last_print_time = current_time
        percent = (self.uploaded / self.file_size) * 100
        elapsed = current_time - self.start_time
        speed = self.uploaded / elapsed if elapsed > 0 else 0
        
        print(f"   进度: {percent:.1f}% ({_format_size(self.uploaded)} / {_format_size(self.file_size)}) - {_format_size(speed)}/s", flush=True)


def upload_file(
    local_path: str,
    remote_key: str = None,
    models_subdir: str = '/workspace/models',
    profile: str = 'runpods3',
    verbose: bool = True
) -> bool:
    """
    上传单个文件到 RunPod S3

    Args:
        local_path: 本地文件路径
        remote_key: 远程对象键（可选，默认使用文件名）
        models_subdir: 子目录前缀（默认 '/workspace/models'）
        profile: S3 配置 profile
        verbose: 是否输出详细日志

    Returns:
        上传是否成功
    """
    local_file = Path(local_path).expanduser().resolve()
    
    if not local_file.exists() or not local_file.is_file():
        if verbose:
            print(f"❌ 本地文件不存在: {local_file}")
        return False
    
    # 加载配置
    config = S3Config(profile)
    if not config.is_configured():
        if verbose:
            print("❌ S3 未配置")
        return False
    
    # 生成 remote_key
    if remote_key is None:
        remote_key = local_file.name
    
    # 构建完整路径
    full_remote_key = _build_remote_path(models_subdir, remote_key)
    
    if verbose:
        file_size = local_file.stat().st_size
        print(f"\n📂 本地文件: {local_file}")
        print(f"   大小: {_format_size(file_size)}")
        
        print(f"\n🔧 S3 配置")
        print(f"   Endpoint: {config.get_endpoint_url()}")
        print(f"   Region: {config.get_region()}")
        print(f"   Volume: {config.volume_id}")
        
        print(f"\n📍 目标路径: {full_remote_key}")
        print(f"   完整 S3 路径: s3://{config.volume_id}/{full_remote_key}")
        
        print(f"\n📤 开始上传...")
    
    try:
        s3_client = _create_s3_client(config)
        start_time = time.time()
        
        # 上传文件
        callback = _ProgressCallback(local_file.stat().st_size, verbose) if verbose else None
        s3_client.upload_file(
            str(local_file),
            config.volume_id,
            full_remote_key,
            Callback=callback
        )
        
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"\n✅ 上传成功！")
            print(f"   耗时: {elapsed:.1f} 秒")
            if elapsed > 0:
                speed = local_file.stat().st_size / elapsed
                print(f"   平均速度: {_format_size(speed)}/s")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"\n❌ 上传失败: {e}")
        return False


def upload_directory(
    local_dir: str,
    remote_prefix: str = None,
    models_subdir: str = '/workspace/models',
    include_parent_dir: bool = False,
    profile: str = 'runpods3',
    verbose: bool = True
) -> Dict[str, int]:
    """
    上传整个目录到 RunPod S3

    Args:
        local_dir: 本地目录路径
        remote_prefix: 远程前缀（作为文件夹名）
        models_subdir: 子目录前缀（默认 '/workspace/models'）
        include_parent_dir: 是否包含父目录名（默认 False）
        profile: S3 配置 profile
        verbose: 是否输出详细日志

    Returns:
        {'total': int, 'success': int, 'failed': int}
    """
    local_path = Path(local_dir).expanduser().resolve()
    
    if not local_path.exists() or not local_path.is_dir():
        if verbose:
            print(f"❌ 本地目录不存在: {local_path}")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    # 收集所有文件
    files = []
    for item in local_path.rglob('*'):
        if item.is_file():
            files.append(item)
    
    if not files:
        if verbose:
            print(f"⚠️  目录为空: {local_path}")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    # 计算总大小
    total_size = sum(f.stat().st_size for f in files)
    
    if verbose:
        print(f"\n📂 本地目录: {local_path}")
        print(f"   文件数量: {len(files)}")
        print(f"   总大小: {_format_size(total_size)}")
    
    # 加载配置
    config = S3Config(profile)
    if not config.is_configured():
        if verbose:
            print("❌ S3 未配置")
        return {'total': len(files), 'success': 0, 'failed': len(files)}
    
    if verbose:
        print(f"\n🔧 S3 配置")
        print(f"   Endpoint: {config.get_endpoint_url()}")
        print(f"   Volume: {config.volume_id}")
    
    # 上传文件
    result = {'total': len(files), 'success': 0, 'failed': 0}
    s3_client = _create_s3_client(config)
    
    if verbose:
        print(f"\n📤 开始上传 {len(files)} 个文件...\n")
    
    # 使用 tqdm 进度条
    try:
        from tqdm import tqdm
        use_tqdm = verbose
    except ImportError:
        use_tqdm = False
    
    iterator = tqdm(files, desc="上传进度", unit="file", position=0, leave=True) if use_tqdm else files
    
    for file_path in iterator:
        # 计算相对路径
        rel_path = file_path.relative_to(local_path)
        
        # 构建远程路径
        if include_parent_dir:
            parent_name = local_path.name
            if remote_prefix:
                remote_key = f"{remote_prefix}/{parent_name}/{rel_path}"
            else:
                remote_key = f"{parent_name}/{rel_path}"
        else:
            if remote_prefix:
                remote_key = f"{remote_prefix}/{rel_path}"
            else:
                remote_key = str(rel_path)
        
        full_remote_key = _build_remote_path(models_subdir, remote_key)
        
        try:
            s3_client.upload_file(
                str(file_path),
                config.volume_id,
                full_remote_key
            )
            result['success'] += 1
            if use_tqdm:
                tqdm.write(f"✅ {file_path} → s3://{config.volume_id}/{full_remote_key}")
        except Exception as e:
            result['failed'] += 1
            if use_tqdm:
                tqdm.write(f"❌ {file_path} → s3://{config.volume_id}/{full_remote_key}: {e}")
    
    if verbose:
        print(f"{'='*60}")
        print(f"📊 上传完成")
        print(f"   总计: {result['total']} 个文件")
        print(f"   成功: {result['success']} 个")
        print(f"   失败: {result['failed']} 个")
    
    return result
