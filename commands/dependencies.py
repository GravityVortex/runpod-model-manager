#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖管理命令
"""
import sys
import os
from projects.loader import get_project
from volume_manager import VolumeManager
from .utils import detect_volume_path


def handle_deps(args):
    """处理 deps 命令"""
    if args.deps_command == 'install':
        install_dependencies(args)
    elif args.deps_command == 'list':
        list_dependencies(args)
    elif args.deps_command == 'check':
        check_dependencies(args)
    else:
        print("❌ 未知的 deps 子命令")
        sys.exit(1)


def install_dependencies(args):
    """安装依赖"""
    print("=" * 60)
    print("🔧 依赖管理（增量）")
    print("=" * 60)
    
    # 获取项目配置
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 检查项目是否定义了依赖
    if not project.dependencies:
        print(f"⚠️  项目 {args.project} 未定义依赖列表")
        return
    
    # 检测 Volume 路径
    volume_path = detect_volume_path()
    manager = VolumeManager(volume_path)
    
    # 检查 Python 版本匹配
    import platform
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    required_version = project.python_version
    
    print(f"\n📦 项目: {args.project}")
    print(f"📂 Volume: {volume_path}")
    print(f"🐍 需要 Python: {required_version}")
    print(f"🐍 当前 Python: {current_version}")
    print(f"📊 定义依赖数: {len(project.dependencies)}")
    
    # 版本检查
    if current_version != required_version:
        print(f"\n⚠️  Python 版本不匹配！")
        print(f"   需要: {required_version}")
        print(f"   当前: {current_version}")
        
        import subprocess
        import shutil
        
        # 检查需要的版本是否已安装
        python_cmd = f"python{required_version}"
        if shutil.which(python_cmd):
            print(f"\n✅ 检测到系统已安装 Python {required_version}")
            print(f"   自动切换到 {python_cmd} 继续运行...")
            print()
            
            # 使用正确的 Python 版本重新运行
            new_cmd = [python_cmd, "volume_cli.py", "deps", "install", "--project", args.project]
            if args.mirror:
                new_cmd.extend(["--mirror", args.mirror])
            if args.force:
                new_cmd.append("--force")
            
            result = subprocess.run(new_cmd, cwd=os.getcwd())
            sys.exit(result.returncode)
        
        # 系统未安装，自动安装
        print(f"\n🔧 系统未安装 Python {required_version}")
        print(f"📥 开始自动安装...")
        print()
        
        try:
            # 更新包列表
            print(f"[1/3] 更新包列表...")
            result = subprocess.run(['apt-get', 'update'], 
                                   capture_output=True, 
                                   text=True,
                                   check=True)
            print(f"      ✓ 完成")
            
            # 安装 Python
            print(f"[2/3] 安装 Python {required_version}...")
            packages = [
                f'python{required_version}',
                f'python{required_version}-pip',
                f'python{required_version}-venv',
                f'python{required_version}-dev'
            ]
            result = subprocess.run(
                ['apt-get', 'install', '-y'] + packages,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"      ✓ 安装完成")
            
            # 验证安装
            print(f"[3/3] 验证安装...")
            result = subprocess.run(
                [f'python{required_version}', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            version_output = result.stdout.strip()
            print(f"      ✓ {version_output}")
            
            print(f"\n✅ Python {required_version} 安装成功！")
            print(f"   使用 python{required_version} 重新运行...")
            print()
            
            # 使用新安装的 Python 重新运行
            new_cmd = [f"python{required_version}", "volume_cli.py", "deps", "install", "--project", args.project]
            if args.mirror:
                new_cmd.extend(["--mirror", args.mirror])
            if args.force:
                new_cmd.append("--force")
            
            result = subprocess.run(new_cmd, cwd=os.getcwd())
            sys.exit(result.returncode)
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ 安装失败！")
            print(f"   错误信息: {e.stderr if e.stderr else str(e)}")
            print(f"\n可能原因:")
            print(f"   1. 权限不足（需要 root 权限）")
            print(f"   2. 网络问题")
            print(f"   3. 软件源中没有 Python {required_version}")
            print(f"\n手动解决:")
            print(f"   # 方案1: 使用 sudo")
            print(f"   sudo apt-get update")
            print(f"   sudo apt-get install -y python{required_version} python{required_version}-pip")
            print(f"\n   # 方案2: 使用当前版本")
            print(f"   修改项目配置: projects/{args.project.replace('-', '_')}/config.py")
            print(f"   python_version = '{current_version}'")
            sys.exit(1)
        except PermissionError:
            print(f"\n❌ 权限不足！")
            print(f"   需要 root 权限才能安装系统包")
            print(f"\n解决方案:")
            print(f"   # 使用 sudo 运行")
            print(f"   sudo python3 volume_cli.py deps install --project {args.project}")
            print(f"\n   # 或者在 RunPod Pod 终端中直接运行（通常已有 root 权限）")
            sys.exit(1)
    else:
        print(f"✅ Python 版本匹配")
    
    # 检查依赖变化
    changed, added, removed = manager.check_dependencies_changed(
        args.project, project.dependencies
    )
    
    if changed and not args.force:
        print(f"\n🔍 检测到依赖变化:")
        if added:
            print(f"  ➕ 新增: {len(added)}")
            for dep in sorted(added):
                print(f"     - {dep}")
        if removed:
            print(f"  ➖ 移除: {len(removed)}")
            for dep in sorted(removed):
                print(f"     - {dep}")
    elif args.force:
        print(f"\n🔄 强制重新安装模式")
    else:
        print(f"\n✅ 依赖已是最新")
    
    print()
    
    # 安装依赖（使用检查后的版本）
    try:
        result = manager.install_dependencies(
            args.project,
            project.dependencies,
            python_version=required_version,  # 使用检查后的版本
            mirror=args.mirror,
            force=args.force
        )
        
        # 显示结果
        print("\n" + "=" * 60)
        print("✅ 安装完成！")
        print("=" * 60)
        print(f"📊 统计: 总计 {result['total']}, 安装 {result['installed']}, 跳过 {result['skipped']}")
        
        print(f"\n📝 使用说明:")
        print(f"  FROM python:{required_version}")
        print(f"  ENV PYTHONPATH=/runpod-volume/python-deps/py{required_version}/{args.project}:$PYTHONPATH")
        
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        sys.exit(1)


def list_dependencies(args):
    """列出项目依赖"""
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    if not project.dependencies:
        print(f"⚠️  项目 {args.project} 未定义依赖列表")
        return
    
    print("=" * 60)
    print(f"📦 项目: {args.project}")
    print("=" * 60)
    print(f"🐍 Python 版本: {project.python_version}")
    print(f"📊 依赖数量: {len(project.dependencies)}\n")
    
    for i, dep in enumerate(project.dependencies, 1):
        print(f"{i:2d}. {dep}")


def check_dependencies(args):
    """检查依赖完整性"""
    volume_path = detect_volume_path()
    
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    if not project.dependencies:
        print(f"⚠️  项目 {args.project} 未定义依赖列表")
        return
    
    print("=" * 60)
    print(f"🔍 检查依赖完整性: {args.project}")
    print("=" * 60)
    
    # 依赖路径
    from pathlib import Path
    deps_path = Path(volume_path) / 'python-deps' / f'py{project.python_version}' / args.project
    
    if not deps_path.exists():
        print(f"\n❌ 依赖目录不存在: {deps_path}")
        print(f"\n💡 使用以下命令安装:")
        print(f"   python3 volume_cli.py deps install --project {args.project}")
        sys.exit(1)
    
    # 尝试导入依赖
    import sys
    sys.path.insert(0, str(deps_path))
    
    failed = []
    success = 0
    
    print()
    for dep in project.dependencies:
        # 提取包名（去掉版本号）
        pkg_name = dep.split('==')[0].split('>=')[0].split('<=')[0].strip()
        
        # 特殊处理包名映射
        import_name = pkg_name.replace('-', '_')
        
        try:
            __import__(import_name)
            print(f"✅ {pkg_name}")
            success += 1
        except ImportError as e:
            print(f"❌ {pkg_name}: {e}")
            failed.append(pkg_name)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 检查结果")
    print("=" * 60)
    print(f"✅ 成功: {success}")
    print(f"❌ 失败: {len(failed)}")
    
    if failed:
        print(f"\n缺失的包:")
        for pkg in failed:
            print(f"  - {pkg}")
        print(f"\n💡 重新安装:")
        print(f"   python3 volume_cli.py deps install --project {args.project} --force")
        sys.exit(1)
    else:
        print("\n✅ 所有依赖完整可用")
