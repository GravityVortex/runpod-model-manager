# -*- coding: utf-8 -*-
"""
下载器工厂 - 用于创建和获取下载器实例
"""
from typing import Dict, Type
from .base_downloader import BaseDownloader
from .modelscope_downloader import ModelScopeDownloader
from .huggingface_downloader import HuggingFaceDownloader


class DownloaderFactory:
    """下载器工厂类"""
    
    # 注册所有可用的下载器
    _downloaders: Dict[str, Type[BaseDownloader]] = {
        'modelscope': ModelScopeDownloader,
        'huggingface': HuggingFaceDownloader,
    }
    
    @classmethod
    def get_downloader(cls, source: str, model_cache: str) -> BaseDownloader:
        """
        获取指定源的下载器实例
        
        Args:
            source: 下载源名称 ('modelscope', 'huggingface' 等)
            model_cache: 模型缓存目录
        
        Returns:
            下载器实例
        
        Raises:
            ValueError: 如果下载源不支持
        """
        downloader_class = cls._downloaders.get(source)
        if not downloader_class:
            raise ValueError(f"不支持的下载源: {source}")
        
        return downloader_class(model_cache)
    
    @classmethod
    def register_downloader(cls, source: str, downloader_class: Type[BaseDownloader]):
        """
        注册新的下载器
        
        Args:
            source: 下载源名称
            downloader_class: 下载器类
        """
        cls._downloaders[source] = downloader_class
    
    @classmethod
    def get_available_sources(cls) -> list:
        """
        获取所有已注册的下载源
        
        Returns:
            下载源名称列表
        """
        return list(cls._downloaders.keys())
