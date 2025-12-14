# -*- coding: utf-8 -*-
"""
HuggingFace 下载器
"""
from .base_downloader import BaseDownloader


class HuggingFaceDownloader(BaseDownloader):
    """HuggingFace 下载器"""
    
    def is_available(self) -> bool:
        """检查 HuggingFace Hub 是否可用"""
        try:
            from huggingface_hub import snapshot_download
            return True
        except ImportError:
            return False
    
    def download(self, model_id: str) -> bool:
        """
        从 HuggingFace 下载模型
        
        Args:
            model_id: 模型 ID
        
        Returns:
            True 表示下载成功，False 表示失败
        """
        if not self.is_available():
            print("  ❌ HuggingFace Hub 未安装")
            return False
        
        try:
            from huggingface_hub import snapshot_download as hf_download
            hf_download(model_id, cache_dir=self.model_cache)
            return True
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False
