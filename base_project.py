# -*- coding: utf-8 -*-
"""
项目配置基类
每个项目继承这个类，定义自己需要的模型
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseProject(ABC):
    """项目配置抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """项目名称"""
        pass
    
    @property
    @abstractmethod
    def models(self) -> Dict[str, List[str]]:
        """
        模型列表，按源分组
        返回格式: {
            'modelscope': ['model1', 'model2'],
            'huggingface': ['model3', 'model4'],
        }
        """
        pass
    
    def get_all_models(self) -> List[tuple]:
        """获取所有模型（返回 (model_id, source) 列表）"""
        all_models = []
        for source, model_list in self.models.items():
            for model_id in model_list:
                all_models.append((model_id, source))
        return all_models
    
    @abstractmethod
    def download_models(self, model_cache: str):
        """
        下载项目所需的所有模型
        每个子类必须实现此方法，定义自己的下载逻辑
        
        Args:
            model_cache: 模型缓存目录
        """
        pass
    
    def __repr__(self):
        total = sum(len(models) for models in self.models.values())
        return f"<{self.name}: {total} 个模型>"
