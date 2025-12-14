#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令共用工具函数
"""
import os
import sys


def detect_volume_path():
    """检测 Volume 挂载路径"""
    possible_paths = [
        '/workspace',           # RunPod Pod 默认
        '/runpod-volume',       # Serverless 常用
        os.environ.get('RUNPOD_VOLUME_PATH', ''),
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path) and os.access(path, os.W_OK):
            return path
    
    raise RuntimeError(
        "❌ 未找到可写的 Volume 挂载点\n"
        "请确保 Volume 已正确挂载到以下路径之一:\n"
        "  - /workspace (RunPod Pod)\n"
        "  - /runpod-volume (Serverless)\n"
        "或设置环境变量 RUNPOD_VOLUME_PATH"
    )
