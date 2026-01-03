#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型同步器 - 通过 rsync/scp 传输本地模型到远程 Volume
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


class ModelSyncer:
    """模型同步器"""
    
    def __init__(self, remote_host: str, remote_volume: Optional[str] = None, ssh_password: Optional[str] = None):
        """
        初始化
        
        Args:
            remote_host: SSH 连接字符串 (user@host 或 user@host:port)
            remote_volume: 远程 volume 路径，None 则自动检测
            ssh_password: SSH 密码（可选，使用 sshpass）
        """
        # 解析主机和端口
        if ':' in remote_host and '@' in remote_host:
            self.remote_host, port = remote_host.rsplit(':', 1)
            self.ssh_port = port
        else:
            self.remote_host = remote_host
            self.ssh_port = '22'
        
        self.ssh_password = ssh_password
        self.remote_volume = remote_volume or self._detect_remote_volume()
        self.use_rsync = self._check_rsync_available()
    
    def _check_rsync_available(self) -> bool:
        """检查 rsync 是否可用（本地和远程都需要）"""
        # 检查本地
        try:
            subprocess.run(['rsync', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        
        # 检查远程
        check_cmd = self._build_ssh_cmd(['ssh', '-p', self.ssh_port, '-o', 'StrictHostKeyChecking=no',
                                         self.remote_host, 'which rsync'])
        try:
            result = subprocess.run(check_cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _build_ssh_cmd(self, base_cmd: list) -> list:
        """构建 SSH 命令（支持密码认证）"""
        if self.ssh_password:
            return ['sshpass', '-p', self.ssh_password] + base_cmd
        return base_cmd
    
    def _detect_remote_volume(self) -> str:
        """检测远程 volume 路径"""
        for path in ['/workspace', '/runpod-volume']:
            cmd = self._build_ssh_cmd(['ssh', '-p', self.ssh_port, '-o', 'StrictHostKeyChecking=no', 
                                       self.remote_host, f'test -d {path} && echo ok'])
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.stdout.strip() == 'ok':
                    return path
            except:
                continue
        return '/workspace'
    
    def _build_target_path(self, model_id: str, source: str) -> str:
        """
        构建目标路径
        
        Args:
            model_id: 模型 ID (如 'org/model')
            source: modelscope 或 huggingface
        """
        models_dir = f"{self.remote_volume}/models"
        
        # 直接使用 model_id，不添加 hub/ 等前缀
        return f"{models_dir}/{model_id}"
    
    def sync_directory(
        self,
        local_path: str,
        model_id: str,
        source: str,
        force: bool = False
    ) -> bool:
        """
        同步目录到远程
        
        Args:
            local_path: 本地模型目录
            model_id: 模型 ID
            source: modelscope/huggingface
            force: 强制覆盖
        """
        local_dir = Path(local_path).expanduser().resolve()
        
        if not local_dir.exists() or not local_dir.is_dir():
            print(f"❌ 本地目录不存在: {local_dir}")
            return False
        
        target_path = self._build_target_path(model_id, source)
        
        print(f"\n📂 本地路径: {local_dir}")
        print(f"📍 目标路径: {self.remote_host}:{target_path}")
        print(f"🔧 传输方式: {'rsync' if self.use_rsync else 'scp'}")
        
        # 检查远程是否已存在
        if not force:
            check_cmd = self._build_ssh_cmd(['ssh', '-p', self.ssh_port, '-o', 'StrictHostKeyChecking=no',
                                             self.remote_host, f'test -d {target_path} && echo exists'])
            try:
                result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
                if result.stdout.strip() == 'exists':
                    print(f"⏭️  目标已存在，跳过传输（使用 --force 强制覆盖）")
                    return True
            except:
                pass
        
        # 创建远程父目录
        parent_dir = str(Path(target_path).parent)
        mkdir_cmd = self._build_ssh_cmd(['ssh', '-p', self.ssh_port, '-o', 'StrictHostKeyChecking=no',
                                         self.remote_host, f'mkdir -p {parent_dir}'])
        try:
            subprocess.run(mkdir_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建远程目录失败: {e}")
            return False
        
        # 传输
        print(f"\n📤 开始传输...")
        
        if self.use_rsync:
            if self.ssh_password:
                cmd = [
                    'sshpass', '-p', self.ssh_password,
                    'rsync', '-avz', '--progress',
                    '-e', f'ssh -p {self.ssh_port} -o StrictHostKeyChecking=no',
                    f'{local_dir}/',
                    f'{self.remote_host}:{target_path}/'
                ]
            else:
                cmd = [
                    'rsync', '-avz', '--progress',
                    '-e', f'ssh -p {self.ssh_port} -o StrictHostKeyChecking=no',
                    f'{local_dir}/',
                    f'{self.remote_host}:{target_path}/'
                ]
        else:
            # scp 上传整个目录到父目录
            parent_path = str(Path(target_path).parent)
            dir_name = Path(target_path).name
            
            if self.ssh_password:
                cmd = [
                    'sshpass', '-p', self.ssh_password,
                    'scp', '-P', self.ssh_port, '-o', 'StrictHostKeyChecking=no', '-r',
                    str(local_dir),
                    f'{self.remote_host}:{parent_path}/'
                ]
            else:
                cmd = [
                    'scp', '-P', self.ssh_port, '-o', 'StrictHostKeyChecking=no', '-r',
                    str(local_dir),
                    f'{self.remote_host}:{parent_path}/'
                ]
            
            # 如果目录名不匹配，需要重命名
            if local_dir.name != dir_name:
                rename_needed = True
            else:
                rename_needed = False
        
        try:
            subprocess.run(cmd, check=True)
            
            # 如果需要重命名
            if not self.use_rsync and rename_needed:
                old_path = f"{parent_path}/{local_dir.name}"
                rename_cmd = self._build_ssh_cmd(['ssh', '-p', self.ssh_port, '-o', 'StrictHostKeyChecking=no',
                                                   self.remote_host, f'mv {old_path} {target_path}'])
                subprocess.run(rename_cmd, check=True, capture_output=True)
            
            print(f"✅ 传输完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 传输失败: {e}")
            return False
    
    def verify_sync(self, local_path: str, model_id: str, source: str) -> bool:
        """
        验证传输完整性
        
        Args:
            local_path: 本地路径
            model_id: 模型 ID
            source: modelscope/huggingface
        """
        local_dir = Path(local_path).expanduser().resolve()
        target_path = self._build_target_path(model_id, source)
        
        # 统计本地文件数
        local_files = list(local_dir.rglob('*'))
        local_count = len([f for f in local_files if f.is_file()])
        
        # 统计远程文件数
        count_cmd = self._build_ssh_cmd(['ssh', '-p', self.ssh_port, '-o', 'StrictHostKeyChecking=no',
                                         self.remote_host, f'find {target_path} -type f | wc -l'])
        try:
            result = subprocess.run(count_cmd, capture_output=True, text=True, check=True)
            remote_count = int(result.stdout.strip())
            
            print(f"\n🔍 验证传输:")
            print(f"   本地文件数: {local_count}")
            print(f"   远程文件数: {remote_count}")
            
            if local_count == remote_count:
                print(f"   ✅ 文件数匹配")
                return True
            else:
                print(f"   ❌ 文件数不匹配")
                return False
        except Exception as e:
            print(f"⚠️  验证失败: {e}")
            return False

