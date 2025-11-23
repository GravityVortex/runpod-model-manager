#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunPod Volume 统一管理 CLI
提供模型和依赖的统一管理入口
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """主命令入口"""
    parser = argparse.ArgumentParser(
        prog='volume',
        description='RunPod Volume 统一管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看状态
  python3 volume_cli.py status
  
  # 安装项目依赖
  python3 volume_cli.py deps install --project speaker-diarization
  
  # 下载项目模型
  python3 volume_cli.py models download --project speaker-diarization
  
  # 一键设置（依赖+模型）
  python3 volume_cli.py setup --project speaker-diarization
"""
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令'
    )
    
    # ==================== status 命令 ====================
    status_parser = subparsers.add_parser(
        'status',
        help='查看 Volume 状态'
    )
    status_parser.add_argument(
        '--project',
        help='查看指定项目（不指定则显示所有）'
    )
    
    # ==================== deps 命令组 ====================
    deps_parser = subparsers.add_parser(
        'deps',
        help='依赖管理'
    )
    deps_subparsers = deps_parser.add_subparsers(
        dest='deps_command',
        help='依赖操作'
    )
    
    # deps install
    deps_install_parser = deps_subparsers.add_parser(
        'install',
        help='安装项目依赖'
    )
    deps_install_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    deps_install_parser.add_argument(
        '--mirror',
        default='https://pypi.tuna.tsinghua.edu.cn/simple',
        help='PyPI 镜像源'
    )
    deps_install_parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新安装'
    )
    
    # deps list
    deps_list_parser = deps_subparsers.add_parser(
        'list',
        help='列出项目依赖'
    )
    deps_list_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    
    # deps check
    deps_check_parser = deps_subparsers.add_parser(
        'check',
        help='检查依赖完整性'
    )
    deps_check_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    
    # ==================== models 命令组 ====================
    models_parser = subparsers.add_parser(
        'models',
        help='模型管理'
    )
    models_subparsers = models_parser.add_subparsers(
        dest='models_command',
        help='模型操作'
    )
    
    # models download
    models_download_parser = models_subparsers.add_parser(
        'download',
        help='下载项目模型'
    )
    models_download_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    models_download_parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新下载'
    )
    
    # models list
    models_list_parser = models_subparsers.add_parser(
        'list',
        help='列出项目模型'
    )
    models_list_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    
    # models verify
    models_verify_parser = models_subparsers.add_parser(
        'verify',
        help='验证模型完整性'
    )
    models_verify_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    
    # ==================== setup 命令 ====================
    setup_parser = subparsers.add_parser(
        'setup',
        help='一键设置（安装依赖+下载模型）'
    )
    setup_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    setup_parser.add_argument(
        '--mirror',
        default='https://pypi.tuna.tsinghua.edu.cn/simple',
        help='PyPI 镜像源'
    )
    setup_parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='跳过依赖安装'
    )
    setup_parser.add_argument(
        '--skip-models',
        action='store_true',
        help='跳过模型下载'
    )
    
    # ==================== clean 命令 ====================
    clean_parser = subparsers.add_parser(
        'clean',
        help='清理项目数据'
    )
    clean_parser.add_argument(
        '--project',
        required=True,
        help='项目名称'
    )
    clean_parser.add_argument(
        '--deps',
        action='store_true',
        help='清理依赖'
    )
    clean_parser.add_argument(
        '--models',
        action='store_true',
        help='清理模型'
    )
    clean_parser.add_argument(
        '--all',
        action='store_true',
        help='清理所有（依赖+模型+元数据）'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 分发到对应的命令处理器
    try:
        if args.command == 'status':
            from commands.status import handle_status
            handle_status(args)
        
        elif args.command == 'deps':
            from commands.dependencies import handle_deps
            handle_deps(args)
        
        elif args.command == 'models':
            from commands.models import handle_models
            handle_models(args)
        
        elif args.command == 'setup':
            from commands.setup import handle_setup
            handle_setup(args)
        
        elif args.command == 'clean':
            from commands.clean import handle_clean
            handle_clean(args)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
