# -*- coding: utf-8 -*-
"""
项目加载器 - 统一管理所有项目配置
"""
from typing import List, Optional
from .base import BaseProject

# 导入各项目配置
from .speaker_reg import SpeakerDiarizationProject
from .v_a_processing import VAProcessingProject


class ProjectLoader:
    """项目加载器"""
    
    # 注册所有启用的项目
    PROJECTS = [
        SpeakerDiarizationProject(),  # 说话人分割（包含你业务项目需要的所有模型）
        VAProcessingProject(),  # V-A Processing 项目
    ]
    
    @classmethod
    def get_all_projects(cls) -> List[BaseProject]:
        """获取所有项目"""
        return cls.PROJECTS
    
    @classmethod
    def get_project(cls, name: str) -> Optional[BaseProject]:
        """根据名称获取项目"""
        for project in cls.PROJECTS:
            if project.name == name:
                return project
        raise ValueError(f"项目不存在: {name}")
    
    @classmethod
    def get_all_models(cls):
        """获取所有项目的所有模型（去重）"""
        all_models = {}
        for project in cls.PROJECTS:
            for model_id, source in project.get_all_models():
                # 去重，同一模型只记录一次
                if model_id not in all_models:
                    all_models[model_id] = source
        return all_models
    
    @classmethod
    def print_summary(cls):
        """打印摘要"""
        print("=" * 60)
        print("📋 已注册项目")
        print("=" * 60)
        for project in cls.PROJECTS:
            total = sum(len(models) for models in project.models.values())
            print(f"  • {project.name}: {total} 个模型")
            for source, models in project.models.items():
                if models:
                    print(f"    - {source}: {len(models)} 个")
        
        all_models = cls.get_all_models()
        print(f"\n📊 总计: {len(all_models)} 个模型（已去重）")
        print("=" * 60)


# 便捷函数
def get_project(name: str) -> BaseProject:
    """获取项目（便捷函数）"""
    return ProjectLoader.get_project(name)


if __name__ == "__main__":
    ProjectLoader.print_summary()
