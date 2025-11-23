# RunPod Model Manager

**统一管理 RunPod Volume 中的模型和依赖**

在 RunPod Network Volume 中管理多个项目的 Python 依赖和 AI 模型，支持增量更新、版本隔离。

## 特性

- ✅ **统一 CLI**：单一入口管理所有操作
- ✅ **增量更新**：只安装/下载新增的内容
- ✅ **版本隔离**：按 Python 版本隔离依赖
- ✅ **自动安装**：自动检测版本并安装需要的 Python
- ✅ **独立项目**：每个项目一个目录，清晰管理
- ✅ **多源支持**：ModelScope、HuggingFace 等

## 目录结构

```
runpod-model-manager/
├── volume_cli.py            # 统一 CLI 入口
├── volume_manager.py        # Volume 增量管理
├── dependency_installer.py  # 通用依赖安装器
├── modelscope_patch.py      # ModelScope 兼容性补丁
├── requirements.txt         # 管理工具依赖（modelscope、huggingface-hub）
├── commands/                # CLI 命令模块
├── downloaders/             # 下载器模块
└── projects/                # 项目配置
    ├── speaker_diarization/ # 示例项目
    │   ├── config.py
    │   └── dependencies.yaml # 项目依赖配置（多索引源）
    └── your_project/        # 添加更多项目
```

**依赖说明**：
- 📦 **根目录 `requirements.txt`**：运行 `volume_cli.py` 需要的依赖（modelscope、huggingface-hub）
- 📦 **项目目录 `dependencies.yaml`**：项目依赖配置，支持多索引源（torch、transformers 等）

## 🚀 快速开始

### 统一 CLI 工具（推荐⭐）

使用统一的 CLI 工具管理依赖和模型：

```bash
# === 在临时 Pod 的 Web Terminal 中 ===

# 1. Clone 项目
cd /workspace
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 2. ⚠️ 重要：先安装管理工具依赖
# CLI 工具需要 pyyaml、modelscope、huggingface-hub 等依赖
pip install -r requirements.txt

# 💡 提示：当系统自动切换 Python 版本时，会自动安装这些依赖到新版本

# 3. 一键设置项目（依赖+模型）
python3 volume_cli.py setup --project speaker-diarization

# 或分步执行：

# 安装依赖
python3 volume_cli.py deps install --project speaker-diarization

# 下载模型
python3 volume_cli.py models download --project speaker-diarization

# 查看状态
python3 volume_cli.py status --project speaker-diarization
```

**CLI 命令参考**：

| 命令 | 说明 |
|------|------|
| `setup` | 一键设置（依赖+模型） |
| `status` | 查看 Volume 状态 |
| `deps install` | 安装依赖（增量） |
| `deps check` | 检查依赖完整性 |
| `models download` | 下载模型（增量） |
| `models verify` | 验证模型完整性 |
| `clean` | 清理项目数据 |

---

## 使用流程

### 1. 在临时 Pod 中设置

```bash
# 创建临时 Pod，挂载 Volume 到 /workspace

cd /workspace
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 一键设置项目
python3 volume_cli.py setup --project speaker-diarization

# 完成后删除 Pod
```

### 2. 在项目中使用

```dockerfile
# Dockerfile.serverless
ENV PYTHONPATH=/runpod-volume/python-deps/py3.10/speaker-diarization:$PYTHONPATH \
    MODELSCOPE_CACHE=/runpod-volume/models
```

---

## 添加项目

### 1. 添加你的项目配置

**每个项目独立一个目录**：

```bash
# 创建项目目录
mkdir -p projects/my_project
```

**创建配置文件** (`projects/my_project/config.py`)：

```python
from pathlib import Path
from ..base import BaseProject

class MyProject(BaseProject):
    @property
    def name(self):
        return "my-project"
    
    @property
    def python_version(self):
        return '3.10'
    
    @property
    def dependencies_config(self):
        """依赖配置文件"""
        return str(Path(__file__).parent / 'dependencies.yaml')
    
    @property
    def models(self):
        return {
            'modelscope': ['org/model-1'],
            'huggingface': ['org/model-2'],
        }
    
    def download_models(self, model_cache: str):
        # 复制 speaker_diarization 的实现即可
        ...
```

**创建依赖配置** (`projects/my_project/dependencies.yaml`)：

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.1.0
  
  standard:
    index_url: null
    packages:
      - transformers==4.35.0
      - fastapi
      - runpod

install_order:
  - pytorch
  - standard

metadata:
  project: my-project
  python_version: "3.10"
```

**创建导出文件** (`projects/my_project/__init__.py`)：

```python
from .config import MyProject
__all__ = ['MyProject']
```

> 📖 **详细添加指南**：[projects/HOWTO_ADD_PROJECT.md](./projects/HOWTO_ADD_PROJECT.md)

### 2. 注册项目

编辑 `projects/loader.py`：

```python
from .my_project import MyProject

PROJECTS = [
    SpeakerDiarizationProject(),
    MyProject(),
]
```

---

## 📖 文档

- **[COMPLETE_GUIDE.md](./COMPLETE_GUIDE.md)** - 完整操作指南（详细 RunPod 步骤）⭐
- [MODELSCOPE_AST_FIX.md](./MODELSCOPE_AST_FIX.md) - ModelScope 兼容性技术文档
- [projects/HOWTO_ADD_PROJECT.md](./projects/HOWTO_ADD_PROJECT.md) - 添加项目详细指南

---

## 🔗 关联业务项目

本工具负责依赖和模型管理，具体业务实现在独立项目中：

- **说话人分割项目**: [GravityVortex/zhesheng-model-speaker-reg](https://github.com/GravityVortex/zhesheng-model-speaker-reg)
  - 业务代码（api.py, mydemo.py）
  - Serverless 部署配置（Dockerfile.serverless）
  - 完整部署文档（RUNPOD_DEPLOY.md）

---

## Volume 结构

```
/runpod-volume/ 或 /workspace/
├── .metadata/                    # 元数据（增量追踪）
├── python-deps/                  # Python 依赖（按版本隔离）
│   ├── py3.10/
│   │   └── speaker-diarization/
│   └── py3.11/
│       └── text-generation/
└── models/                       # 模型（所有项目共享）
    └── hub/
```
