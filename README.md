# RunPod Model Manager

**统一管理 RunPod Volume 中的模型和依赖**

在 RunPod Volume（Pod `/workspace` 或 Serverless `/runpod-volume`）中管理多个项目的 Python 依赖和 AI 模型，支持增量更新与按 Python 版本隔离依赖目录。

## 特性

- ✅ **统一 CLI**：单一入口管理依赖与模型
- ✅ **增量更新**：依赖按配置变更增量/全量更新；模型按已存在文件跳过
- ✅ **版本隔离**：依赖安装到 `venvs/pyX.Y-<project>/`
- ✅ **自动处理 Python 版本**：`deps install` 会检测当前解释器版本，不匹配时自动切换/尝试安装（需要 root 且依赖 apt）
- ✅ **独立项目**：每个项目一个 venv，清晰管理
- ✅ **多源支持**：ModelScope、HuggingFace
- ✅ **高速安装**：使用 uv 工具，速度比 pip 快 10-100 倍

## 目录结构（仓库）

```
runpod-model-manager/
├── volume_cli.py                 # 统一 CLI 入口
├── requirements.txt              # CLI 自身依赖（pyyaml/modelscope/huggingface-hub）
├── src/
│   ├── commands/                 # CLI 子命令实现
│   ├── downloaders/              # ModelScope/HF 下载器
│   ├── projects/                 # 项目配置
│   │   └── speaker_diarization/  # 示例项目
│   │       ├── config.py
│   │       └── dependencies.yaml # 项目依赖配置（支持多索引源/no-deps）
│   ├── dependency_installer.py   # YAML 依赖安装器（多索引源）
│   └── volume_manager.py         # 增量管理与元数据
├── MODEL_DEPLOYMENT_GUIDE.md
└── S3_UPLOAD_GUIDE.md
```

## Volume 目录结构（实际落盘）

CLI 会自动检测可写的 Volume 挂载点（按顺序尝试）：

- `/workspace`（RunPod Pod 常见）
- `/runpod-volume`（RunPod Serverless 常见）
- `RUNPOD_VOLUME_PATH`（你自己指定）

落盘结构如下（相对于 Volume 根目录）：

```
<VOLUME>/
├── venvs/                            # 虚拟环境（使用 uv + venv）
│   └── py3.10-speaker-diarization/   # 每个项目一个 venv
│       ├── bin/python                # Python 解释器
│       └── lib/python3.10/site-packages/  # 依赖包
├── models/                           # 模型缓存目录（ModelScope/HF 都指向这里）
└── .metadata/                        # 增量更新用的元数据（json）
```

## 🚀 快速开始

在带 Volume 的临时 Pod（或任意能写入 Volume 的环境）执行：

```bash
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 安装 uv（新一代包管理工具，速度快 10-100 倍）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或使用 pip: pip install uv

# 安装 CLI 自身依赖
python3 -m pip install -r requirements.txt

# 一键：安装依赖 + 下载模型
python3 volume_cli.py setup --project speaker-diarization
```

如果 Volume 不在默认路径，可显式指定：

```bash
export RUNPOD_VOLUME_PATH=/runpod-volume
python3 volume_cli.py status
```

## CLI 命令参考

| 命令              | 说明                  |
| ----------------- | --------------------- |
| `setup`           | 一键设置（依赖+模型） |
| `status`          | 查看 Volume 状态      |
| `deps install`    | 安装依赖（增量）      |
| `deps list`       | 列出依赖配置          |
| `deps check`      | 检查依赖完整性        |
| `models download` | 下载模型（增量）      |
| `models list`     | 列出模型清单          |
| `models verify`   | 验证模型完整性        |
| `clean`           | 清理项目数据          |

常用参数（与代码一致）：

- `deps install --mirror <url>`：仅对 `dependencies.yaml` 中 `index_url: null` 的组生效（其他组走各自 `index_url`）
- `deps install --force`：跳过变更检测，强制重装
- `models download --force`：强制重新下载
- `setup --skip-deps` / `setup --skip-models`：跳过某一步
- `clean --deps/--models/--all`：必须指定清理范围，且需要输入 `yes` 确认

## 使用流程（推荐）

### 1) 在临时 Pod 中预热 Volume

```bash
python3 volume_cli.py setup --project speaker-diarization
```

### 2) 在业务镜像/Serverless 中使用落盘内容

依赖安装在 venv 中，业务镜像侧通过激活 venv 或直接使用 venv 的 python：

```dockerfile
# 方式 1: 激活 venv（推荐）
ENV VIRTUAL_ENV=/runpod-volume/venvs/py3.10-speaker-diarization
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV MODELSCOPE_CACHE=/runpod-volume/models

# 方式 2: 直接用 venv 的 python
CMD ["/runpod-volume/venvs/py3.10-speaker-diarization/bin/python", "app.py"]
```

模型下载时显式使用 `<VOLUME>/models` 作为 `cache_dir`；运行时也建议把相关缓存变量指向同一路径（至少 `MODELSCOPE_CACHE`）。

## 添加项目

### 1) 添加项目配置

**每个项目独立一个目录**：

```bash
mkdir -p src/projects/my_project
```

**创建配置文件**（必须继承 `src/projects/base.py:BaseProject`）：

```python
from pathlib import Path
from ..base import BaseProject

class MyProject(BaseProject):
    @property
    def name(self):
        return "my-project"

    @property
    def models(self):
        return {
            'modelscope': ['org/model-1'],
            'huggingface': ['org/model-2'],
        }

    @property
    def python_version(self):
        return '3.10'

    @property
    def dependencies_config(self):
        """依赖配置文件"""
        return str(Path(__file__).parent / 'dependencies.yaml')

    def download_models(self, model_cache: str):
        # 可直接复制 src/projects/speaker_diarization/config.py 的下载逻辑
        raise NotImplementedError
```

**创建依赖配置**（`dependencies.yaml` 支持多索引源、`no_deps` 等）：

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

**创建导出文件**（`src/projects/my_project/__init__.py`）：

```python
from .config import MyProject
__all__ = ['MyProject']
```

### 2) 注册项目

编辑 `src/projects/loader.py`，导入并加入 `ProjectLoader.PROJECTS`：

```python
from .speaker_diarization import SpeakerDiarizationProject
from .my_project import MyProject

class ProjectLoader:
    PROJECTS = [
        SpeakerDiarizationProject(),
        MyProject(),
    ]
```

## 📖 文档与说明

- `MODEL_DEPLOYMENT_GUIDE.md`：两种模型落盘方式对比（S3 上传 vs 在线下载）与完整流程
- `S3_UPLOAD_GUIDE.md`：S3 上传工具（`src/s3_uploader.py`）使用说明（需要额外安装 `boto3`）

## 注意事项（按代码行为）

- `deps install` 会要求当前解释器版本等于项目的 `python_version`；不匹配时会优先尝试调用 `pythonX.Y` 重新执行，否则尝试 `apt-get install pythonX.Y-*`（需要 root 且依赖系统源）。
- 依赖使用 uv 安装到独立的 venv 中，业务侧通过激活 venv 或直接使用 venv 的 python 运行。
- 模型默认下载到 `<VOLUME>/models/`，目录结构由上游库决定（ModelScope 通常在 `models/hub/<model_id>`，HuggingFace 通常在 `models/models--org--repo`）。
- `clean --models` 不会删除真实模型文件（模型可能被多个项目共享），只清理元数据记录；删除真实模型请自行处理 `models/` 目录。

## Volume 结构

```
/runpod-volume/ 或 /workspace/
├── .metadata/                    # 元数据（增量追踪）
├── venvs/                        # 虚拟环境（按 Python 版本 + 项目隔离）
│   ├── py3.10-speaker-diarization/
│   │   ├── bin/python
│   │   └── lib/python3.10/site-packages/
│   └── py3.11-text-generation/
│       ├── bin/python
│       └── lib/python3.11/site-packages/
└── models/                       # 模型（所有项目共享）
    └── hub/
```
