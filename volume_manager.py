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
        安装依赖（使用临时目录策略）
        
        Args:
            project_name: 项目名称
            dependencies: 依赖列表
            python_version: Python 版本 (如 '3.10')
            mirror: PyPI 镜像源
            force: 保留参数兼容性
            
        Returns:
            安装结果统计
        """
        # 按 Python 版本隔离依赖
        deps_path = self.volume_path / 'python-deps' / f'py{python_version}' / project_name
        deps_path_temp = self.volume_path / 'python-deps' / f'py{python_version}' / f'{project_name}_tmp'
        deps_path.parent.mkdir(parents=True, exist_ok=True)
        
        result = {
            'total': len(dependencies),
            'installed': 0,
            'skipped': 0,
            'removed': 0,
            'failed': []
        }
        
        # 清理可能存在的临时目录
        import shutil
        if deps_path_temp.exists():
            shutil.rmtree(deps_path_temp)
        
        # 创建临时目录
        deps_path_temp.mkdir(parents=True, exist_ok=True)
        
        # 直接安装所有依赖到临时目录
        to_install = dependencies
        
        # 安装依赖
        print(f"\n📦 待安装依赖: {len(to_install)}")
        for dep in to_install:
            print(f"  - {dep}")
        
        # 使用当前 Python 解释器的 pip，确保版本匹配
        import sys
        python_exe = sys.executable
        python_version_actual = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"\n🐍 使用 Python: {python_exe} ({python_version_actual})")
        print(f"📂 临时目录: {deps_path_temp}")
        print()
        
        cmd = [
            sys.executable, '-m', 'pip', 'install',
            '--no-cache-dir',
            '--progress-bar', 'off',  # 禁用进度条
            '--ignore-installed',  # 忽略系统已安装的包
            '--force-reinstall',  # 强制重新安装，确保版本正确
            f'--target={deps_path_temp}',  # 安装到临时目录
            '--upgrade',  # 确保获取正确版本
        ]
        
        if mirror:
            cmd.extend(['-i', mirror])
        
        cmd.extend(to_install)
        
        try:
            print(f"🚀 开始安装 {len(to_install)} 个依赖...")
            print(f"{'='*60}\n")
            import sys
            sys.stdout.flush()
            
            # 使用 Popen 实时输出，line-buffered 模式
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )
            
            # 实时读取并打印输出
            last_line = ""
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                print(line, end='', flush=True)
                last_line = line.strip()
            
            print(f"\n{'='*60}")
            print(f"📍 最后一行输出: {last_line[:100]}")
            print(f"📍 等待 pip 进程完全退出...")
            sys.stdout.flush()
            
            # 等待进程结束，并跟踪等待时间
            import time
            start_wait = time.time()
            
            # 使用超时轮询检测卡住
            timeout = 10  # 最多等待 10 秒
            check_interval = 0.5  # 每 0.5 秒检查一次
            elapsed = 0
            
            while elapsed < timeout:
                return_code = process.poll()  # 非阻塞检查
                if return_code is not None:
                    # 进程已结束
                    break
                time.sleep(check_interval)
                elapsed += check_interval
                if elapsed % 2 == 0:  # 每 2 秒打印一次
                    print(f"📍 等待中... ({elapsed:.1f}s)", flush=True)
            
            if return_code is None:
                # 超时了，进程还在运行
                print(f"⚠️  警告: pip 进程在输出结束后 {timeout}s 仍未退出")
                print(f"📍 强制获取退出码...")
                return_code = process.wait(timeout=5)  # 再等 5 秒
            
            wait_duration = time.time() - start_wait
            
            print(f"📍 pip 进程退出码: {return_code}")
            print(f"📍 总等待时间: {wait_duration:.2f} 秒")
            if wait_duration > 2:
                print(f"⚠️  pip 后处理耗时: {wait_duration:.2f}s (可能在生成 .pyc 或更新缓存)")
            sys.stdout.flush()
            
            if return_code != 0:
                raise Exception(f"pip 安装失败，返回码: {return_code}")
            
            result['installed'] = len(to_install)
            result['skipped'] = result['total'] - result['installed']
            
            # 替换原目录（跳过删除，直接重命名覆盖）
            print(f"\n🔄 替换依赖目录...")
            
            if deps_path.exists():
                import time
                
                # 处理旧备份（如果存在） - 前台执行
                deps_path_backup = deps_path.parent / f'{project_name}_old'
                if deps_path_backup.exists():
                    print(f"   - 删除旧备份: {deps_path_backup.name}")
                    sys.stdout.flush()
                    start = time.time()
                    
                    try:
                        shutil.rmtree(deps_path_backup)
                        print(f"     ✓ 完成 ({time.time() - start:.2f}s)")
                    except Exception as e:
                        print(f"     ⚠️  删除失败: {e}")
                    sys.stdout.flush()
                
                # 重命名当前目录为备份
                print(f"   - 重命名当前目录: {deps_path.name} -> {deps_path_backup.name}")
                sys.stdout.flush()
                deps_path.rename(deps_path_backup)
                print(f"     ✓ 完成")
                sys.stdout.flush()
                
                # 激活新目录
                print(f"   - 激活新目录: {deps_path_temp.name} -> {deps_path.name}")
                sys.stdout.flush()
                deps_path_temp.rename(deps_path)
                print(f"     ✓ 完成")
                sys.stdout.flush()
                
                # 前台删除旧备份
                print(f"   - 删除旧版本: {deps_path_backup.name} (可能需要一段时间...)")
                sys.stdout.flush()
                start = time.time()
                
                try:
                    shutil.rmtree(deps_path_backup)
                    elapsed = time.time() - start
                    print(f"     ✓ 完成 ({elapsed:.2f}s)")
                except Exception as e:
                    print(f"     ⚠️  删除失败: {e}")
                sys.stdout.flush()
            else:
                # 直接重命名
                print(f"   - 激活新目录: {deps_path_temp.name} -> {deps_path.name}")
                deps_path_temp.rename(deps_path)
            
            print(f"✅ 依赖安装完成！")
            
        except Exception as e:
            # 安装失败，清理临时目录
            print(f"\n❌ 安装失败，清理临时目录...")
            if deps_path_temp.exists():
                shutil.rmtree(deps_path_temp)
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
