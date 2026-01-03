# -*- coding: utf-8 -*-
"""
TTS 项目配置
"""
from pathlib import Path
from ..base import BaseProject


class TTSProject(BaseProject):
    """TTS 项目"""
    
    @property
    def name(self):
        return "tts"
    
    @property
    def models(self):
        return {}
    
    @property
    def dependencies_config(self):
        """依赖配置文件路径 (dependencies.yaml)"""
        current_dir = Path(__file__).parent
        return str(current_dir / 'dependencies.yaml')
    
    @property
    def local_models_path(self):
        """本地模型路径"""
        return '/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/tts'
    
    @property
    def upload_remote_host(self):
        """上传目标 SSH 连接"""
        return 'root@69.30.85.125:22147'
    
    @property
    def upload_model_id(self):
        """上传的模型 ID"""
        return 'tts'
    
    def download_models(self, model_cache: str):
        """无需下载模型"""
        print(f"\n{'='*60}")
        print(f"📦 项目: {self.name}")
        print(f"{'='*60}")
        print("  ℹ️  该项目无需下载模型，仅支持本地上传")

