#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖管理命令
"""
import sys
import os
from src.projects.loader import get_project
from src.volume_manager import VolumeManager
from .utils import detect_volume_path


def handle_deps(args):
    """处理 deps 命令"""
    if args.deps_command == 'install':
        install_dependencies(args)
    elif args.deps_command == 'list':
        list_dependencies(args)
    elif args.deps_command == 'check':
        check_dependencies(args)
    elif args.deps_command == 'status':
        check_task_status(args)
    elif args.deps_command == 'stop':
        stop_task(args)
    else:
        print("❌ 未知的 deps 子命令")
        sys.exit(1)


def install_dependencies(args):
    """安装依赖"""
    # 检查是否为异步模式
    if hasattr(args, 'async_mode') and args.async_mode:
        # 异步模式：启动后台任务
        from src.task_manager import TaskManager
        
        volume_path = detect_volume_path()
        task_manager = TaskManager(volume_path)
        
        # 构建命令参数（移除 --async）
        command_args = sys.argv.copy()
        
        # 启动后台任务
        task_info = task_manager.start_background_task(command_args)
        
        print("=" * 60)
        print("🚀 后台任务已启动")
        print("=" * 60)
        print(f"📋 任务ID: {task_info['task_id']}")
        print(f"📝 日志文件: {task_info['log_file']}")
        print(f"\n查看进度:")
        print(f"  python3 volume_cli.py deps status {task_info['task_id']}")
        print(f"\n实时跟踪日志:")
        print(f"  tail -f {task_info['log_file']}")
        return
    
    # 同步模式：正常执行
    print("=" * 60)
    print("🔧 依赖管理（增量）")
    print("=" * 60)
    
    # 获取项目配置
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 检查项目是否定义了依赖配置
    if not project.dependencies_config:
        print(f"⚠️  项目 {args.project} 未定义依赖配置文件 (dependencies.yaml)")
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
    print(f"📝 配置文件: {project.dependencies_config}")
    
    from pathlib import Path
    if not Path(project.dependencies_config).exists():
        print(f"❌ 配置文件不存在: {project.dependencies_config}")
        sys.exit(1)
    print(f"✅ 配置文件存在")
    
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
            
            # 检查新版本是否有管理工具依赖
            print(f"\n📦 检查 {python_cmd} 的管理工具依赖...")
            check_cmd = [python_cmd, "-c", "import yaml, modelscope, huggingface_hub"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                print(f"⚠️  {python_cmd} 缺少管理工具依赖")
                print(f"🔧 自动安装根目录依赖到 {python_cmd}...")
                print()
                
                # 自动安装根目录依赖
                root_requirements = os.path.join(os.getcwd(), "requirements.txt")
                install_cmd = [python_cmd, "-m", "pip", "install", "-r", root_requirements]
                
                print(f"💻 命令: {' '.join(install_cmd)}")
                install_result = subprocess.run(install_cmd)
                
                if install_result.returncode != 0:
                    print(f"\n❌ 管理工具依赖安装失败")
                    print(f"\n请手动安装后重试:")
                    print(f"   {python_cmd} -m pip install -r requirements.txt")
                    print(f"\n或切换到已安装依赖的 Python 版本")
                    sys.exit(1)
                
                print(f"\n✅ 管理工具依赖安装完成")
            else:
                print(f"✅ 管理工具依赖已安装")
            
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
            
            # 自动安装管理工具依赖
            print(f"\n📦 安装管理工具依赖到新的 Python 版本...")
            root_requirements = os.path.join(os.getcwd(), "requirements.txt")
            install_cmd = [f"python{required_version}", "-m", "pip", "install", "-r", root_requirements]
            
            print(f"💻 命令: {' '.join(install_cmd)}")
            install_result = subprocess.run(install_cmd)
            
            if install_result.returncode != 0:
                print(f"\n❌ 管理工具依赖安装失败")
                print(f"\n请手动安装后重试:")
                print(f"   python{required_version} -m pip install -r requirements.txt")
                print(f"\n或切换到已安装依赖的 Python 版本")
                sys.exit(1)
            
            print(f"✅ 管理工具依赖安装完成")
            
            print(f"\n   使用 python{required_version} 重新运行...")
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
    
    # 安装依赖（使用 venv + uv）
    try:
        from src.venv_manager import VenvManager
        
        if args.force:
            print(f"\n⚠️  使用 --force 参数，将强制重新安装所有依赖")
        
        # 创建/检测 venv
        venv_mgr = VenvManager(volume_path)
        venv_path = venv_mgr.ensure_venv(args.project, required_version)
        
        print(f"\n📦 使用 uv 安装依赖到 venv...")
        result = venv_mgr.install_from_yaml(
            venv_path,
            project.dependencies_config,
            mirror=args.mirror,
            force=args.force
        )
        
        # 显示结果
        print("\n" + "=" * 60)
        print("✅ 安装完成！")
        print("=" * 60)
        print(f"📊 统计: 总计 {result['total']}, 安装 {result['installed']}, 失败 {result['failed']}")
        if result.get('groups'):
            print(f"\n分组安装结果:")
            for group, success in result['groups'].items():
                status = "✅" if success else "❌"
                print(f"  {status} {group}")
        
        print(f"\n📝 使用说明（业务侧 Dockerfile）:")
        print(f"  FROM python:{required_version}")
        print(f"  # 方式 1: 激活 venv（推荐）")
        print(f"  ENV VIRTUAL_ENV=/runpod-volume/venvs/py{required_version}-{args.project}")
        print(f"  ENV PATH=\"$VIRTUAL_ENV/bin:$PATH\"")
        print(f"  ")
        print(f"  # 方式 2: 直接用 venv 的 python")
        print(f"  CMD [\"/runpod-volume/venvs/py{required_version}-{args.project}/bin/python\", \"app.py\"]")
        
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def list_dependencies(args):
    """列出项目依赖"""
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    if not project.dependencies_config:
        print(f"⚠️  项目 {args.project} 未定义依赖配置文件")
        return
    
    from pathlib import Path
    import yaml
    
    config_file = Path(project.dependencies_config)
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("=" * 60)
    print(f"📦 项目: {args.project}")
    print("=" * 60)
    print(f"🐍 Python 版本: {project.python_version}")
    print(f"📝 配置文件: {project.dependencies_config}\n")
    
    groups = config.get('groups', {})
    install_order = config.get('install_order', list(groups.keys()))
    
    total_packages = 0
    for group_name in install_order:
        if group_name not in groups:
            continue
        
        group_config = groups[group_name]
        packages = group_config.get('packages', [])
        index_url = group_config.get('index_url')
        description = group_config.get('description', '')
        
        print(f"{'─'*60}")
        print(f"📦 组: {group_name}")
        if description:
            print(f"   {description}")
        if index_url:
            print(f"   索引: {index_url}")
        print(f"   包数量: {len(packages)}")
        print(f"{'─'*60}")
        
        for i, pkg in enumerate(packages, 1):
            print(f"  {i:2d}. {pkg}")
        
        print()
        total_packages += len(packages)
    
    print("=" * 60)
    print(f"📊 总计: {total_packages} 个包")
    print("=" * 60)


def check_dependencies(args):
    """检查依赖完整性"""
    volume_path = detect_volume_path()
    
    try:
        project = get_project(args.project)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    if not project.dependencies_config:
        print(f"⚠️  项目 {args.project} 未定义依赖配置文件")
        return
    
    from pathlib import Path
    import yaml
    
    config_file = Path(project.dependencies_config)
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("=" * 60)
    print(f"🔍 检查依赖完整性: {args.project}")
    print("=" * 60)
    
    # 依赖路径
    deps_path = Path(volume_path) / 'python-deps' / f'py{project.python_version}' / args.project
    
    if not deps_path.exists():
        print(f"\n❌ 依赖目录不存在: {deps_path}")
        print(f"\n💡 使用以下命令安装:")
        print(f"   python3 volume_cli.py deps install --project {args.project}")
        sys.exit(1)
    
    # 获取所有依赖包
    groups = config.get('groups', {})
    all_packages = []
    for group_name, group_config in groups.items():
        packages = group_config.get('packages', [])
        all_packages.extend(packages)
    
    if not all_packages:
        print(f"\n⚠️  配置文件中没有定义依赖包")
        return
    
    # 尝试导入依赖
    import sys
    sys.path.insert(0, str(deps_path))
    
    failed = []
    success = 0
    
    print()
    for dep in all_packages:
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
        print(f"   python3 volume_cli.py deps install --project {args.project}")
        sys.exit(1)
    else:
        print("\n✅ 所有依赖完整可用")


def check_task_status(args):
    """检查任务状态"""
    from src.task_manager import TaskManager
    
    volume_path = detect_volume_path()
    task_manager = TaskManager(volume_path)
    
    # 如果没有提供任务ID，列出所有任务
    if not hasattr(args, 'task_id') or not args.task_id:
        tasks = task_manager.list_tasks()
        if not tasks:
            print("📋 没有找到任何任务")
            return
        
        print("=" * 60)
        print("📋 任务列表")
        print("=" * 60)
        for task in tasks[:10]:  # 只显示最近10个
            status_icon = {
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'unknown': '❓'
            }.get(task.get('status', 'unknown'), '❓')
            
            print(f"\n{status_icon} {task['task_id']}")
            print(f"   命令: {task['command']}")
            print(f"   开始: {task['started_at']}")
            print(f"   状态: {task['status']}")
        
        print(f"\n💡 查看详情:")
        print(f"   python3 volume_cli.py deps status <task_id>")
        return
    
    # 获取任务状态
    try:
        task_info = task_manager.get_task_status(args.task_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 显示任务信息
    print("=" * 60)
    print(f"📋 任务: {task_info['task_id']}")
    print("=" * 60)
    print(f"📦 命令: {task_info['command']}")
    print(f"⏱️  开始时间: {task_info['started_at']}")
    
    status_icon = {
        'running': '🔄 运行中',
        'completed': '✅ 已完成',
        'failed': '❌ 失败',
        'unknown': '❓ 未知'
    }.get(task_info['status'], '❓ 未知')
    print(f"🔄 状态: {status_icon}")
    
    if task_info.get('completed_at'):
        print(f"⏱️  完成时间: {task_info['completed_at']}")
    
    # 显示进度
    progress = task_info.get('progress', {})
    if progress.get('total_groups', 0) > 0:
        print(f"\n📊 进度:")
        current_group = progress.get('current_group', 'N/A')
        completed = progress.get('completed_groups', 0)
        total = progress.get('total_groups', 0)
        
        if current_group:
            print(f"  当前组: {current_group} ({completed}/{total})")
        
        # 进度条
        if total > 0:
            percentage = int((completed / total) * 100)
            bar_length = 20
            filled = int((completed / total) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"  总进度: {percentage}% {bar}")
        
        # 统计
        print(f"\n📈 统计:")
        print(f"  ✅ 成功: {progress.get('success_count', 0)} 组")
        print(f"  ❌ 失败: {progress.get('failed_count', 0)} 组")
        if progress.get('retry_count', 0) > 0:
            print(f"  🔄 重试: {progress.get('retry_count', 0)} 次")
    
    # 日志文件
    print(f"\n💡 实时日志:")
    print(f"  tail -f {task_info['log_file']}")


def stop_task(args):
    """停止任务"""
    from src.task_manager import TaskManager
    
    volume_path = detect_volume_path()
    task_manager = TaskManager(volume_path)
    
    if not hasattr(args, 'task_id') or not args.task_id:
        print("❌ 请提供任务ID")
        print("\n💡 查看所有任务:")
        print("   python3 volume_cli.py deps status")
        sys.exit(1)
    
    try:
        force = hasattr(args, 'force') and args.force
        success = task_manager.stop_task(args.task_id, force=force)
        
        if success:
            print("=" * 60)
            print("✅ 任务已停止")
            print("=" * 60)
            print(f"📋 任务ID: {args.task_id}")
            if force:
                print("⚠️  使用强制终止 (SIGKILL)")
            else:
                print("✅ 优雅终止 (SIGTERM)")
        else:
            print("=" * 60)
            print("⚠️  任务未运行")
            print("=" * 60)
            print(f"📋 任务ID: {args.task_id}")
            print("💡 任务可能已经完成或停止")
    
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 停止任务失败: {e}")
        sys.exit(1)

