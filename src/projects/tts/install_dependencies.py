#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装 TTS 项目依赖
快捷脚本，封装 volume_cli.py deps install 命令
"""
import sys
import subprocess
from pathlib import Path


def find_project_root():
    """向上查找项目根目录（包含 volume_cli.py）"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / 'volume_cli.py').exists():
            return current
        current = current.parent
    raise FileNotFoundError("找不到项目根目录（volume_cli.py）")


def main():
    """主函数"""
    try:
        project_root = find_project_root()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    
    # 构建命令
    cmd = [
        sys.executable,
        str(project_root / 'volume_cli.py'),
        'deps', 'install',
        '--project', 'tts'
    ]
    
    # 传递命令行参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    print(f"🚀 安装 TTS 项目依赖")
    print(f"📂 项目根目录: {project_root}")
    print(f"💻 执行命令: {' '.join(cmd)}\n")
    
    # 执行命令
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())

