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
    
    @property
    def local_models_path(self) -> Optional[str]:
        """本地模型路径（用于上传）"""
        return None
    
    @property
    def upload_remote_host(self) -> Optional[str]:
        """上传目标 SSH 连接 (user@host:port)"""
        return None
    
    @property
    def upload_remote_volume(self) -> str:
        """上传目标 volume 路径"""
        return '/workspace'
    
    @property
    def upload_model_id(self) -> Optional[str]:
        """上传的模型 ID"""
        return None
    
    @property
    def upload_source(self) -> str:
        """上传的模型源（modelscope/huggingface）"""
        return 'modelscope'
    
    def upload_models(self):
        """
        上传本地模型到远程 Volume
        使用子类定义的配置参数
        """
        if not self.local_models_path:
            print("❌ 未配置本地模型路径")
            return False
        
        if not self.upload_remote_host:
            print("❌ 未配置远程主机")
            return False
        
        if not self.upload_model_id:
            print("❌ 未配置模型 ID")
            return False
        
        from src.model_syncer import ModelSyncer
        
        print(f"\n{'='*60}")
        print(f"📤 上传本地模型: {self.name}")
        print(f"{'='*60}")
        
        # 创建同步器
        syncer = ModelSyncer(
            remote_host=self.upload_remote_host,
            remote_volume=self.upload_remote_volume
        )
        
        # 上传模型
        success = syncer.sync_directory(
            local_path=self.local_models_path,
            model_id=self.upload_model_id,
            source=self.upload_source,
            force=False
        )
        
        if not success:
            print("\n❌ 上传失败")
            return False
        
        # 验证传输
        if syncer.verify_sync(self.local_models_path, self.upload_model_id, self.upload_source):
            print("\n✅ 验证通过")
        else:
            print("\n⚠️  验证失败，但文件可能已传输")
        
        print(f"\n✅ 上传完成！")
        print(f"目标路径: {self.upload_remote_volume}/models/hub/{self.upload_model_id}/")
        return True
    
    def __repr__(self):
        total = sum(len(models) for models in self.models.values())
        return f"<{self.name}: {total} 个模型>"
