# -*- coding: utf-8 -*-
"""
下载器抽象基类
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseDownloader(ABC):
    """下载器抽象基类"""
    
    def __init__(self, model_cache: str):
        """
        初始化下载器
        
        Args:
            model_cache: 模型缓存目录
        """
        self.model_cache = model_cache
        Path(model_cache).mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查该下载器是否可用（依赖库是否已安装）
        
        Returns:
            True 表示可用，False 表示不可用
        """
        pass
    
    @abstractmethod
    def download(self, model_id: str) -> bool:
        """
        下载模型
        
        Args:
            model_id: 模型 ID
        
        Returns:
            True 表示下载成功，False 表示失败
        """
        pass
    
    def check_model_exists(self, model_id: str) -> bool:
        """
        检查模型是否已存在于缓存目录
        
        Args:
            model_id: 模型 ID
        
        Returns:
            True 表示模型已存在，False 表示需要下载
        """
        # 尝试多种可能的路径格式
        possible_paths = [
            # ModelScope 格式：hub/model_id
            Path(self.model_cache) / 'hub' / model_id,
            # HuggingFace 格式：models--org--name
            Path(self.model_cache) / f"models--{model_id.replace('/', '--')}",
            # 直接目录格式
            Path(self.model_cache) / model_id,
        ]
        
        for path in possible_paths:
            if path.exists() and any(path.iterdir()):
                return True
        
        return False
