#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试一站式部署功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.projects.speaker_diarization.config import SpeakerDiarizationProject
from src.project_uploader import ProjectUploader


def test_project_config():
    """测试项目配置"""
    print("=" * 60)
    print("测试 1: 项目配置")
    print("=" * 60)
    
    project = SpeakerDiarizationProject()
    
    # 测试基本属性
    assert project.name == "speaker-diarization", "项目名称错误"
    print(f"✅ 项目名称: {project.name}")
    
    # 测试新增属性
    assert project.models_remote_prefix == "speaker-reg", "远程前缀错误"
    print(f"✅ 远程前缀: {project.models_remote_prefix}")
    
    assert project.local_models_dir is None, "本地目录应为 None"
    print(f"✅ 本地目录: {project.local_models_dir} (默认 None)")
    
    assert project.python_version == "3.10", "Python 版本错误"
    print(f"✅ Python 版本: {project.python_version}")
    
    print("\n✅ 测试 1 通过\n")


def test_uploader_without_models_dir():
    """测试上传器（无模型目录）"""
    print("=" * 60)
    print("测试 2: 上传器（无模型目录）")
    print("=" * 60)
    
    project = SpeakerDiarizationProject()
    
    # 应该返回错误码 1
    result = ProjectUploader.upload(project, models_dir=None)
    assert result == 1, "应该返回错误码 1"
    print("✅ 正确处理缺少模型目录的情况")
    
    print("\n✅ 测试 2 通过\n")


def test_deploy_command_import():
    """测试 deploy 命令导入"""
    print("=" * 60)
    print("测试 3: deploy 命令导入")
    print("=" * 60)
    
    try:
        from src.commands.deploy import handle_deploy
        print("✅ deploy 命令导入成功")
        
        # 检查函数签名
        import inspect
        sig = inspect.signature(handle_deploy)
        assert 'args' in sig.parameters, "handle_deploy 应该接受 args 参数"
        print("✅ handle_deploy 函数签名正确")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        sys.exit(1)
    
    print("\n✅ 测试 3 通过\n")


def test_cli_integration():
    """测试 CLI 集成"""
    print("=" * 60)
    print("测试 4: CLI 集成")
    print("=" * 60)
    
    # 读取 volume_cli.py 检查是否包含 deploy 命令
    cli_file = Path(__file__).parent.parent / "volume_cli.py"
    content = cli_file.read_text()
    
    assert "deploy" in content, "CLI 应该包含 deploy 命令"
    print("✅ CLI 包含 deploy 命令")
    
    assert "handle_deploy" in content, "CLI 应该导入 handle_deploy"
    print("✅ CLI 导入 handle_deploy")
    
    assert "--models-dir" in content, "CLI 应该支持 --models-dir 参数"
    print("✅ CLI 支持 --models-dir 参数")
    
    assert "--skip-upload" in content, "CLI 应该支持 --skip-upload 参数"
    print("✅ CLI 支持 --skip-upload 参数")
    
    print("\n✅ 测试 4 通过\n")


def test_upload_script_exists():
    """测试上传脚本存在"""
    print("=" * 60)
    print("测试 5: 上传脚本存在")
    print("=" * 60)
    
    script_path = Path(__file__).parent.parent / "src/projects/speaker_diarization/upload_models.py"
    assert script_path.exists(), "上传脚本应该存在"
    print(f"✅ 上传脚本存在: {script_path}")
    
    # 检查脚本内容
    content = script_path.read_text()
    assert "ProjectUploader" in content, "脚本应该使用 ProjectUploader"
    print("✅ 脚本使用 ProjectUploader")
    
    assert "main_cli" in content, "脚本应该调用 main_cli"
    print("✅ 脚本调用 main_cli")
    
    print("\n✅ 测试 5 通过\n")


def test_documentation_exists():
    """测试文档存在"""
    print("=" * 60)
    print("测试 6: 文档存在")
    print("=" * 60)
    
    # 检查 DEPLOYMENT_GUIDE.md
    doc_path = Path(__file__).parent.parent / "DEPLOYMENT_GUIDE.md"
    assert doc_path.exists(), "DEPLOYMENT_GUIDE.md 应该存在"
    print(f"✅ 部署文档存在: {doc_path}")
    
    content = doc_path.read_text()
    assert "一站式部署" in content, "文档应该包含一站式部署说明"
    print("✅ 文档包含一站式部署说明")
    
    # 检查 MODEL_DEPLOYMENT_GUIDE.md 更新
    model_doc = Path(__file__).parent.parent / "MODEL_DEPLOYMENT_GUIDE.md"
    model_content = model_doc.read_text()
    assert "DEPLOYMENT_GUIDE.md" in model_content, "应该链接到新文档"
    print("✅ MODEL_DEPLOYMENT_GUIDE.md 已更新链接")
    
    print("\n✅ 测试 6 通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 开始测试一站式部署功能")
    print("=" * 60 + "\n")
    
    tests = [
        test_project_config,
        test_uploader_without_models_dir,
        test_deploy_command_import,
        test_cli_integration,
        test_upload_script_exists,
        test_documentation_exists,
    ]
    
    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}\n")
            failed.append(test.__name__)
        except Exception as e:
            print(f"❌ 测试异常: {test.__name__}")
            print(f"   错误: {e}\n")
            failed.append(test.__name__)
    
    # 总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"总计: {len(tests)} 个测试")
    print(f"通过: {len(tests) - len(failed)} 个")
    print(f"失败: {len(failed)} 个")
    
    if failed:
        print(f"\n❌ 失败的测试:")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print("\n✅ 所有测试通过！")
        return 0


if __name__ == '__main__':
    sys.exit(main())

