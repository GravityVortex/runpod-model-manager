#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台任务管理器
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import random
import string


class TaskManager:
    """后台任务管理器"""
    
    def __init__(self, volume_path: str):
        """
        初始化
        
        Args:
            volume_path: Volume 根目录
        """
        self.volume_path = Path(volume_path)
        self.tasks_dir = self.volume_path / '.metadata' / 'tasks'
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_task_id(self, prefix: str = "deps_install") -> str:
        """生成唯一任务ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def start_background_task(self, command_args: list, task_id: str = None) -> dict:
        """
        启动后台任务
        
        Args:
            command_args: 命令参数列表（不包含 --async）
            task_id: 任务ID（可选，不提供则自动生成）
        
        Returns:
            任务信息字典
        """
        if task_id is None:
            task_id = self.generate_task_id()
        
        # 创建日志文件
        log_file = self.tasks_dir / f"{task_id}.log"
        
        # 构建后台命令（移除 --async 参数）
        bg_command = [sys.executable] + [arg for arg in command_args if arg != '--async']
        
        # 启动后台进程
        with open(log_file, 'w') as log_f:
            process = subprocess.Popen(
                bg_command,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                start_new_session=True  # 脱离当前会话
            )
        
        # 保存任务元数据
        task_info = {
            'task_id': task_id,
            'command': ' '.join(command_args),
            'status': 'running',
            'pid': process.pid,
            'log_file': str(log_file),
            'started_at': datetime.now().isoformat(),
            'progress': {
                'current_group': None,
                'total_groups': 0,
                'completed_groups': 0
            }
        }
        
        metadata_file = self.tasks_dir / f"{task_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(task_info, f, indent=2)
        
        return task_info
    
    def get_task_status(self, task_id: str) -> dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务信息字典
        """
        metadata_file = self.tasks_dir / f"{task_id}.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"任务不存在: {task_id}")
        
        with open(metadata_file, 'r') as f:
            task_info = json.load(f)
        
        # 检查进程是否还在运行
        if task_info['status'] == 'running':
            pid = task_info['pid']
            try:
                os.kill(pid, 0)  # 检查进程是否存在
            except OSError:
                # 进程已结束，更新状态
                task_info['status'] = self._detect_final_status(task_info['log_file'])
                task_info['completed_at'] = datetime.now().isoformat()
                with open(metadata_file, 'w') as f:
                    json.dump(task_info, f, indent=2)
        
        # 解析日志获取最新进度
        task_info['progress'] = self._parse_log_progress(task_info['log_file'])
        
        return task_info
    
    def _detect_final_status(self, log_file: str) -> str:
        """从日志检测最终状态"""
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                if '✅ 安装完成' in content or '✅ 所有依赖完整可用' in content:
                    return 'completed'
                elif '❌' in content or 'failed' in content.lower():
                    return 'failed'
                return 'completed'
        except:
            return 'unknown'
    
    def _parse_log_progress(self, log_file: str) -> dict:
        """解析日志获取进度信息"""
        progress = {
            'current_group': None,
            'total_groups': 0,
            'completed_groups': 0,
            'success_count': 0,
            'failed_count': 0,
            'retry_count': 0
        }
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                # 解析组进度
                if '[PROGRESS]' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('group='):
                            progress['current_group'] = part.split('=')[1]
                        elif part.startswith('current='):
                            progress['completed_groups'] = int(part.split('=')[1])
                        elif part.startswith('total='):
                            progress['total_groups'] = int(part.split('=')[1])
                
                # 统计成功/失败
                if '[SUCCESS]' in line:
                    progress['success_count'] += 1
                elif '[FAILED]' in line:
                    progress['failed_count'] += 1
                elif '[RETRY]' in line:
                    progress['retry_count'] += 1
                
                # 兼容原有日志格式
                if '✅ 组' in line and '安装成功' in line:
                    progress['success_count'] += 1
                elif '❌ 组' in line and '安装失败' in line:
                    progress['failed_count'] += 1
        
        except Exception as e:
            pass
        
        return progress
    
    def list_tasks(self) -> list:
        """列出所有任务"""
        tasks = []
        for metadata_file in self.tasks_dir.glob('*.json'):
            try:
                with open(metadata_file, 'r') as f:
                    task_info = json.load(f)
                    tasks.append(task_info)
            except:
                continue
        
        # 按开始时间倒序排序
        tasks.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        return tasks
    
    def stop_task(self, task_id: str, force: bool = False) -> bool:
        """
        停止任务
        
        Args:
            task_id: 任务ID
            force: 是否强制终止（SIGKILL）
        
        Returns:
            是否成功
        """
        metadata_file = self.tasks_dir / f"{task_id}.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"任务不存在: {task_id}")
        
        with open(metadata_file, 'r') as f:
            task_info = json.load(f)
        
        if task_info['status'] != 'running':
            return False
        
        pid = task_info['pid']
        
        try:
            # 检查进程是否存在
            os.kill(pid, 0)
            
            # 终止进程
            import signal
            if force:
                os.kill(pid, signal.SIGKILL)  # 强制终止
            else:
                os.kill(pid, signal.SIGTERM)  # 优雅终止
            
            # 更新状态
            task_info['status'] = 'stopped'
            task_info['stopped_at'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(task_info, f, indent=2)
            
            return True
        
        except ProcessLookupError:
            # 进程不存在
            task_info['status'] = 'completed'
            with open(metadata_file, 'w') as f:
                json.dump(task_info, f, indent=2)
            return False
        except PermissionError:
            raise PermissionError(f"没有权限终止进程 {pid}")
        except Exception as e:
            raise Exception(f"终止任务失败: {e}")

