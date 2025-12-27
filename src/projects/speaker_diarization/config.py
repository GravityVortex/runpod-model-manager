# -*- coding: utf-8 -*-
"""
说话人分割项目配置
"""
import os
from pathlib import Path
from ..base import BaseProject
from downloaders.factory import DownloaderFactory


class SpeakerDiarizationProject(BaseProject):
    """说话人分割项目"""
    
    @property
    def name(self):
        return "speaker-diarization"
    
    @property
    def models(self):
        return {
            'modelscope': [
                "iic/speech_campplus_speaker-diarization_common",
                "damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                "damo/speech_campplus_sv_zh-cn_16k-common",
                "damo/speech_campplus-transformer_scl_zh-cn_16k-common",
            ]
        }
    
    @property
    def dependencies_config(self):
        """依赖配置文件路径 (dependencies.yaml)"""
        current_dir = Path(__file__).parent
        return str(current_dir / 'dependencies.yaml')
    
    @property
    def local_models_path(self):
        """本地模型路径"""
        return '/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/speaker-reg/models'
    
    @property
    def upload_remote_host(self):
        """上传目标 SSH 连接"""
        return 'root@69.30.85.76:22068'
    
    @property
    def upload_model_id(self):
        """上传的模型 ID"""
        return 'speaker-reg'
    
    def download_models(self, model_cache: str):
        """下载 ModelScope 模型"""
        print(f"\n{'='*60}")
        print(f"📦 项目: {self.name}")
        print(f"{'='*60}")
        
        all_models = self.get_all_models()
        success = 0
        skipped = 0
        failed = []
        
        for i, (model_id, source) in enumerate(all_models, 1):
            print(f"\n[{i}/{len(all_models)}] {model_id} ({source})")
            
            # 获取对应的下载器
            try:
                downloader = DownloaderFactory.get_downloader(source, model_cache)
            except ValueError as e:
                print(f"  ❌ {e}")
                failed.append(model_id)
                continue
            
            # 检查模型是否已存在
            if downloader.check_model_exists(model_id):
                print(f"  ⏭️  已存在，跳过")
                skipped += 1
                continue
            
            # 下载模型
            if downloader.download(model_id):
                print(f"  ✅ 下载完成")
                success += 1
            else:
                failed.append(model_id)
        
        # 统计
        print(f"\n{'='*60}")
        print(f"📊 {self.name} 统计")
        print(f"{'='*60}")
        print(f"✅ 下载成功: {success}")
        print(f"⏭️  跳过（已存在）: {skipped}")
        if failed:
            print(f"❌ 失败: {len(failed)}")
            for model in failed:
                print(f"  - {model}")
