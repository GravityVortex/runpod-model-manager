#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传脚本基类
"""
from abc import ABC, abstractmethod


class BaseUploader(ABC):
    """上传脚本基类"""
    
    @property
    @abstractmethod
    def local_models_path(self) -> str:
        """本地模型路径"""
        pass
    
    @property
    @abstractmethod
    def remote_host(self) -> str:
        """SSH 连接 (user@host:port)"""
        pass
    
    @property
    @abstractmethod
    def model_id(self) -> str:
        """模型 ID"""
        pass
    
    @property
    def remote_volume(self) -> str:
        """远程 volume 路径"""
        return '/workspace'
    
    @property
    def source(self) -> str:
        """模型源"""
        return 'modelscope'
    
    def main(self):
        """统一上传入口"""
        from src.model_syncer import ModelSyncer
        
        print(f"🚀 开始上传模型\n")
        print(f"📂 本地路径: {self.local_models_path}")
        print(f"🔗 远程主机: {self.remote_host}")
        print(f"📦 模型 ID: {self.model_id}\n")
        
        # 创建同步器
        syncer = ModelSyncer(
            remote_host=self.remote_host,
            remote_volume=self.remote_volume
        )
        
        # 上传模型
        success = syncer.sync_directory(
            local_path=self.local_models_path,
            model_id=self.model_id,
            source=self.source,
            force=False
        )
        
        if not success:
            print("\n❌ 上传失败")
            return 1
        
        # 验证传输
        if syncer.verify_sync(self.local_models_path, self.model_id, self.source):
            print("\n✅ 验证通过")
        else:
            print("\n⚠️  验证失败，但文件可能已传输")
        
        print(f"\n✅ 上传完成！")
        print(f"目标路径: {self.remote_volume}/models/{self.model_id}/")
        return 0


