#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理命令
"""
import sys
import shutil
from pathlib import Path
from projects.loader import get_project
from .utils import detect_volume_path


def handle_clean(args):
    """处理 clean 命令"""
    if not (args.deps or args.models or args.all):
        print("❌ 请指定清理内容: --deps, --models, 或 --all")
        sys.exit(1)
    
    volume_path = detect_volume_path()
    
    # 获取项目配置（用于获取 Python 版本）
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("🗑️  清理项目数据")
    print("=" * 60)
    print(f"\n📦 项目: {args.project}")
    print(f"📂 Volume: {volume_path}\n")
    
    # 确认
    items_to_clean = []
    if args.all or args.deps:
        items_to_clean.append("依赖")
    if args.all or args.models:
        items_to_clean.append("模型")
    if args.all:
        items_to_clean.append("元数据")
    
    print(f"⚠️  将清理: {', '.join(items_to_clean)}")
    response = input("\n确认删除？(yes/N): ")
    
    if response.lower() != 'yes':
        print("已取消")
        return
    
    # 清理依赖
    if args.all or args.deps:
        deps_path = Path(volume_path) / 'python-deps' / f'py{project.python_version}' / args.project
        if deps_path.exists():
            print(f"\n🗑️  删除依赖: {deps_path}")
            shutil.rmtree(deps_path)
            print("  ✅ 已删除")
        else:
            print(f"\n⏭️  依赖目录不存在，跳过")
    
    # 清理模型（只清理元数据记录，不删除实际模型文件）
    if args.all or args.models:
        print(f"\n⚠️  注意: 模型文件被多项目共享，只清理元数据记录")
        metadata_file = Path(volume_path) / '.metadata' / f'{args.project}.json'
        if metadata_file.exists():
            # 读取元数据，只清空模型部分
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            model_count = len(metadata.get('models', {}))
            metadata['models'] = {}
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  ✅ 已清理 {model_count} 个模型记录")
        else:
            print(f"  ⏭️  元数据不存在，跳过")
    
    # 清理元数据
    if args.all:
        metadata_file = Path(volume_path) / '.metadata' / f'{args.project}.json'
        if metadata_file.exists():
            print(f"\n🗑️  删除元数据: {metadata_file}")
            metadata_file.unlink()
            print("  ✅ 已删除")
        else:
            print(f"\n⏭️  元数据文件不存在，跳过")
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 清理完成")
    print("=" * 60)
    
    if args.all or args.deps:
        print(f"\n💡 重新安装:")
        print(f"   python3 volume_cli.py setup --project {args.project}")
