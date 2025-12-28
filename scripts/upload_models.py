#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的模型上传脚本
支持所有项目的本地模型上传
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.projects.loader import get_project


def main():
    """统一上传入口"""
    parser = argparse.ArgumentParser(description='上传本地模型到 RunPod Volume')
    parser.add_argument('--project', required=True, help='项目名称')
    parser.add_argument('--remote-host', required=True, help='SSH 连接 (user@host:port)')
    parser.add_argument('--remote-volume', default='/workspace', help='远程 volume 路径')
    
    args = parser.parse_args()
    
    print(f"🚀 上传项目: {args.project}\n")
    
    # 获取项目配置
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    
    # 上传模型
    success = project.upload_models(
        remote_host=args.remote_host,
        remote_volume=args.remote_volume
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())


