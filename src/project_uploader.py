#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目模型上传器基类"""
import argparse
from typing import Optional
from src.s3_uploader import upload_directory
from src.projects.base import BaseProject


class ProjectUploader:
    """项目模型上传器"""
    
    @staticmethod
    def upload(
        project: BaseProject,
        models_dir: Optional[str] = None,
        volume_path: str = '/workspace'
    ) -> int:
        """
        上传项目模型到 S3
        
        Args:
            project: 项目配置对象
            models_dir: 本地模型目录（可选，覆盖项目配置）
            volume_path: Volume 挂载路径
        
        Returns:
            0: 成功, 1: 失败
        """
        local_dir = models_dir or project.local_models_dir
        if not local_dir:
            print("❌ 错误: 未指定本地模型目录")
            print("\n使用方式:")
            print("  python3 <script> --models-dir /path/to/models")
            print("\n或在 config.py 中配置 local_models_dir")
            return 1
        
        print(f"🚀 上传 {project.name} 模型到 S3\n")
        print(f"本地目录: {local_dir}")
        print(f"远程前缀: {project.models_remote_prefix}")
        print(f"Volume路径: {volume_path}/models/{project.models_remote_prefix}/\n")
        
        result = upload_directory(
            local_dir=local_dir,
            remote_prefix=project.models_remote_prefix,
            models_subdir=f'{volume_path}/models',
            include_parent_dir=False,
            verbose=True
        )
        
        print(f"\n{'='*60}")
        print(f"📊 上传完成: {result['success']}/{result['total']}")
        print(f"{'='*60}")
        
        if result['failed'] > 0:
            print(f"⚠️  {result['failed']} 个文件上传失败")
            return 1
        else:
            print(f"✅ 所有文件上传成功！")
            return 0
    
    @staticmethod
    def main_cli(project: BaseProject):
        """CLI 入口（供项目脚本调用）"""
        parser = argparse.ArgumentParser(
            description=f'上传 {project.name} 模型到 S3'
        )
        parser.add_argument(
            '--models-dir',
            help='本地模型目录（覆盖配置）'
        )
        parser.add_argument(
            '--volume-path',
            default='/workspace',
            help='Volume挂载路径（默认: /workspace）'
        )
        args = parser.parse_args()
        
        return ProjectUploader.upload(
            project,
            args.models_dir,
            args.volume_path
        )

