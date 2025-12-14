#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunPod S3 配置管理
"""
import os
from pathlib import Path
from typing import Optional, Dict
try:
    import configparser
except ImportError:
    configparser = None


class S3Config:
    """S3 配置管理器"""

    # 参考官方文档：S3 API 可能只在部分 datacenter 可用。
    # 这里仅用于提示，不应作为硬性校验（避免文档/服务变更导致误判）。
    SUPPORTED_DATACENTERS = {
        "eur-is-1",
        "eu-ro-1",
        "eu-cz-1",
        "us-ks-2",
        "us-ca-2",
        "us-il-1",
    }
    
    def __init__(self, profile: str = 'runpods3'):
        """
        初始化 S3 配置
        
        Args:
            profile: 配置文件中的 profile 名称
        """
        self.profile = profile
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, str]:
        """
        加载 S3 配置
        优先级: 环境变量 > 配置文件
        """
        config = {}
        
        # 1. 尝试从环境变量加载
        if os.getenv('RUNPOD_S3_ACCESS_KEY'):
            config['access_key'] = os.getenv('RUNPOD_S3_ACCESS_KEY')
            config['secret_key'] = os.getenv('RUNPOD_S3_SECRET_KEY')
            config['datacenter'] = os.getenv('RUNPOD_DATACENTER')
            config['volume_id'] = os.getenv('RUNPOD_VOLUME_ID')
            if os.getenv('RUNPOD_S3_ENDPOINT_URL'):
                config['endpoint_url'] = os.getenv('RUNPOD_S3_ENDPOINT_URL')
            return config
        
        # 2. 尝试从配置文件加载
        if configparser:
            config_file = Path.home() / '.runpod_s3_config'
            if config_file.exists():
                parser = configparser.ConfigParser()
                parser.read(config_file)
                if self.profile in parser:
                    section = parser[self.profile]
                    config['access_key'] = section.get('aws_access_key_id')
                    config['secret_key'] = section.get('aws_secret_access_key')
                    config['datacenter'] = section.get('datacenter')
                    config['volume_id'] = section.get('volume_id')
                    endpoint_url = section.get('endpoint_url')
                    if endpoint_url:
                        config['endpoint_url'] = endpoint_url
                    return config
        
        return config
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        if not all(k in self.config for k in ['access_key', 'secret_key', 'volume_id', 'datacenter']):
            return False
        return bool((self.config.get('datacenter') or '').strip())

    def is_datacenter_supported(self) -> bool:
        """检查当前 datacenter 是否支持 S3 API。"""
        datacenter = (self.config.get('datacenter') or '').strip().lower()
        return bool(datacenter) and datacenter in self.SUPPORTED_DATACENTERS

    def get_unsupported_datacenter_message(self) -> str:
        """获取 datacenter 不支持时的提示信息。"""
        datacenter = (self.config.get('datacenter') or '').strip()
        supported = ", ".join(sorted(self.SUPPORTED_DATACENTERS))
        return (
            f"RunPod S3 API 不支持 datacenter={datacenter!r}。"
            f"支持的 datacenter: {supported}。"
            "请在支持的 datacenter 创建 Volume，或在配置中提供 endpoint_url 覆盖。"
        )

    def get_endpoint_url(self) -> str:
        """获取 S3 endpoint URL"""
        endpoint_url = (self.config.get('endpoint_url') or '').strip()
        if endpoint_url:
            return endpoint_url
        datacenter = (self.config.get('datacenter') or '').strip().lower()
        if not datacenter:
            raise ValueError("S3 未配置 datacenter")
        return f"https://s3api-{datacenter}.runpod.io/"
    
    def get_region(self) -> str:
        """获取 region 名称"""
        return (self.config.get('datacenter') or '').strip().lower()
    
    @property
    def access_key(self) -> Optional[str]:
        return self.config.get('access_key')
    
    @property
    def secret_key(self) -> Optional[str]:
        return self.config.get('secret_key')
    
    @property
    def volume_id(self) -> Optional[str]:
        return self.config.get('volume_id')
