# -*- coding: utf-8 -*-
"""
下载器模块
"""
from .base_downloader import BaseDownloader
from .modelscope_downloader import ModelScopeDownloader
from .huggingface_downloader import HuggingFaceDownloader

__all__ = ['BaseDownloader', 'ModelScopeDownloader', 'HuggingFaceDownloader']
