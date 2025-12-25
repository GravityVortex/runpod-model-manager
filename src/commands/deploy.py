#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一站式部署命令
"""
import sys
from src.projects.loader import get_project
from src.project_uploader import ProjectUploader


def handle_deploy(args):
    """处理 deploy 命令"""
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    print("="*60)
    print(f"🚀 一站式部署: {project.name}")
    print("="*60)
    
    # 1. 上传模型
    if not args.skip_upload:
        print(f"\n[1/4] 📤 上传模型到 S3")
        print("─"*60)
        result = ProjectUploader.upload(
            project,
            args.models_dir,
            args.volume_path
        )
        if result != 0:
            print("\n⚠️  模型上传失败，但继续输出部署指南...")
    else:
        print(f"\n[1/4] ⏭️  跳过模型上传")
    
    # 2. 输出依赖安装指南
    print(f"\n[2/4] 📋 临时 Pod 依赖安装命令")
    print("─"*60)
    print("在 RunPod 控制台创建临时 Pod，执行以下命令：\n")
    print("  git clone https://github.com/xxx/runpod-model-manager.git")
    print("  cd runpod-model-manager")
    print("  pip install -r requirements.txt")
    print(f"  python3 volume_cli.py deps install --project {project.name}")
    
    # 3. 输出验证清单
    print(f"\n[3/4] ✅ 验证清单")
    print("─"*60)
    print(f"□ 模型: {args.volume_path}/models/{project.models_remote_prefix}/")
    print(f"□ 依赖: {args.volume_path}/python-deps/py{project.python_version}/{project.name}/")
    print(f"\n验证命令:")
    print(f"  python3 volume_cli.py status --project {project.name}")
    
    # 4. 输出业务容器配置
    print(f"\n[4/4] 🐳 业务容器配置")
    print("─"*60)
    print("# handler.py")
    print("import sys")
    print(f"sys.path.insert(0, '{args.volume_path}/python-deps/py{project.python_version}/{project.name}')")
    print("\nimport os")
    print(f"os.environ['MODELSCOPE_CACHE'] = '{args.volume_path}/models'")
    
    print(f"\n{'='*60}")
    print("✅ 部署指南已生成")
    print("="*60)

