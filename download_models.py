# -*- coding: utf-8 -*-
"""
通用模型下载工具 - 支持 ModelScope / HuggingFace 等多种源
在 RunPod Pod 中运行，下载模型到 Volume

使用方法：
  python download_models.py model1 model2 model3 ...
  python download_models.py --file models.txt
  python download_models.py --source huggingface model1 model2
"""
import os
import sys
import argparse
from pathlib import Path

# 尝试导入 modelscope（如果可用）
try:
    import modelscope_patch
    from modelscope import snapshot_download as ms_download
    HAS_MODELSCOPE = True
except ImportError:
    HAS_MODELSCOPE = False

# 尝试导入 huggingface_hub（如果可用）
try:
    from huggingface_hub import snapshot_download as hf_download
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False


def download_to_volume(model_ids, source='auto'):
    """下载模型到 Volume"""
    
    print("=" * 60)
    print("🚀 通用模型下载工具")
    print("=" * 60)
    
    # 检测 Volume 路径
    volume_path = None
    for path in ['/workspace', '/runpod-volume', os.environ.get('RUNPOD_VOLUME_PATH', '')]:
        if path and os.path.exists(path) and os.path.isdir(path):
            volume_path = path
            break
    
    if not volume_path:
        print("❌ 未检测到 Volume，请确保在 RunPod Pod 中运行")
        sys.exit(1)
    
    model_cache = os.path.join(volume_path, 'models')
    Path(model_cache).mkdir(parents=True, exist_ok=True)
    
    # 设置缓存路径
    os.environ['MODELSCOPE_CACHE'] = model_cache
    os.environ['TRANSFORMERS_CACHE'] = model_cache
    os.environ['HF_HOME'] = model_cache
    
    print(f"📁 Volume: {volume_path}")
    print(f"📦 模型目录: {model_cache}")
    print(f"📊 待下载: {len(model_ids)} 个模型\n")
    
    # 下载所有模型
    print("=" * 60)
    print("开始下载...")
    print("=" * 60)
    
    success = 0
    failed = []
    
    for i, model_id in enumerate(model_ids, 1):
        print(f"\n[{i}/{len(model_ids)}] {model_id}")
        
        try:
            # 自动选择下载源
            if source == 'auto':
                # 简单判断：如果包含中文组织名，优先 ModelScope
                if model_id.startswith(('iic/', 'damo/', 'alibaba/')):
                    use_source = 'modelscope'
                else:
                    use_source = 'huggingface' if HAS_HUGGINGFACE else 'modelscope'
            else:
                use_source = source
            
            # 执行下载
            if use_source == 'modelscope':
                if not HAS_MODELSCOPE:
                    print("  ❌ ModelScope 未安装")
                    failed.append(model_id)
                    continue
                ms_download(model_id, cache_dir=model_cache)
                print(f"  ✅ 下载完成 (ModelScope)")
                
            elif use_source == 'huggingface':
                if not HAS_HUGGINGFACE:
                    print("  ❌ HuggingFace Hub 未安装")
                    failed.append(model_id)
                    continue
                hf_download(model_id, cache_dir=model_cache)
                print(f"  ✅ 下载完成 (HuggingFace)")
            
            success += 1
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            failed.append(model_id)
    
    # 统计
    print("\n" + "=" * 60)
    print("📊 下载统计")
    print("=" * 60)
    print(f"✅ 成功: {success}/{len(model_ids)}")
    if failed:
        print(f"❌ 失败: {len(failed)}")
        for model in failed:
            print(f"  - {model}")
    print(f"\n💾 存储位置: {model_cache}")
    print("可以删除此 Pod，模型已保存在 Volume\n")


def download_from_projects():
    """从项目配置下载所有模型（调度模式）"""
    from projects.loader import ProjectLoader
    
    # 打印项目摘要
    ProjectLoader.print_summary()
    
    # 获取所有项目
    projects = ProjectLoader.get_all_projects()
    
    if not projects:
        print("\n❌ 未找到任何项目配置")
        print("请在 projects/ 目录下添加项目配置")
        sys.exit(1)
    
    # 检测 Volume 路径
    volume_path = None
    for path in ['/workspace', '/runpod-volume', os.environ.get('RUNPOD_VOLUME_PATH', '')]:
        if path and os.path.exists(path) and os.path.isdir(path):
            volume_path = path
            break
    
    if not volume_path:
        print("\n❌ 未检测到 Volume，请确保在 RunPod Pod 中运行")
        sys.exit(1)
    
    model_cache = os.path.join(volume_path, 'models')
    Path(model_cache).mkdir(parents=True, exist_ok=True)
    
    # 设置缓存路径
    os.environ['MODELSCOPE_CACHE'] = model_cache
    os.environ['TRANSFORMERS_CACHE'] = model_cache
    os.environ['HF_HOME'] = model_cache
    
    print(f"\n{'='*60}")
    print("🚀 开始下载模型到 Volume")
    print(f"{'='*60}")
    print(f"📁 Volume: {volume_path}")
    print(f"📦 模型目录: {model_cache}\n")
    
    # 调度各个项目进行下载
    for project in projects:
        project.download_models(model_cache)
    
    print(f"\n{'='*60}")
    print("✅ 所有项目下载完成")
    print(f"{'='*60}")
    print(f"💾 存储位置: {model_cache}")
    print("可以删除此 Pod，模型已保存在 Volume\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='通用模型下载工具')
    parser.add_argument('--all', '-a', action='store_true', 
                        help='下载所有项目配置的模型')
    parser.add_argument('models', nargs='*', help='模型 ID 列表（手动指定）')
    parser.add_argument('--source', '-s', choices=['auto', 'modelscope', 'huggingface'], 
                        default='auto', help='下载源（手动模式）')
    
    args = parser.parse_args()
    
    if args.all or not args.models:
        # 从项目配置下载
        download_from_projects()
    else:
        # 手动指定模型
        model_ids = list(args.models)
        download_to_volume(model_ids, source=args.source)
