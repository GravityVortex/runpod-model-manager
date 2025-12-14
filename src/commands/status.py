#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态查看命令
"""
import os
from src.volume_manager import VolumeManager
from .utils import detect_volume_path


def handle_status(args):
    """处理 status 命令"""
    volume_path = detect_volume_path()
    manager = VolumeManager(volume_path)
    
    print("=" * 60)
    print("📊 RunPod Volume 状态")
    print("=" * 60)
    print(f"📂 Volume 路径: {volume_path}\n")
    
    if args.project:
        # 显示单个项目
        stats = manager.get_project_stats(args.project)
        if not stats.get('dependencies_count') and not stats.get('models_count'):
            print(f"⚠️  项目 {args.project} 尚未安装")
            return
        
        print(f"📦 项目: {stats['project']}")
        print(f"   依赖: {stats['dependencies_count']} 个")
        if 'dependencies_size' in stats:
            print(f"   大小: {stats['dependencies_size']}")
        print(f"   模型: {stats['models_count']} 个")
        if stats.get('last_updated'):
            print(f"   更新: {stats['last_updated']}")
    else:
        # 显示所有项目
        projects = manager.list_projects()
        
        if not projects:
            print("⚠️  Volume 中没有已安装的项目")
            print("\n💡 使用以下命令安装项目:")
            print("   python3 volume_cli.py setup --project <项目名>")
            return
        
        print(f"已安装项目: {len(projects)}\n")
        for stats in projects:
            print(f"📦 {stats['project']}")
            print(f"   依赖: {stats['dependencies_count']} 个", end='')
            if 'dependencies_size' in stats:
                print(f" ({stats['dependencies_size']})")
            else:
                print()
            print(f"   模型: {stats['models_count']} 个")
            if stats.get('last_updated'):
                print(f"   更新: {stats['last_updated']}")
            print()
