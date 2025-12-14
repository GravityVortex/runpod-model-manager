#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理命令
"""
import sys
from src.projects.loader import get_project
from src.volume_manager import VolumeManager
from src.downloaders.factory import DownloaderFactory
from .utils import detect_volume_path


def handle_models(args):
    """处理 models 命令"""
    if args.models_command == 'download':
        download_models(args)
    elif args.models_command == 'list':
        list_models(args)
    elif args.models_command == 'verify':
        verify_models(args)
    else:
        print("❌ 未知的 models 子命令")
        sys.exit(1)


def download_models(args):
    """下载模型"""
    print("=" * 60)
    print("📥 模型下载")
    print("=" * 60)
    
    # 获取项目配置
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 检测 Volume 路径
    volume_path = detect_volume_path()
    manager = VolumeManager(volume_path)
    
    # 模型缓存路径
    from pathlib import Path
    model_cache = str(Path(volume_path) / 'models')
    
    print(f"\n📦 项目: {args.project}")
    print(f"📂 Volume: {volume_path}")
    print(f"📍 模型路径: {model_cache}")
    
    # 获取所有模型
    all_models = project.get_all_models()
    print(f"📊 模型数量: {len(all_models)}")
    
    # 检查变化
    changed, added, removed = manager.check_models_changed(
        args.project, project.models
    )
    
    if changed and not args.force:
        print(f"\n🔍 检测到模型变化:")
        if added:
            print(f"  ➕ 新增: {len(added)}")
            for model_id, source in added:
                print(f"     - {model_id} ({source})")
        if removed:
            print(f"  ➖ 移除: {len(removed)}")
            for model_id in removed:
                print(f"     - {model_id}")
    elif args.force:
        print(f"\n🔄 强制重新下载模式")
    
    print()
    
    # 下载模型
    success = 0
    skipped = 0
    failed = []
    
    for i, (model_id, source) in enumerate(all_models, 1):
        print(f"[{i}/{len(all_models)}] {model_id} ({source})")
        
        # 获取下载器
        try:
            downloader = DownloaderFactory.get_downloader(source, model_cache)
        except ValueError as e:
            print(f"  ❌ {e}")
            failed.append(model_id)
            continue
        
        # 检查是否已存在
        if not args.force and manager.check_model_exists(model_id, source):
            print(f"  ⏭️  已存在，跳过")
            skipped += 1
            # 注册到元数据
            manager.register_model(args.project, model_id, source)
            continue
        
        # 下载
        if downloader.download(model_id):
            print(f"  ✅ 下载完成")
            success += 1
            # 注册到元数据
            manager.register_model(args.project, model_id, source)
        else:
            failed.append(model_id)
    
    # 统计
    print("\n" + "=" * 60)
    print("📊 下载统计")
    print("=" * 60)
    print(f"✅ 下载成功: {success}")
    print(f"⏭️  跳过（已存在）: {skipped}")
    if failed:
        print(f"❌ 失败: {len(failed)}")
        for model in failed:
            print(f"  - {model}")
        sys.exit(1)
    else:
        print("\n✅ 所有模型下载完成")


def list_models(args):
    """列出项目模型"""
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    all_models = project.get_all_models()
    
    print("=" * 60)
    print(f"📦 项目: {args.project}")
    print("=" * 60)
    print(f"📊 模型数量: {len(all_models)}\n")
    
    # 按源分组显示
    from collections import defaultdict
    models_by_source = defaultdict(list)
    for model_id, source in all_models:
        models_by_source[source].append(model_id)
    
    for source, models in models_by_source.items():
        print(f"📁 {source.upper()} ({len(models)} 个)")
        for i, model_id in enumerate(models, 1):
            print(f"   {i}. {model_id}")
        print()


def verify_models(args):
    """验证模型完整性"""
    volume_path = detect_volume_path()
    manager = VolumeManager(volume_path)
    
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    all_models = project.get_all_models()
    
    print("=" * 60)
    print(f"🔍 验证模型完整性: {args.project}")
    print("=" * 60)
    print()
    
    missing = []
    success = 0
    
    for i, (model_id, source) in enumerate(all_models, 1):
        exists = manager.check_model_exists(model_id, source)
        status = "✅" if exists else "❌"
        print(f"{status} [{i}/{len(all_models)}] {model_id}")
        
        if exists:
            success += 1
        else:
            missing.append(model_id)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 验证结果")
    print("=" * 60)
    print(f"✅ 存在: {success}")
    print(f"❌ 缺失: {len(missing)}")
    
    if missing:
        print(f"\n缺失的模型:")
        for model in missing:
            print(f"  - {model}")
        print(f"\n💡 下载缺失的模型:")
        print(f"   python3 volume_cli.py models download --project {args.project}")
        sys.exit(1)
    else:
        print("\n✅ 所有模型完整可用")
