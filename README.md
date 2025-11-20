# RunPod 模型管理中心

集中管理所有项目的模型，一次性下载到 RunPod Volume。

## 🎯 设计理念

采用**插件化架构**，每个项目一个配置文件，上层统一管理：

```
├── base_project.py          # 项目抽象基类
├── model_downloader.py      # 下载器工厂
├── downloaders/             # 下载器模块
│   ├── base_downloader.py         # 下载器基类
│   ├── modelscope_downloader.py   # ModelScope 下载器
│   └── huggingface_downloader.py  # HuggingFace 下载器
├── projects/                # 项目配置目录
│   ├── speaker_diarization.py     # 现有项目
│   └── your_project.py            # 添加更多...
├── project_loader.py        # 项目加载器
└── download_models.py       # 下载调度器
```

## 🚀 快速开始

### 1. 添加你的项目配置

在 `projects/` 目录创建新文件，例如 `my_project.py`：

```python
from base_project import BaseProject
from model_downloader import DownloaderFactory

class MyProject(BaseProject):
    @property
    def name(self):
        return "my-project"
    
    @property
    def models(self):
        return {
            'modelscope': [
                "org/model-1",
                "org/model-2",
            ],
            'huggingface': [
                "org/model-3",
            ]
        }
    
    def download_models(self, model_cache: str):
        """实现下载逻辑"""
        # 统计信息
        success = 0
        skipped = 0
        failed = []
        
        for model_id, source in self.get_all_models():
            # 获取下载器
            downloader = DownloaderFactory.get_downloader(source, model_cache)
            
            # 检查是否已存在
            if downloader.check_model_exists(model_id):
                skipped += 1
                continue
            
            # 下载
            if downloader.download(model_id):
                success += 1
            else:
                failed.append(model_id)
```

### 2. 注册项目

编辑 `project_loader.py`：

```python
from projects.my_project import MyProject

class ProjectLoader:
    PROJECTS = [
        SpeakerDiarizationProject(),
        MyProject(),  # 添加这行
    ]
```

### 3. 在 RunPod 运行

**创建 Pod:**
- GPU: 任意
- Image: `pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime`
- Volume: 挂载到 `/workspace`

**在 Pod Terminal:**

```bash
# 安装依赖
pip install modelscope torch huggingface-hub

# 上传项目文件，运行
python download_models.py --all
```

### 4. 手动模式（可选）

也支持不配置项目，直接下载：

```bash
# 下载单个模型
python download_models.py org/model-name

# 指定源
python download_models.py --source huggingface org/model-name

# 下载多个
python download_models.py model1 model2 model3
```

## 📁 文件说明

| 文件 | 说明 | 是否需要修改 |
|------|------|--------------|
| `base_project.py` | 项目抽象基类 | ❌ 不需要 |
| `model_downloader.py` | 下载器工厂 | ⚠️ 添加新下载源时 |
| `downloaders/` | 下载器模块 | ⚠️ 添加新下载源时 |
| `project_loader.py` | 项目加载器 | ✅ 注册新项目 |
| `projects/*.py` | 各项目配置 | ✅ 添加新项目 |
| `download_models.py` | 下载调度器 | ❌ 不需要 |
| `modelscope_patch.py` | Python 3.10 补丁 | ❌ 不需要 |

## 💡 特性

- ✅ **插件化架构** - 每个项目独立配置
- ✅ **模块化下载器** - 每个下载渠道独立为类，易于扩展
- ✅ **多源支持** - ModelScope、HuggingFace，可自定义添加
- ✅ **智能检测** - 自动跳过已下载的模型
- ✅ **统一管理** - 所有项目模型集中下载
- ✅ **灵活使用** - 支持项目配置或手动指定

## 🔧 高级用法

### 查看项目摘要

```bash
python project_loader.py
```

### 只下载特定项目

修改 `project_loader.py` 临时注释掉不需要的项目。

### 添加自定义下载源

**1. 创建新的下载器类**（`downloaders/custom_downloader.py`）：

```python
from .base_downloader import BaseDownloader

class CustomDownloader(BaseDownloader):
    def is_available(self) -> bool:
        # 检查依赖是否安装
        return True
    
    def download(self, model_id: str) -> bool:
        # 实现下载逻辑
        try:
            # 你的下载代码
            return True
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False
```

**2. 在工厂类注册**（修改 `model_downloader.py`）：

```python
from downloaders.custom_downloader import CustomDownloader

class DownloaderFactory:
    _downloaders = {
        'modelscope': ModelScopeDownloader,
        'huggingface': HuggingFaceDownloader,
        'custom': CustomDownloader,  # 添加这行
    }
```

**3. 在项目中使用**：

```python
@property
def models(self):
    return {
        'modelscope': [...],
        'custom': ['model-id'],  # 使用自定义源
    }
```
