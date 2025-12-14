#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键设置命令
"""
import sys
from .dependencies import install_dependencies
from .models import download_models


def handle_setup(args):
    """处理 setup 命令 - 一键设置项目（依赖+模型）"""
    print("=" * 60)
    print("🚀 一键设置项目")
    print("=" * 60)
    print(f"\n📦 项目: {args.project}\n")
    
    has_error = False
    
    # 1. 安装依赖
    if not args.skip_deps:
        print("步骤 1/2: 安装依赖")
        print("-" * 60)
        try:
            # 复制参数
            deps_args = type('obj', (object,), {
                'project': args.project,
                'mirror': args.mirror,
                'force': False,
                'deps_command': 'install'
            })()
            install_dependencies(deps_args)
        except SystemExit as e:
            if e.code != 0:
                print("\n⚠️  依赖安装失败，但继续模型下载...")
                has_error = True
        except Exception as e:
            print(f"\n⚠️  依赖安装出错: {e}")
            has_error = True
        print()
    else:
        print("⏭️  跳过依赖安装\n")
    
    # 2. 下载模型
    if not args.skip_models:
        print("步骤 2/2: 下载模型")
        print("-" * 60)
        try:
            # 复制参数
            models_args = type('obj', (object,), {
                'project': args.project,
                'force': False,
                'models_command': 'download'
            })()
            download_models(models_args)
        except SystemExit as e:
            if e.code != 0:
                print("\n⚠️  模型下载失败")
                has_error = True
        except Exception as e:
            print(f"\n⚠️  模型下载出错: {e}")
            has_error = True
        print()
    else:
        print("⏭️  跳过模型下载\n")
    
    # 总结
    print("=" * 60)
    if has_error:
        print("⚠️  设置完成（有警告）")
        print("=" * 60)
        print("\n💡 检查上方输出，解决失败的步骤")
        sys.exit(1)
    else:
        print("✅ 设置完成！")
        print("=" * 60)
        print(f"\n📝 下一步:")
        print(f"   1. 删除临时 Pod")
        print(f"   2. 在项目 Dockerfile.serverless 中配置环境变量")
        print(f"   3. 推送代码到 GitHub")
        print(f"   4. 在 RunPod Console 部署 Serverless Endpoint")
        print(f"\n查看详细文档: VOLUME_SETUP_GUIDE.md")
