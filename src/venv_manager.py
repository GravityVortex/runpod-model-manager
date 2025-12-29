#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Venv 管理器 - 使用 uv 创建和管理虚拟环境
"""
import os
import subprocess
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class VenvManager:
    """虚拟环境管理器 - 基于 uv"""
    
    def __init__(self, volume_path: str):
        """
        初始化
        
        Args:
            volume_path: Volume 挂载路径
        """
        self.volume_path = Path(volume_path)
        self.venvs_dir = self.volume_path / 'venvs'
        self.venvs_dir.mkdir(parents=True, exist_ok=True)
    
    def _check_uv_installed(self):
        """检查 uv 是否已安装"""
        if not shutil.which('uv'):
            raise RuntimeError(
                "未检测到 uv 工具\n"
                "请先安装 uv:\n"
                "  curl -LsSf https://astral.sh/uv/install.sh | sh\n"
                "或:\n"
                "  pip install uv"
            )
    
    def get_venv_path(self, project_name: str, python_version: str) -> Path:
        """
        获取 venv 路径
        
        Args:
            project_name: 项目名称
            python_version: Python 版本（如 '3.10'）
        
        Returns:
            venv 路径
        """
        return self.venvs_dir / f'py{python_version}-{project_name}'
    
    def venv_exists(self, venv_path: Path) -> bool:
        """检查 venv 是否存在且有效"""
        python_bin = venv_path / 'bin' / 'python'
        return venv_path.exists() and python_bin.exists()
    
    def create_venv(self, project_name: str, python_version: str, force: bool = False) -> Path:
        """
        创建虚拟环境
        
        Args:
            project_name: 项目名称
            python_version: Python 版本（如 '3.10'）
            force: 强制重建（删除已存在的 venv）
        
        Returns:
            venv 路径
        """
        self._check_uv_installed()
        
        venv_path = self.get_venv_path(project_name, python_version)
        
        if self.venv_exists(venv_path):
            if force:
                print(f"🗑️  删除已存在的 venv: {venv_path.name}")
                shutil.rmtree(venv_path)
            else:
                print(f"✅ Venv 已存在: {venv_path}")
                return venv_path
        
        print(f"\n{'='*60}")
        print(f"🔨 创建虚拟环境")
        print(f"{'='*60}")
        print(f"📂 路径: {venv_path}")
        print(f"🐍 Python: {python_version}")
        
        cmd = ['uv', 'venv', str(venv_path), '--python', python_version]
        print(f"💻 命令: {' '.join(cmd)}\n")
        
        try:
            subprocess.run(cmd, check=True)
            print(f"\n✅ Venv 创建成功")
            return venv_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"创建 venv 失败: {e}")
    
    def ensure_venv(self, project_name: str, python_version: str) -> Path:
        """
        确保 venv 存在（不存在则创建）
        
        Args:
            project_name: 项目名称
            python_version: Python 版本
        
        Returns:
            venv 路径
        """
        venv_path = self.get_venv_path(project_name, python_version)
        
        if not self.venv_exists(venv_path):
            return self.create_venv(project_name, python_version)
        
        return venv_path
    
    def install_from_yaml(
        self,
        venv_path: Path,
        yaml_config_file: str,
        mirror: Optional[str] = None,
        force: bool = False
    ) -> Dict:
        """从 dependencies.yaml 安装依赖"""
        self._check_uv_installed()
        
        with open(yaml_config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        python_bin = venv_path / 'bin' / 'python'
        if not python_bin.exists():
            raise RuntimeError(f"Venv Python 不存在: {python_bin}")
        
        groups = config.get('groups', {})
        install_order = config.get('install_order', list(groups.keys()))
        
        print(f"\n{'='*60}")
        print(f"📦 安装依赖: {len(install_order)} 组")
        print(f"{'='*60}")
        
        results = {}
        for group_name in install_order:
            group = groups.get(group_name)
            if not group or not group.get('packages'):
                continue
            
            cmd = ['uv', 'pip', 'install', '--python', str(python_bin)]
            cmd.extend(group['packages'])
            
            if group.get('no_deps'):
                cmd.append('--no-deps')
            if group.get('index_url'):
                cmd.extend(['--index-url', group['index_url']])
            elif mirror:
                cmd.extend(['--index-url', mirror])
            if force:
                cmd.append('--reinstall')
            
            print(f"\n📦 {group_name} ({len(group['packages'])} 包)")
            result = subprocess.run(cmd, check=False)
            results[group_name] = (result.returncode == 0)
        
        success = sum(1 for s in results.values() if s)
        print(f"\n{'='*60}")
        print(f"✅ 完成: {success}/{len(results)} 组成功")
        print(f"{'='*60}")
        
        return {
            'total': sum(len(groups[g].get('packages', [])) for g in install_order if g in groups),
            'installed': success,
            'failed': len(results) - success,
            'groups': results
        }
    
    def list_packages(self, venv_path: Path) -> List[str]:
        """
        列出 venv 中已安装的包
        
        Args:
            venv_path: venv 路径
        
        Returns:
            包列表
        """
        self._check_uv_installed()
        
        python_bin = venv_path / 'bin' / 'python'
        if not python_bin.exists():
            return []
        
        cmd = ['uv', 'pip', 'list', '--python', str(python_bin)]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[2:]  # 跳过表头
            packages = [line.split()[0] for line in lines if line.strip()]
            return packages
        except subprocess.CalledProcessError:
            return []
    
    def get_venv_info(self, venv_path: Path) -> Dict:
        """
        获取 venv 信息
        
        Args:
            venv_path: venv 路径
        
        Returns:
            venv 信息字典
        """
        if not self.venv_exists(venv_path):
            return {'exists': False}
        
        python_bin = venv_path / 'bin' / 'python'
        
        # 获取 Python 版本
        try:
            result = subprocess.run(
                [str(python_bin), '--version'],
                check=True,
                capture_output=True,
                text=True
            )
            python_version = result.stdout.strip()
        except subprocess.CalledProcessError:
            python_version = 'Unknown'
        
        # 获取已安装包数量
        packages = self.list_packages(venv_path)
        
        return {
            'exists': True,
            'path': str(venv_path),
            'python_version': python_version,
            'packages_count': len(packages)
        }

