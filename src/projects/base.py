# -*- coding: utf-8 -*-
"""
项目配置基类
每个项目继承这个类，定义自己需要的模型和依赖
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


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
    
    @property
    def dependencies_config(self) -> Optional[str]:
        """
        依赖配置文件路径 (dependencies.yaml)
        返回格式: 'path/to/dependencies.yaml'
        支持多索引源的配置化依赖管理
        如果返回 None，表示项目无依赖管理
        """
        return None
    
    @property
    def python_version(self) -> str:
        """
        项目所需的 Python 版本
        返回格式: '3.10', '3.11', etc.
        用于隔离不同 Python 版本的依赖
        """
        return '3.10'  # 默认 3.10
    
    @property
    def models_remote_prefix(self) -> str:
        """
        模型在 Volume 中的子目录名（项目隔离）
        默认使用项目名，子类可覆盖
        
        示例: 'speaker-reg' 
        结果: /runpod-volume/models/speaker-reg/
        """
        return self.name
    
    @property
    def local_models_dir(self) -> Optional[str]:
        """
        本地模型目录（用于 S3 上传）
        返回本地模型文件的根目录路径
        
        示例: '/Users/xxx/Downloads/speaker-reg/models'
        上传后: /runpod-volume/models/speaker-reg/...
        
        返回 None 表示需要通过命令行参数指定
        """
        return None
    
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
