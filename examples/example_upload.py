#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S3 上传示例脚本
演示如何在代码中调用上传功能
"""
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.s3_uploader import upload_file, upload_directory


def example_upload_file():
    """示例：上传单个文件"""
    print("="*60)
    print("示例 1: 上传单个文件")
    print("="*60)
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是一个测试文件\n" * 100)
        test_file = f.name
    
    try:
        # 上传到默认子目录 /workspace/models
        success = upload_file(
            local_path=test_file,
            remote_key='example/test.txt',
            models_subdir='/workspace/models'
        )
        
        if success:
            print("\n✅ 文件上传成功！")
            print(f"   S3 路径: s3://dkhgi7iqpu/workspace/models/example/test.txt")
        else:
            print("\n❌ 文件上传失败")
    finally:
        Path(test_file).unlink()


def example_upload_directory():
    """示例：上传整个目录"""
    print("\n" + "="*60)
    print("示例 2: 上传整个目录")
    print("="*60)
    
    # 创建测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建一些测试文件
        (temp_path / 'config.json').write_text('{"model": "test"}')
        (temp_path / 'model.bin').write_bytes(b'model data' * 100)
        
        # 创建子目录
        subdir = temp_path / 'tokenizer'
        subdir.mkdir()
        (subdir / 'vocab.txt').write_text('vocab\ndata\n')
        
        # 上传目录（不包含父目录名）
        result = upload_directory(
            local_dir=str(temp_path),
            remote_prefix='example-model',
            models_subdir='/workspace/models',
            include_parent_dir=False
        )
        
        print(f"\n✅ 目录上传完成！")
        print(f"   成功: {result['success']}/{result['total']} 个文件")
        print(f"   S3 路径: s3://dkhgi7iqpu/workspace/models/example-model/")


def main():
    """主函数"""
    print("\n🚀 S3 上传功能演示\n")
    
    # 示例 1: 上传单个文件
    example_upload_file()
    
    # 示例 2: 上传整个目录
    example_upload_directory()
    
    print("\n" + "="*60)
    print("✅ 所有示例执行完成")
    print("="*60)


if __name__ == '__main__':
    main()
