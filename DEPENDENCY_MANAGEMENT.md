# 通用依赖管理系统

## 概述

RunPod Model Manager 提供了一个配置化的依赖管理系统，支持从不同的索引源（如 PyTorch 官方索引、私有 PyPI 镜像等）安装不同的依赖包。

## 特性

- ✅ **多索引源支持**：不同包可以从不同的索引源安装
- ✅ **分组管理**：按功能或来源对依赖进行分组
- ✅ **安装顺序控制**：控制依赖组的安装顺序
- ✅ **配置化**：统一使用 YAML 文件管理所有依赖
- ✅ **清晰明确**：每个项目必须定义 dependencies.yaml

## 配置文件格式

### dependencies.yaml 结构

```yaml
# 依赖配置文件
groups:
  # 依赖组名称
  group_name:
    # 索引 URL (null 表示使用默认 PyPI)
    index_url: "https://download.pytorch.org/whl/cu121"
    # 包列表
    packages:
      - package1==1.0.0
      - package2>=2.0.0
    # 描述（可选）
    description: "Group description"
  
  another_group:
    index_url: null  # 使用默认 PyPI
    packages:
      - package3
      - package4

# 安装顺序（某些包需要先安装）
install_order:
  - group_name
  - another_group

# 元数据（可选）
metadata:
  project: project-name
  python_version: "3.10"
  description: "Project description"
```

## 使用示例

### 示例 1：PyTorch with CUDA

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
      - torchaudio==2.4.1
    description: "PyTorch with CUDA 12.1"
  
  standard:
    index_url: null
    packages:
      - numpy==1.23.5
      - pandas==2.0.3
    description: "Standard packages"

install_order:
  - pytorch
  - standard
```

### 示例 2：私有 PyPI 镜像

```yaml
groups:
  private_packages:
    index_url: "https://pypi.company.com/simple"
    packages:
      - internal-package==1.0.0
    description: "Company internal packages"
  
  public_packages:
    index_url: null
    packages:
      - requests==2.31.0
    description: "Public packages"

install_order:
  - public_packages
  - private_packages
```

### 示例 3：多个 CUDA 版本

```yaml
groups:
  pytorch_cu121:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
    description: "PyTorch CUDA 12.1"

install_order:
  - pytorch_cu121
```

## 项目配置

### 在项目中启用配置化依赖

编辑项目配置文件 `projects/your_project/config.py`:

```python
from pathlib import Path
from ..base import BaseProject

class YourProject(BaseProject):
    @property
    def name(self):
        return "your-project"
    
    @property
    def dependencies_config(self):
        """依赖配置文件路径"""
        current_dir = Path(__file__).parent
        return str(current_dir / 'dependencies.yaml')
    
    @property
    def models(self):
        return {
            'modelscope': ['org/model-1'],
            'huggingface': ['org/model-2'],
        }
    
    def download_models(self, model_cache: str):
        # 实现模型下载逻辑
        pass
```

## 安装依赖

### 方式 1：使用 CLI（推荐）

```bash
# 安装依赖（自动检测配置文件）
python volume_cli.py deps install --project speaker-diarization

# 使用镜像源（仅用于未指定 index_url 的组）
python volume_cli.py deps install --project speaker-diarization --mirror https://pypi.tuna.tsinghua.edu.cn/simple
```

### 方式 2：直接使用安装器

```bash
# 使用 dependency_installer.py
python dependency_installer.py projects/speaker_diarization/dependencies.yaml -t /target/dir

# 使用镜像源
python dependency_installer.py projects/speaker_diarization/dependencies.yaml -t /target/dir -m https://pypi.tuna.tsinghua.edu.cn/simple

# 干运行（只打印命令）
python dependency_installer.py projects/speaker_diarization/dependencies.yaml --dry-run
```

### 方式 3：生成 requirements.txt

```bash
# 从 dependencies.yaml 生成 requirements.txt
python dependency_installer.py projects/speaker_diarization/dependencies.yaml --generate-requirements requirements.txt
```

## 工作原理

### 安装流程

1. **读取配置**：从 `dependencies.yaml` 读取依赖配置
2. **按组安装**：根据 `install_order` 按顺序安装每个组
3. **自动选择索引**：
   - 如果组指定了 `index_url`，使用 `--index-url` 参数
   - 如果组的 `index_url` 为 null，使用默认 PyPI 或指定的镜像源
4. **记录元数据**：安装成功后更新项目元数据

### 命令生成示例

对于以下配置：

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
```

生成的命令：

```bash
pip install torch==2.4.1 -t /target/dir --index-url https://download.pytorch.org/whl/cu121
```

## 最佳实践

### 1. 按来源分组

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages: [torch, torchaudio]
  
  ml_packages:
    index_url: null
    packages: [transformers, datasets]
```

### 2. 控制安装顺序

某些包依赖其他包，确保先安装基础包：

```yaml
install_order:
  - base_packages    # numpy, scipy 等
  - pytorch          # 依赖 numpy
  - ml_packages      # 依赖 PyTorch
```

### 3. 添加描述信息

```yaml
groups:
  pytorch:
    description: "PyTorch with CUDA 12.1 for RTX 4090"
    index_url: "https://download.pytorch.org/whl/cu121"
    packages: [torch==2.4.1]
```

### 4. 版本锁定

使用确切版本避免意外更新：

```yaml
packages:
  - torch==2.4.1      # 好：确切版本
  - numpy>=1.20.0     # 可以：最小版本
  - pandas            # 避免：无版本约束
```

## 故障排除

### 问题 1：index_url 不被识别

**错误**：`no such option: --index-url`

**原因**：某些环境不支持 `--index-url` 参数

**解决方案**：使用配置化安装（本系统已解决）

### 问题 2：包冲突

**现象**：不同组安装的包版本冲突

**解决方案**：调整 `install_order`，确保兼容版本

### 问题 3：私有索引认证

**场景**：需要认证的私有 PyPI

**解决方案**：在 URL 中包含认证信息或使用环境变量

```yaml
index_url: "https://user:token@pypi.company.com/simple"
```

## 创建新项目

### 步骤

1. **创建 dependencies.yaml**：

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
      - torchaudio==2.4.1
  
  standard:
    index_url: null
    packages:
      - numpy==1.23.5
      - transformers==4.46.3

install_order:
  - pytorch
  - standard

metadata:
  project: your-project
  python_version: "3.10"
```

2. **创建项目配置** (`projects/your_project/config.py`):

```python
from pathlib import Path
from ..base import BaseProject

class YourProject(BaseProject):
    @property
    def name(self):
        return "your-project"
    
    @property
    def dependencies_config(self):
        current_dir = Path(__file__).parent
        return str(current_dir / 'dependencies.yaml')
    
    @property
    def models(self):
        return {
            'modelscope': ['org/model-name'],
        }
    
    def download_models(self, model_cache: str):
        # 实现模型下载逻辑
        pass
```

3. **注册项目** (编辑 `projects/loader.py`):

```python
from .your_project import YourProject

PROJECTS = [
    YourProject(),
    # 其他项目...
]
```

4. **测试安装**：

```bash
python volume_cli.py deps install --project your-project
```

## 参考

- [BaseProject API](./projects/base.py)
- [DependencyInstaller API](./dependency_installer.py)
- [CLI 使用指南](./CLI_GUIDE.md)
