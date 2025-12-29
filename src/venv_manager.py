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
        """
        从 dependencies.yaml 安装依赖
        
        Args:
            venv_path: venv 路径
            yaml_config_file: 依赖配置文件路径
            mirror: PyPI 镜像源（仅用于 index_url 为 null 的组）
            force: 强制重装
        
        Returns:
            安装结果统计
        """
        self._check_uv_installed()
        
        if not Path(yaml_config_file).exists():
            raise FileNotFoundError(f"配置文件不存在: {yaml_config_file}")
        
        # 加载配置
        with open(yaml_config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        groups = config.get('groups', {})
        install_order = config.get('install_order', list(groups.keys()))
        
        print(f"\n{'='*60}")
        print(f"📦 使用 uv 安装依赖")
        print(f"{'='*60}")
        print(f"📝 配置文件: {yaml_config_file}")
        print(f"🐍 Venv: {venv_path.name}")
        print(f"📊 依赖组数: {len(install_order)}")
        
        python_bin = venv_path / 'bin' / 'python'
        if not python_bin.exists():
            raise RuntimeError(f"Venv Python 不存在: {python_bin}")
        
        results = {}
        total_packages = 0
        
        for idx, group_name in enumerate(install_order, 1):
            if group_name not in groups:
                print(f"\n⚠️  警告: 组 '{group_name}' 不存在，跳过")
                continue
            
            group_config = groups[group_name]
            packages = group_config.get('packages', [])
            index_url = group_config.get('index_url')
            description = group_config.get('description', '')
            no_deps = group_config.get('no_deps', False)
            
            if not packages:
                print(f"\n⏭️  跳过空组: {group_name}")
                results[group_name] = True
                continue
            
            total_packages += len(packages)
            
            print(f"\n{'─'*60}")
            print(f"📦 组 [{idx}/{len(install_order)}]: {group_name}")
            if description:
                print(f"   {description}")
            print(f"   包数量: {len(packages)}")
            if index_url:
                print(f"   索引 URL: {index_url}")
            if no_deps:
                print(f"   ⚠️  跳过依赖检查 (--no-deps)")
            print(f"{'─'*60}")
            
            # 构建 uv pip install 命令
            cmd = ['uv', 'pip', 'install', '--python', str(python_bin)]
            
            # 添加包列表
            cmd.extend(packages)
            
            # 添加 --no-deps 选项
            if no_deps:
                cmd.append('--no-deps')
            
            # 添加索引 URL
            if index_url:
                cmd.extend(['--index-url', index_url])
            elif mirror:
                cmd.extend(['--index-url', mirror])
            
            # 强制重装
            if force:
                cmd.append('--reinstall')
            
            # 打印命令
            cmd_str = ' '.join(cmd)
            print(f"\n💻 命令: {cmd_str}")
            print()
            
            # 执行安装
            import time
            start_time = time.time()
            
            try:
                result = subprocess.run(cmd, check=False)
                elapsed_time = int(time.time() - start_time)
                
                if result.returncode == 0:
                    print(f"\n✅ 组 '{group_name}' 安装成功 ({elapsed_time}s)")
                    results[group_name] = True
                else:
                    print(f"\n❌ 组 '{group_name}' 安装失败 (退出码: {result.returncode})")
                    results[group_name] = False
            
            except Exception as e:
                print(f"\n❌ 组 '{group_name}' 安装异常: {e}")
                results[group_name] = False
        
        # 统计
        print(f"\n{'='*60}")
        print(f"📊 安装统计")
        print(f"{'='*60}")
        success_count = sum(1 for s in results.values() if s)
        total_count = len(results)
        print(f"✅ 成功: {success_count}/{total_count}")
        
        if success_count < total_count:
            print(f"❌ 失败: {total_count - success_count}")
            for group_name, success in results.items():
                if not success:
                    print(f"  - {group_name}")
        
        return {
            'total': total_packages,
            'installed': sum(1 for s in results.values() if s),
            'failed': sum(1 for s in results.values() if not s),
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

