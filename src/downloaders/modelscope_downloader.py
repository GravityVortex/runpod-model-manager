# -*- coding: utf-8 -*-
"""
ModelScope 下载器
"""
from .base_downloader import BaseDownloader


class ModelScopeDownloader(BaseDownloader):
    """ModelScope 下载器"""
    
    def is_available(self) -> bool:
        """检查 ModelScope 是否可用"""
        try:
            import modelscope_patch
            from modelscope import snapshot_download
            return True
        except ImportError:
            return False
    
    def download(self, model_id: str) -> bool:
        """
        从 ModelScope 下载模型
        
        Args:
            model_id: 模型 ID
        
        Returns:
            True 表示下载成功，False 表示失败
        """
        if not self.is_available():
            print("  ❌ ModelScope 未安装")
            return False
        
        try:
            from modelscope import snapshot_download as ms_download
            ms_download(model_id, cache_dir=self.model_cache)
            return True
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False
