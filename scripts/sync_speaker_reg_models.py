#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 speaker-reg 模型到 RunPod Volume
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model_syncer import ModelSyncer


def main():
    """同步 speaker-reg 模型"""
    print("🚀 开始同步 speaker-reg 模型到 Pod Volume\n")
    
    # 创建同步器（使用 SSH 密钥认证）
    syncer = ModelSyncer(
        remote_host='root@69.30.85.76:22068',
        remote_volume='/workspace'
    )
    
    # 同步目录
    success = syncer.sync_directory(
        local_path='/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/speaker-reg/models',
        model_id='speaker-reg',
        source='modelscope',
        force=False
    )
    
    if not success:
        print("\n❌ 同步失败")
        return 1
    
    # 验证传输
    if syncer.verify_sync(
        '/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/speaker-reg/models',
        'speaker-reg',
        'modelscope'
    ):
        print("\n✅ 验证通过")
    else:
        print("\n⚠️  验证失败，但文件可能已传输")
    
    print("\n✅ 同步完成！")
    print("目标路径: /workspace/models/hub/speaker-reg/")
    return 0


if __name__ == '__main__':
    exit(main())

