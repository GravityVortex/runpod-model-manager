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
from dependency_installer import DependencyInstaller


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
    
    def _get_project_metadata_file(self, project_name: str, python_version: Optional[str] = None) -> Path:
        """
        获取项目元数据文件路径
        
        Args:
            project_name: 项目名称
            python_version: Python 版本（如 '3.10'），不指定则返回旧格式兼容
        """
        if python_version:
            return self.metadata_dir / f'{project_name}-py{python_version}.json'
        return self.metadata_dir / f'{project_name}.json'
    
    def _load_metadata(self, project_name: str, python_version: Optional[str] = None) -> Dict:
        """
        加载项目元数据（兼容旧格式）
        
        Args:
            project_name: 项目名称
            python_version: Python 版本（如 '3.10'）
        """
        # 先尝试读取新格式（带 Python 版本）
        metadata_file = self._get_project_metadata_file(project_name, python_version)
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        
        # 如果新格式不存在，尝试读取旧格式并迁移
        if python_version:
            old_metadata_file = self._get_project_metadata_file(project_name, None)
            if old_metadata_file.exists():
                print(f"   📋 检测到旧格式元数据，正在迁移...")
                with open(old_metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # 添加 Python 版本信息
                metadata['python_version'] = python_version
                
                # 保存为新格式
                self._save_metadata(project_name, metadata, python_version)
                print(f"   ✅ 元数据已迁移到新格式: {metadata_file.name}")
                
                return metadata
        
        # 都不存在，返回空元数据
        return {
            'project': project_name,
            'python_version': python_version,
            'dependencies': {},
            'models': {},
            'last_updated': None
        }
    
    def _save_metadata(self, project_name: str, metadata: Dict, python_version: Optional[str] = None):
        """
        保存项目元数据
        
        Args:
            project_name: 项目名称
            metadata: 元数据字典
            python_version: Python 版本（如 '3.10'）
        """
        metadata_file = self._get_project_metadata_file(project_name, python_version)
        metadata['last_updated'] = datetime.now().isoformat()
        if python_version:
            metadata['python_version'] = python_version
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _fix_modelscope_release_date(self, deps_dir: Path):
        """
        修复 ModelScope 版本日期（标准方法）
        
        原理：
        - 将 __release_datetime__ 改为过去的日期（如 2024-01-01）
        - ModelScope 判断为正式版本，跳过 AST 扫描
        - 删除旧的 AST 索引缓存，避免触发更新扫描
        - 避免 Python 3.10/3.11 环境下的 type_params AttributeError
        
        Args:
            deps_dir: 依赖安装目录
        """
        version_file = deps_dir / 'modelscope' / 'version.py'
        
        if not version_file.exists():
            return
        
        try:
            import re
            import shutil
            content = version_file.read_text(encoding='utf-8')
            
            # 检查是否已修改
            if '# PATCHED' in content:
                print(f"   ℹ️  ModelScope 版本已修复")
                # 即使已修复，也检查并删除 AST 缓存
                ast_cache = self.volume_path / 'models' / 'ast_indexer'
                if ast_cache.exists():
                    print(f"   🗑️  删除 AST 索引缓存...")
                    try:
                        if ast_cache.is_dir():
                            shutil.rmtree(ast_cache)
                        else:
                            ast_cache.unlink()
                        print(f"   ✅ AST 缓存已删除")
                    except Exception as e:
                        print(f"   ⚠️  删除缓存失败: {e}")
                return
            
            # 修改发布日期为过去的日期
            pattern = r"__release_datetime__\s*=\s*['\"].*?['\"]"
            replacement = "__release_datetime__ = '2024-01-01 00:00:00'  # PATCHED: Set as release version"
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                version_file.write_text(new_content, encoding='utf-8')
                print(f"   ✅ ModelScope 已标记为正式版本（跳过 AST 扫描）")
                print(f"   ℹ️  原理：发布日期在过去 → 正式版本 → 跳过 AST 扫描")
                
                # 🔥 关键：删除 AST 索引缓存
                ast_cache = self.volume_path / 'models' / 'ast_indexer'
                if ast_cache.exists():
                    print(f"   🗑️  删除旧的 AST 索引缓存...")
                    try:
                        if ast_cache.is_dir():
                            shutil.rmtree(ast_cache)
                        else:
                            ast_cache.unlink()
                        print(f"   ✅ AST 缓存已删除")
                    except Exception as e:
                        print(f"   ⚠️  删除缓存失败: {e}")
            else:
                print(f"   ⚠️  未找到 __release_datetime__ 或格式变化")
        
        except Exception as e:
            print(f"   ⚠️  修复 ModelScope 版本时出错: {e}")
    
    def _hash_dependencies(self, deps: List[str]) -> str:
        """计算依赖列表的哈希值"""
        deps_str = '\n'.join(sorted(deps))
        return hashlib.md5(deps_str.encode()).hexdigest()
    
    def check_dependencies_changed(
        self,
        project_name: str,
        new_deps: List[str],
        python_version: Optional[str] = None
    ) -> tuple[bool, Set[str], Set[str], Set[str]]:
        """
        检查依赖是否变化
        
        Args:
            project_name: 项目名称
            new_deps: 新的依赖列表
            python_version: Python 版本（如 '3.10'）
        
        Returns:
            (changed, added, removed, updated)
            - changed: 是否有变化
            - added: 新增的依赖（包名级别）
            - removed: 移除的依赖（包名级别）
            - updated: 版本更新的依赖
        """
        def extract_pkg_name(dep: str) -> str:
            """提取包名（去除版本号）"""
            for sep in ['==', '>=', '<=', '>', '<', '!=', '~=']:
                if sep in dep:
                    return dep.split(sep)[0].strip()
            return dep.strip()
        
        metadata = self._load_metadata(project_name, python_version)
        
        # 完整依赖字符串集合
        old_deps_full = set(metadata['dependencies'].keys())
        new_deps_full = set(new_deps)
        
        # 包名集合（不含版本）
        old_pkg_names = {extract_pkg_name(d) for d in old_deps_full}
        new_pkg_names = {extract_pkg_name(d) for d in new_deps_full}
        
        # 纯新增的包（包名不在旧列表中）
        truly_added = new_pkg_names - old_pkg_names
        added = {d for d in new_deps_full if extract_pkg_name(d) in truly_added}
        
        # 纯删除的包（包名不在新列表中）
        truly_removed = old_pkg_names - new_pkg_names
        removed = {d for d in old_deps_full if extract_pkg_name(d) in truly_removed}
        
        # 版本更新的包（包名相同，但完整字符串不同）
        common_pkg_names = old_pkg_names & new_pkg_names
        updated = set()
        for pkg_name in common_pkg_names:
            old_full = next((d for d in old_deps_full if extract_pkg_name(d) == pkg_name), None)
            new_full = next((d for d in new_deps_full if extract_pkg_name(d) == pkg_name), None)
            if old_full != new_full:
                updated.add(new_full)
        
        changed = bool(added or removed or updated)
        
        return changed, added, removed, updated
    
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
            
            # 安装完成后自动修复 ModelScope
            if (deps_path / 'modelscope').exists():
                print(f"\n🛠️  后处理: 修复 ModelScope 版本检测...")
                self._fix_modelscope_release_date(deps_path)
            
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
    
    def install_dependencies_from_config(
        self,
        project_name: str,
        config_file: str,
        python_version: str,
        mirror: Optional[str] = None,
        force: bool = False
    ) -> Dict:
        """
        使用依赖配置文件 (dependencies.yaml) 安装依赖
        使用临时目录策略：先安装到临时目录，成功后再替换正式目录
        
        Args:
            project_name: 项目名称
            config_file: 依赖配置文件路径 (dependencies.yaml)
            python_version: Python 版本 (如 '3.10')
            mirror: PyPI 镜像源（仅用于未指定 index_url 的依赖组）
            force: 强制重新安装（跳过变更检测）
        
        Returns:
            安装结果统计
        """
        # 按 Python 版本隔离依赖
        deps_path = self.volume_path / 'python-deps' / f'py{python_version}' / project_name
        deps_path_temp = self.volume_path / 'python-deps' / f'py{python_version}' / f'{project_name}_tmp'
        deps_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"📦 使用配置文件安装依赖: {config_file}")
        print(f"{'='*60}")
        
        # 创建依赖安装器
        installer = DependencyInstaller(config_file)
        all_packages = installer.get_all_packages()
        
        # 检查依赖是否变化
        if force:
            print(f"\n🔄 强制重新安装模式")
            print(f"   跳过依赖变更检测")
            changed = True  # 强制视为有变化
            added = set()
            removed = set()
            updated = set()
        else:
            print(f"\n🔍 检查依赖变更...")
            print(f"   Python 版本: {python_version}")
            print(f"   配置包数量: {len(all_packages)}")
            
            changed, added, removed, updated = self.check_dependencies_changed(
                project_name, 
                all_packages,
                python_version
            )
        
        # 如果依赖未变化且目录已存在，跳过安装
        if not force and not changed and deps_path.exists():
            print(f"\n✅ 依赖未变化，跳过重新安装")
            print(f"   已安装包数: {len(all_packages)}")
            
            # 但仍然执行 ModelScope 修复检查
            if (deps_path / 'modelscope').exists():
                print(f"\n🛠️  后处理: 检查 ModelScope 版本...")
                self._fix_modelscope_release_date(deps_path)
            
            return {
                'total': len(all_packages),
                'installed': 0,
                'skipped': len(all_packages),
                'failed': 0,
                'unchanged': True,
                'groups': {}
            }
        
        # 有变化或首次安装，执行安装流程
        is_first_install = not deps_path.exists()
        
        if changed:
            print(f"\n📦 检测到依赖变化:")
            if added:
                print(f"   ✚ 新增: {len(added)} 个包")
                for pkg in list(added)[:5]:
                    print(f"      - {pkg}")
                if len(added) > 5:
                    print(f"      ... 还有 {len(added) - 5} 个")
            if removed:
                print(f"   ✖ 移除: {len(removed)} 个包")
                for pkg in list(removed)[:5]:
                    print(f"      - {pkg}")
                if len(removed) > 5:
                    print(f"      ... 还有 {len(removed) - 5} 个")
            if updated:
                print(f"   🔄 版本更新: {len(updated)} 个包")
                for pkg in list(updated)[:5]:
                    print(f"      - {pkg}")
                if len(updated) > 5:
                    print(f"      ... 还有 {len(updated) - 5} 个")
        else:
            print(f"\n📦 首次安装，开始安装所有依赖...")
        
        # 清理可能存在的临时目录
        import shutil
        if deps_path_temp.exists():
            print(f"\n🗑️  清理旧的临时目录...")
            shutil.rmtree(deps_path_temp)
        
        # 创建临时目录
        deps_path_temp.mkdir(parents=True, exist_ok=True)
        print(f"📂 临时目录: {deps_path_temp}")
        
        # 🔥 增量安装策略
        if removed and not is_first_install:
            # 有删除的包 → 全部重新安装（避免依赖关系问题）
            print(f"\n⚠️  检测到包删除，将全部重新安装以确保依赖完整性")
            results = installer.install(
                target_dir=str(deps_path_temp),
                mirror=mirror,
                dry_run=False
            )
        elif (added or updated) and not is_first_install:
            # 只有新增/更新，没有删除 → 增量安装（直接在正式目录）
            total_changes = len(added) + len(updated)
            print(f"\n🚀 增量安装模式：直接更新正式目录")
            print(f"   变更: {len(added)} 新增, {len(updated)} 更新")
            print(f"   跳过复制步骤，直接安装到正式目录（更快）")
            
            # 合并新增和更新的包
            to_install = list(added) + list(updated)
            groups = installer.config.get('groups', {})
            install_order = installer.config.get('install_order', list(groups.keys()))
            
            # 按组安装/更新包（直接在正式目录）
            install_success = True
            for group_name in install_order:
                if group_name not in groups:
                    continue
                
                group_config = groups[group_name]
                group_packages = group_config.get('packages', [])
                index_url = group_config.get('index_url')
                no_deps = group_config.get('no_deps', False)
                
                # 找出这个组中需要安装/更新的包
                group_to_install = [pkg for pkg in to_install if pkg in group_packages]
                
                if not group_to_install:
                    continue
                
                print(f"\n   📦 组: {group_name} ({len(group_to_install)} 个包)")
                if no_deps:
                    print(f"      ⚠️  跳过依赖检查 (--no-deps)")
                
                import sys
                cmd = [
                    sys.executable, '-m', 'pip', 'install',
                    '--no-cache-dir',
                    '--target', str(deps_path),  # 直接安装到正式目录
                    '--upgrade',  # 使用 --upgrade 确保版本更新
                ]
                
                # 添加 --no-deps 选项
                if no_deps:
                    cmd.append('--no-deps')
                
                # 添加索引源
                if index_url:
                    cmd.extend(['--index-url', index_url])
                elif mirror:
                    cmd.extend(['-i', mirror])
                
                cmd.extend(group_to_install)
                
                try:
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    print(f"      ✅ 安装成功: {', '.join(group_to_install)}")
                except subprocess.CalledProcessError as e:
                    print(f"      ❌ 安装失败: {e}")
                    print(f"      {e.stderr}")
                    install_success = False
                    break
            
            results = {'incremental': install_success}
            
            # 增量安装不需要替换目录，直接跳到后处理
            if results.get('incremental'):
                # 安装完成后自动修复 ModelScope
                if (deps_path / 'modelscope').exists():
                    print(f"\n🛠️  后处理: 修复 ModelScope 版本检测...")
                    self._fix_modelscope_release_date(deps_path)
                
                # 更新元数据
                all_packages = installer.get_all_packages()
                metadata = self._load_metadata(project_name, python_version)
                for pkg in all_packages:
                    metadata['dependencies'][pkg] = {
                        'installed': True,
                        'timestamp': datetime.now().isoformat()
                    }
                self._save_metadata(project_name, metadata, python_version)
                
                return {
                    'total': len(all_packages),
                    'installed': len(added) + len(updated),
                    'failed': 0,
                    'incremental': True,
                    'groups': {}
                }
            else:
                # 增量安装失败
                print(f"\n{'='*60}")
                print(f"❌ 增量安装失败")
                print(f"{'='*60}")
                
                return {
                    'total': len(all_packages),
                    'installed': 0,
                    'failed': len(added) + len(updated),
                    'groups': results
                }
        else:
            # 首次安装 → 完整安装
            results = installer.install(
                target_dir=str(deps_path_temp),
                mirror=mirror,
                dry_run=False
            )
        
        # 检查完整安装（删除包或首次安装）是否有失败的组
        if 'incremental' not in results:
            # 完整安装 - 检查各组结果
            failed_groups = [name for name, success in results.items() if not success]
            if failed_groups:
                print(f"\n{'='*60}")
                print(f"❌ 安装失败")
                print(f"{'='*60}")
                print(f"失败的组: {', '.join(failed_groups)}")
                print(f"\n临时目录未被删除，可用于调试: {deps_path_temp}")
                
                return {
                    'total': len(all_packages),
                    'installed': 0,
                    'failed': len(failed_groups),
                    'groups': results
                }
        
        # 所有组都安装成功，替换正式目录
        print(f"\n🔄 替换依赖目录...")
        
        if deps_path.exists():
            # 备份旧目录
            deps_path_backup = deps_path.parent / f'{project_name}_old'
            if deps_path_backup.exists():
                print(f"🗑️  删除旧备份...")
                shutil.rmtree(deps_path_backup)
            
            print(f"📦 备份当前目录 -> {deps_path_backup.name}")
            deps_path.rename(deps_path_backup)
        
        # 将临时目录重命名为正式目录
        print(f"✅ 应用新安装 -> {deps_path.name}")
        deps_path_temp.rename(deps_path)
        
        # 清理备份（可选，如果需要保留备份可以注释掉）
        if deps_path.exists() and deps_path_backup.exists():
            print(f"🗑️  清理备份目录...")
            shutil.rmtree(deps_path_backup)
        
        # 安装完成后自动修复 ModelScope
        if (deps_path / 'modelscope').exists():
            print(f"\n🛠️  后处理: 修复 ModelScope 版本检测...")
            self._fix_modelscope_release_date(deps_path)
        
        # 更新元数据
        all_packages = installer.get_all_packages()
        metadata = self._load_metadata(project_name, python_version)
        for pkg in all_packages:
            metadata['dependencies'][pkg] = {
                'installed': True,
                'timestamp': datetime.now().isoformat()
            }
        self._save_metadata(project_name, metadata, python_version)
        
        # 返回完整安装结果统计
        return {
            'total': len(all_packages),
            'installed': sum(1 for s in results.values() if s),
            'failed': sum(1 for s in results.values() if not s),
            'groups': results
        }
