#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出 S3 Volume 上的文件
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.s3_config import S3Config


def create_s3_client(config: S3Config):
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


def list_files(prefix='', max_files=100):
    """列出指定前缀下的文件"""
    config = S3Config('runpods3')
    
    if not config.is_configured():
        print("❌ S3 未配置")
        return
    
    print(f"🔧 S3 配置")
    print(f"   Endpoint: {config.get_endpoint_url()}")
    print(f"   Volume: {config.volume_id}")
    print(f"   前缀: {prefix or '(根目录)'}")
    print()
    
    s3_client = create_s3_client(config)
    
    try:
        # 列出文件
        response = s3_client.list_objects_v2(
            Bucket=config.volume_id,
            Prefix=prefix,
            MaxKeys=max_files
        )
        
        if 'Contents' not in response:
            print(f"📂 目录为空或不存在")
            return
        
        files = response['Contents']
        total_size = sum(f['Size'] for f in files)
        
        print(f"📂 找到 {len(files)} 个文件 (总大小: {total_size / 1024 / 1024:.2f} MB)")
        print(f"{'='*80}\n")
        
        for i, obj in enumerate(files, 1):
            size_mb = obj['Size'] / 1024 / 1024
            print(f"[{i}] {obj['Key']}")
            print(f"    大小: {size_mb:.2f} MB")
            print(f"    修改时间: {obj['LastModified']}")
            print()
        
        if response.get('IsTruncated'):
            print(f"⚠️  还有更多文件未显示（超过 {max_files} 个）")
            
    except Exception as e:
        print(f"❌ 列出文件失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='列出 S3 Volume 上的文件')
    parser.add_argument(
        '--prefix',
        type=str,
        default='workspace/models/speaker-reg/',
        help='文件前缀（默认: workspace/models/speaker-reg/）'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=100,
        help='最多显示文件数（默认: 100）'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("S3 Volume 文件列表")
    print("="*80)
    print()
    
    list_files(args.prefix, args.max)


if __name__ == '__main__':
    main()
