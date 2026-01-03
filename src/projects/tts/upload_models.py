#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传 TTS 本地模型到 RunPod Volume
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.uploaders.base_uploader import BaseUploader


class TTSUploader(BaseUploader):
    """TTS 项目上传器"""
    
    @property
    def local_models_path(self):
        return '/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/tts'
    
    @property
    def remote_host(self):
        return 'root@69.30.85.125:22147'
    
    @property
    def model_id(self):
        return 'tts'


if __name__ == '__main__':
    uploader = TTSUploader()
    exit(uploader.main())

