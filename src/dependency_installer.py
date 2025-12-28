#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用依赖安装器
根据 YAML 配置文件从不同索引源安装依赖
"""
import os
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class DependencyInstaller:
    """依赖安装器 - 支持多索引源安装"""
    
    def __init__(self, config_file: str):
        """
        初始化
        
        Args:
            config_file: 依赖配置文件路径 (dependencies.yaml)
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"依赖配置文件不存在: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_all_packages(self) -> List[str]:
        """获取所有依赖包列表"""
        all_packages = []
        groups = self.config.get('groups', {})
        for group_name, group_config in groups.items():
            packages = group_config.get('packages', [])
            all_packages.extend(packages)
        return all_packages
    
    def install(
        self,
        target_dir: Optional[str] = None,
        mirror: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, bool]:
        """
        安装所有依赖
        
        Args:
            target_dir: 安装目标目录 (使用 pip -t 参数)
            mirror: PyPI 镜像源 (仅用于 index_url 为 null 的组)
            dry_run: 是否只打印命令不执行
        
        Returns:
            安装结果字典 {group_name: success}
        """
        groups = self.config.get('groups', {})
        install_order = self.config.get('install_order', list(groups.keys()))
        results = {}
        
        print(f"\n{'='*60}")
        print(f"📦 开始安装依赖")
        print(f"{'='*60}")
        
        total_groups = len([g for g in install_order if g in groups])
        current_group_idx = 0
        
        for group_name in install_order:
            if group_name not in groups:
                print(f"\n⚠️  警告: 安装顺序中的组 '{group_name}' 不存在，跳过")
                continue
            
            current_group_idx += 1
            group_config = groups[group_name]
            
            # 输出结构化进度日志
            print(f"[PROGRESS] group={group_name} current={current_group_idx} total={total_groups}")
            
            success = self._install_group(
                group_name,
                group_config,
                target_dir,
                mirror,
                dry_run,
                current_group_idx,
                total_groups
            )
            results[group_name] = success
        
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
        
        return results
    
    def _install_group(
        self,
        group_name: str,
        group_config: Dict,
        target_dir: Optional[str],
        mirror: Optional[str],
        dry_run: bool,
        current_idx: int = 1,
        total_groups: int = 1
    ) -> bool:
        """
        安装一个依赖组
        
        Args:
            group_name: 组名称
            group_config: 组配置
            target_dir: 安装目标目录
            mirror: PyPI 镜像源
            dry_run: 是否只打印命令
            current_idx: 当前组索引
            total_groups: 总组数
        
        Returns:
            是否成功
        """
        packages = group_config.get('packages', [])
        index_url = group_config.get('index_url')
        description = group_config.get('description', '')
        no_deps = group_config.get('no_deps', False)  # 是否跳过依赖检查
        
        if not packages:
            print(f"\n⏭️  跳过空组: {group_name}")
            return True
        
        print(f"\n{'─'*60}")
        print(f"📦 安装组: {group_name}")
        if description:
            print(f"   {description}")
        print(f"   包数量: {len(packages)}")
        if index_url:
            print(f"   索引 URL: {index_url}")
        if no_deps:
            print(f"   ⚠️  跳过依赖检查 (--no-deps)")
        print(f"{'─'*60}")
        
        # 构建 pip install 命令
        cmd = ['pip', 'install']
        
        # 添加包列表
        cmd.extend(packages)
        
        # 添加目标目录
        if target_dir:
            cmd.extend(['-t', target_dir])
        
        # 添加 --no-deps 选项
        if no_deps:
            cmd.append('--no-deps')
        
        # 添加索引 URL
        if index_url:
            cmd.extend(['--index-url', index_url])
        elif mirror:
            # 只有在没有指定 index_url 时才使用 mirror
            cmd.extend(['-i', mirror])
        
        # 打印命令
        cmd_str = ' '.join(cmd)
        print(f"\n💻 命令: {cmd_str}")
        print()  # 空行，使输出更清晰
        
        if dry_run:
            print("   (Dry run - 不执行)")
            return True
        
        # 执行安装（实时显示输出）
        import time
        start_time = time.time()
        
        try:
            # 不捕获输出，让日志实时显示到终端
            result = subprocess.run(
                cmd,
                check=False
            )
            
            elapsed_time = int(time.time() - start_time)
            print()  # 安装完成后空一行
            
            if result.returncode == 0:
                print(f"[SUCCESS] group={group_name} time={elapsed_time}s packages={len(packages)}")
                print(f"✅ 组 '{group_name}' 安装成功")
                return True
            else:
                print(f"[FAILED] group={group_name} exitcode={result.returncode}")
                print(f"❌ 组 '{group_name}' 安装失败 (退出码: {result.returncode})")
                return False
        
        except Exception as e:
            print(f"[FAILED] group={group_name} error={str(e)}")
            print(f"❌ 组 '{group_name}' 安装异常: {e}")
            return False
    
    def generate_requirements_txt(self, output_file: str):
        """
        生成传统的 requirements.txt 文件（包含注释说明）
        
        Args:
            output_file: 输出文件路径
        """
        groups = self.config.get('groups', {})
        install_order = self.config.get('install_order', list(groups.keys()))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入头部注释
            f.write("# 依赖列表\n")
            f.write("# 此文件由 dependencies.yaml 自动生成\n")
            f.write("# 建议使用 dependency_installer.py 安装以支持多索引源\n\n")
            
            # 写入元数据
            metadata = self.config.get('metadata', {})
            if metadata:
                f.write(f"# Project: {metadata.get('project', 'N/A')}\n")
                f.write(f"# Python: {metadata.get('python_version', 'N/A')}\n\n")
            
            # 按组写入依赖
            for group_name in install_order:
                if group_name not in groups:
                    continue
                
                group_config = groups[group_name]
                packages = group_config.get('packages', [])
                index_url = group_config.get('index_url')
                description = group_config.get('description', '')
                
                # 写入组信息
                f.write(f"# === {group_name} ===\n")
                if description:
                    f.write(f"# {description}\n")
                if index_url:
                    f.write(f"# Install with: pip install [packages] --index-url {index_url}\n")
                f.write("\n")
                
                # 写入包列表
                for package in packages:
                    f.write(f"{package}\n")
                f.write("\n")
        
        print(f"✅ 已生成 requirements.txt: {output_file}")


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='通用依赖安装器')
    parser.add_argument('config', help='依赖配置文件 (dependencies.yaml)')
    parser.add_argument('-t', '--target', help='安装目标目录')
    parser.add_argument('-m', '--mirror', help='PyPI 镜像源')
    parser.add_argument('--dry-run', action='store_true', help='只打印命令不执行')
    parser.add_argument('--generate-requirements', help='生成 requirements.txt 文件')
    
    args = parser.parse_args()
    
    installer = DependencyInstaller(args.config)
    
    if args.generate_requirements:
        installer.generate_requirements_txt(args.generate_requirements)
    else:
        installer.install(
            target_dir=args.target,
            mirror=args.mirror,
            dry_run=args.dry_run
        )


if __name__ == '__main__':
    main()
