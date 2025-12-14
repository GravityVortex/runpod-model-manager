#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传 speaker-reg 模型到 RunPod S3
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.s3_uploader import upload_directory


def main():
    """上传 speaker-reg 模型"""
    local_dir = '/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/speaker-reg/models'
    
    print("🚀 开始上传 speaker-reg 模型到 S3\n")
    
    result = upload_directory(
        local_dir=local_dir,
        remote_prefix='speaker-reg',
        models_subdir='/workspace/models',
        include_parent_dir=False,
        verbose=True
    )
    
    print(f"\n{'='*60}")
    print(f"📊 上传完成")
    print(f"{'='*60}")
    print(f"总计: {result['total']} 个文件")
    print(f"成功: {result['success']} 个")
    print(f"失败: {result['failed']} 个")
    
    if result['failed'] > 0:
        print(f"\n⚠️  警告: {result['failed']} 个文件上传失败")
        return 1
    else:
        print(f"\n✅ 所有文件上传成功！")
        print(f"S3 路径: s3://dkhgi7iqpu/workspace/models/speaker-reg/")
        return 0


if __name__ == '__main__':
    exit(main())
