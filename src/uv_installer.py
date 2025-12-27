#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv 包装器 - 自动检测、安装和降级
"""
import subprocess
import shutil
from typing import List, Optional


class UvInstaller:
    """uv 安装器包装类"""
    
    def __init__(self):
        self._uv_available = None
        self._check_uv()
    
    def _check_uv(self) -> bool:
        """检查 uv 是否可用"""
        if self._uv_available is not None:
            return self._uv_available
        
        self._uv_available = shutil.which('uv') is not None
        return self._uv_available
    
    def _install_uv(self) -> bool:
        """尝试安装 uv"""
        print("📦 检测到 uv 未安装，正在自动安装...")
        try:
            # 使用官方安装脚本
            result = subprocess.run(
                ['curl', '-LsSf', 'https://astral.sh/uv/install.sh'],
                capture_output=True,
                check=True
            )
            subprocess.run(['sh'], input=result.stdout, check=True)
            
            # 重新检查
            self._uv_available = shutil.which('uv') is not None
            if self._uv_available:
                print("✅ uv 安装成功")
                return True
            else:
                print("⚠️  uv 安装后未在 PATH 中找到，降级到 pip")
                return False
        except Exception as e:
            print(f"⚠️  uv 安装失败: {e}，降级到 pip")
            self._uv_available = False
            return False
    
    def get_install_command(self, pip_args: List[str]) -> List[str]:
        """
        获取安装命令
        
        Args:
            pip_args: pip 命令参数列表，如 ['pip', 'install', 'package']
        
        Returns:
            uv 或 pip 命令列表
        """
        # 如果 uv 不可用，尝试安装
        if not self._check_uv():
            self._install_uv()
        
        # 如果 uv 可用，转换命令
        if self._uv_available:
            # 将 ['pip', 'install', ...] 转换为 ['uv', 'pip', 'install', ...]
            if pip_args[0] == 'pip':
                return ['uv'] + pip_args
            else:
                return ['uv', 'pip'] + pip_args[1:]
        
        # 降级到 pip
        return pip_args


# 全局单例
_uv_installer = None


def get_uv_installer() -> UvInstaller:
    """获取全局 uv 安装器实例"""
    global _uv_installer
    if _uv_installer is None:
        _uv_installer = UvInstaller()
    return _uv_installer


def get_pip_command(base_args: List[str]) -> List[str]:
    """
    获取优化后的 pip 安装命令（优先使用 uv）
    
    Args:
        base_args: 基础 pip 命令参数，如 ['pip', 'install', ...]
    
    Returns:
        优化后的命令列表
    """
    return get_uv_installer().get_install_command(base_args)

