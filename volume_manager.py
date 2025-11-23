#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunPod Volume 增量管理器
支持依赖和模型的增量安装/更新
"""
import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime


class VolumeManager:
    """Volume 增量管理器"""
    
    def __init__(self, volume_path: str):
        """
        初始化
        
        Args:
            volume_path: Volume 挂载路径
        """
        self.volume_path = Path(volume_path)
        self.metadata_dir = self.volume_path / '.metadata'
        self.metadata_dir.mkdir(exist_ok=True)
    
    def _get_project_metadata_file(self, project_name: str) -> Path:
        """获取项目元数据文件路径"""
        return self.metadata_dir / f'{project_name}.json'
    
    def _load_metadata(self, project_name: str) -> Dict:
        """加载项目元数据"""
        metadata_file = self._get_project_metadata_file(project_name)
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {
            'project': project_name,
            'dependencies': {},
            'models': {},
            'last_updated': None
        }
    
    def _save_metadata(self, project_name: str, metadata: Dict):
        """保存项目元数据"""
        metadata_file = self._get_project_metadata_file(project_name)
        metadata['last_updated'] = datetime.now().isoformat()
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _hash_dependencies(self, deps: List[str]) -> str:
        """计算依赖列表的哈希值"""
        deps_str = '\n'.join(sorted(deps))
        return hashlib.md5(deps_str.encode()).hexdigest()
    
    def check_dependencies_changed(
        self,
        project_name: str,
        new_deps: List[str]
    ) -> tuple[bool, Set[str], Set[str]]:
        """
        检查依赖是否变化
        
        Returns:
            (changed, added, removed)
            - changed: 是否有变化
            - added: 新增的依赖
            - removed: 移除的依赖
        """
        metadata = self._load_metadata(project_name)
        old_deps = set(metadata['dependencies'].keys())
        new_deps_set = set(new_deps)
        
        added = new_deps_set - old_deps
        removed = old_deps - new_deps_set
        changed = bool(added or removed)
        
        return changed, added, removed
    
    def install_dependencies(
        self,
        project_name: str,
        dependencies: List[str],
        python_version: str,
        mirror: Optional[str] = None,
        force: bool = False
    ) -> Dict:
        """
        增量安装依赖
        
        Args:
            project_name: 项目名称
            dependencies: 依赖列表
            python_version: Python 版本 (如 '3.10')
            mirror: PyPI 镜像源
            force: 强制重新安装所有依赖
            
        Returns:
            安装结果统计
        """
        # 按 Python 版本隔离依赖
        deps_path = self.volume_path / 'python-deps' / f'py{python_version}' / project_name
        deps_path.mkdir(parents=True, exist_ok=True)
        
        # 检查依赖变化
        changed, added, removed = self.check_dependencies_changed(
            project_name, dependencies
        )
        
        result = {
            'total': len(dependencies),
            'installed': 0,
            'skipped': 0,
            'removed': 0,
            'failed': []
        }
        
        # 如果强制安装或有移除的依赖，清空目录重新安装
        if force or removed:
            if removed and not force:
                print(f"\n⚠️  检测到移除的依赖: {', '.join(removed)}")
                response = input("是否清空依赖目录重新安装？(y/N): ")
                if response.lower() != 'y':
                    force = False
                else:
                    force = True
            
            if force:
                print(f"\n🗑️  清空依赖目录: {deps_path}")
                import shutil
                if deps_path.exists():
                    shutil.rmtree(deps_path)
                deps_path.mkdir(parents=True, exist_ok=True)
                to_install = dependencies
                result['removed'] = len(removed)
            else:
                to_install = list(added)
        else:
            to_install = list(added) if changed else []
        
        # 如果没有需要安装的
        if not to_install:
            print(f"\n✅ 依赖已是最新，无需安装")
            result['skipped'] = len(dependencies)
            return result
        
        # 安装依赖
        print(f"\n📦 待安装依赖: {len(to_install)}")
        for dep in to_install:
            print(f"  - {dep}")
        
        # 使用当前 Python 解释器的 pip，确保版本匹配
        import sys
        python_exe = sys.executable
        python_version_actual = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"\n🐍 使用 Python: {python_exe} ({python_version_actual})")
        print(f"📂 安装目录: {deps_path}")
        print()
        
        cmd = [
            sys.executable, '-m', 'pip', 'install',
            '--no-cache-dir',
            f'--target={deps_path}',
        ]
        
        # 增量模式优化
        if force:
            cmd.append('--upgrade')  # 强制模式：升级所有包
        else:
            # 增量模式：使用 --exists-action i 忽略已存在的包
            cmd.extend(['--exists-action', 'i'])  # ignore 已存在的包，不报警告
        
        if mirror:
            cmd.extend(['-i', mirror])
        
        cmd.extend(to_install)
        
        try:
            mode = "强制模式" if force else "增量模式"
            print(f"🚀 开始安装 {len(to_install)} 个依赖 ({mode})")
            if not force:
                print(f"📝 仅安装新增的包: {', '.join(to_install[:5])}{'...' if len(to_install) > 5 else ''}")
            
            # 使用 subprocess.run 而不是 os.system，因为命令可能很长
            result_proc = subprocess.run(cmd, capture_output=False, text=True)
            
            if result_proc.returncode != 0:
                raise Exception(f"pip 安装失败，返回码: {result_proc.returncode}")
            
            result['installed'] = len(to_install)
            result['skipped'] = result['total'] - result['installed']
            
            print(f"✅ 依赖安装完成！")
            
        except Exception as e:
            result['failed'] = to_install
            raise e
        
        return result
    
    def check_model_exists(self, model_id: str, source: str) -> bool:
        """检查模型是否已存在"""
        models_path = self.volume_path / 'models'
        
        if source == 'modelscope':
            # ModelScope 模型路径格式
            model_dir = models_path / 'hub' / model_id
            return model_dir.exists()
        elif source == 'huggingface':
            # HuggingFace 模型路径格式
            model_parts = model_id.split('/')
            if len(model_parts) == 2:
                model_dir = models_path / 'models--' / f'{model_parts[0]}--{model_parts[1]}'
            else:
                model_dir = models_path / model_id
            return model_dir.exists()
        
        return False
    
    def register_model(
        self,
        project_name: str,
        model_id: str,
        source: str,
        size: Optional[int] = None
    ):
        """注册已下载的模型"""
        metadata = self._load_metadata(project_name)
        
        if 'models' not in metadata:
            metadata['models'] = {}
        
        metadata['models'][model_id] = {
            'source': source,
            'installed_at': datetime.now().isoformat(),
            'size': size
        }
        
        self._save_metadata(project_name, metadata)
    
    def check_models_changed(
        self,
        project_name: str,
        new_models: Dict[str, List[str]]
    ) -> tuple[bool, List[tuple], List[str]]:
        """
        检查模型列表是否变化
        
        Returns:
            (changed, added, removed)
            - changed: 是否有变化
            - added: 新增的模型 [(model_id, source), ...]
            - removed: 移除的模型 [model_id, ...]
        """
        metadata = self._load_metadata(project_name)
        old_models = set(metadata.get('models', {}).keys())
        
        # 展开新模型列表
        new_models_flat = []
        for source, model_list in new_models.items():
            for model_id in model_list:
                new_models_flat.append((model_id, source))
        
        new_model_ids = set(m[0] for m in new_models_flat)
        
        added = [(mid, src) for mid, src in new_models_flat if mid not in old_models]
        removed = list(old_models - new_model_ids)
        changed = bool(added or removed)
        
        return changed, added, removed
    
    def get_project_stats(self, project_name: str) -> Dict:
        """获取项目统计信息"""
        metadata = self._load_metadata(project_name)
        deps_path = self.volume_path / 'python-deps' / project_name
        
        stats = {
            'project': project_name,
            'dependencies_count': len(metadata.get('dependencies', {})),
            'models_count': len(metadata.get('models', {})),
            'last_updated': metadata.get('last_updated'),
        }
        
        # 跳过目录大小计算（太慢）
        # 如果需要查看大小，手动运行 du -sh 命令
        
        return stats
    
    def list_projects(self) -> List[Dict]:
        """列出所有项目"""
        projects = []
        for metadata_file in self.metadata_dir.glob('*.json'):
            project_name = metadata_file.stem
            projects.append(self.get_project_stats(project_name))
        return projects
