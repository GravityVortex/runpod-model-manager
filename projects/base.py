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
    def requirements_file(self) -> Optional[str]:
        """
        requirements.txt 文件路径（相对于项目根目录）
        返回格式: 'path/to/requirements.txt'
        如果不需要依赖管理，返回 None
        """
        return None
    
    @property
    def dependencies(self) -> Optional[List[str]]:
        """
        从 requirements.txt 读取依赖列表
        子类一般不需要重写此方法，只需指定 requirements_file
        """
        if not self.requirements_file:
            return None
        
        import os
        from pathlib import Path
        
        # 支持绝对路径或相对路径
        req_file = Path(self.requirements_file)
        if not req_file.is_absolute():
            # 相对路径，从当前工作目录解析
            req_file = Path.cwd() / req_file
        
        if not req_file.exists():
            print(f"⚠️  requirements.txt 未找到: {req_file}")
            return None
        
        # 读取并解析
        deps = []
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('#'):
                    deps.append(line)
        
        return deps if deps else None
    
    @property
    def python_version(self) -> str:
        """
        项目所需的 Python 版本
        返回格式: '3.10', '3.11', etc.
        用于隔离不同 Python 版本的依赖
        """
        return '3.10'  # 默认 3.10
    
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
