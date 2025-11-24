# 如何添加新项目

## 项目结构

每个项目独立一个目录，包含所有相关配置：

```
projects/
├── speaker_diarization/          # 项目目录（使用下划线）
│   ├── __init__.py               # 导出配置类
│   ├── config.py                 # 项目配置
│   └── dependencies.yaml         # 依赖配置（支持多索引源、no-deps 等）
├── your_project/                 # 你的新项目
│   ├── __init__.py
│   ├── config.py
│   └── dependencies.yaml
└── base.py                       # 基类（不要修改）
```

---

## 步骤 1：创建项目目录

```bash
mkdir -p projects/your_project
```

**注意**：目录名必须是合法的 Python 模块名（使用下划线 `_`，不能用连字符 `-`）

---

## 步骤 2：创建配置文件

### `projects/your_project/config.py`

```python
# -*- coding: utf-8 -*-
"""
你的项目配置
"""
from pathlib import Path
from ..base import BaseProject
from downloaders.factory import DownloaderFactory


class YourProject(BaseProject):
    """你的项目"""
    
    @property
    def name(self):
        """项目名称（可以用连字符）"""
        return "your-project"
    
    @property
    def python_version(self):
        """Python 版本"""
        return '3.10'  # 或 '3.11', '3.12' 等
    
    @property
    def dependencies_config(self):
        """dependencies.yaml 路径"""
        current_dir = Path(__file__).parent
        return str(current_dir / 'dependencies.yaml')
    
    @property
    def models(self):
        """模型列表"""
        return {
            'modelscope': [
                'org/model-name',
            ],
            'huggingface': [
                'org/model-name',
            ]
        }
    
    def download_models(self, model_cache: str):
        """下载模型的实现"""
        print(f"\n{'='*60}")
        print(f"📦 项目: {self.name}")
        print(f"{'='*60}")
        
        all_models = self.get_all_models()
        success = 0
        skipped = 0
        failed = []
        
        for i, (model_id, source) in enumerate(all_models, 1):
            print(f"\n[{i}/{len(all_models)}] {model_id} ({source})")
            
            try:
                downloader = DownloaderFactory.get_downloader(source, model_cache)
            except ValueError as e:
                print(f"  ❌ {e}")
                failed.append(model_id)
                continue
            
            if downloader.check_model_exists(model_id):
                print(f"  ⏭️  已存在，跳过")
                skipped += 1
                continue
            
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
```

**提示**：可以直接复制 `speaker_diarization/config.py`，然后修改。

---

## 步骤 3：创建 __init__.py

### `projects/your_project/__init__.py`

```python
from .config import YourProject

__all__ = ['YourProject']
```

---

## 步骤 4：创建 dependencies.yaml

### `projects/your_project/dependencies.yaml`

```yaml
# 依赖配置文件
# 支持从不同索引源安装不同的依赖包

# 依赖组（按安装源分组）
groups:
  # PyTorch 相关包（需要从 PyTorch 官方索引安装）
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
      - torchaudio==2.4.1
    description: "PyTorch with CUDA 12.1 support"
  
  # 标准 PyPI 包（从默认源安装）
  standard:
    index_url: null  # null 表示使用默认 PyPI 源
    packages:
      - transformers==4.46.3
      - fastapi==0.121.0
      - uvicorn==0.33.0
      - runpod
    description: "Standard packages from PyPI"
  
  # 使用 --no-deps 安装的包（避免依赖冲突）
  special:
    index_url: null
    no_deps: true  # 关键配置：跳过依赖检查
    packages:
      - your-special-package==1.0.0
    description: "Packages installed with --no-deps"
    # 注意：使用 no_deps 前，确保该包的所有依赖已在其他组中声明

# 安装顺序（某些包需要先安装）
install_order:
  - pytorch    # 先安装 PyTorch
  - standard   # 再安装其他包
  - special    # 最后安装 no-deps 的包

# 元数据
metadata:
  project: your-project
  python_version: "3.10"
  created: "2024-11-24"
  description: "Your project dependencies"
```

**配置说明**：

1. **groups**: 依赖分组
   - `index_url`: 索引源地址（`null` 表示默认 PyPI）
   - `packages`: 包列表
   - `no_deps`: 是否使用 `--no-deps` 安装（可选）
   - `description`: 组说明（可选）

2. **install_order**: 安装顺序（数组）

3. **metadata**: 元数据（可选）

**no_deps 使用场景**：
- 包的依赖声明有问题（如 `umap` vs `umap-learn`）
- 需要精确控制依赖版本
- 避免自动安装不需要的依赖

⚠️ **使用 no_deps 的注意事项**：
- 必须在其他组中显式声明该包的所有依赖
- 参考该包的官方文档或 `setup.py` 确认依赖列表
- 示例：`speaker_diarization/dependencies.yaml` 中的 `funasr` 配置

---

## 步骤 5：注册项目

### `projects/loader.py`

```python
# 导入各项目配置
from .speaker_diarization import SpeakerDiarizationProject
from .your_project import YourProject  # 添加导入

class ProjectLoader:
    """项目加载器"""
    
    PROJECTS = [
        SpeakerDiarizationProject(),
        YourProject(),  # 注册你的项目
    ]
```

---

## 步骤 6：测试

```bash
# 测试配置加载
python3 -c "
from projects.loader import get_project
project = get_project('your-project')
print(f'Project: {project.name}')
print(f'Dependencies: {len(project.dependencies)}')"

# 查看项目列表
python3 -m projects.loader
```

---

## 步骤 7：使用

```bash
# 一键设置
python3 volume_cli.py setup --project your-project

# 或分步：
python3 volume_cli.py deps install --project your-project
python3 volume_cli.py models download --project your-project
```

---

## 完整示例

### 示例：Text Generation 项目

**目录结构**：
```
projects/text_generation/
├── __init__.py
├── config.py
└── dependencies.yaml
```

**config.py**：
```python
from pathlib import Path
from ..base import BaseProject
from downloaders.factory import DownloaderFactory


class TextGenerationProject(BaseProject):
    @property
    def name(self):
        return "text-generation"
    
    @property
    def python_version(self):
        return '3.11'
    
    @property
    def dependencies_config(self):
        return str(Path(__file__).parent / 'dependencies.yaml')
    
    @property
    def models(self):
        return {
            'huggingface': [
                'meta-llama/Llama-2-7b-hf',
                'sentence-transformers/all-MiniLM-L6-v2',
            ]
        }
    
    def download_models(self, model_cache: str):
        # 同 speaker_diarization 的实现
        ...
```

**dependencies.yaml**：
```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.1.0
  
  standard:
    index_url: null
    packages:
      - transformers==4.36.0
      - accelerate
      - sentencepiece
      - fastapi
      - uvicorn
      - runpod

install_order:
  - pytorch
  - standard

metadata:
  project: text-generation
  python_version: "3.11"
```

**__init__.py**：
```python
from .config import TextGenerationProject
__all__ = ['TextGenerationProject']
```

**注册** (`loader.py`)：
```python
from .text_generation import TextGenerationProject

class ProjectLoader:
    PROJECTS = [
        SpeakerDiarizationProject(),
        TextGenerationProject(),
    ]
```

---

## 常见问题

### Q: 目录名能用连字符吗？

**不能**。Python 模块名不能有连字符。

```bash
# ❌ 错误
mkdir projects/text-generation

# ✅ 正确
mkdir projects/text_generation
```

但项目名称（`name` 属性）可以用连字符：
```python
@property
def name(self):
    return "text-generation"  # ✅ 可以
```

### Q: dependencies.yaml 必须在项目目录吗？

**推荐放在项目目录**，但也可以指向其他位置：

```python
@property
def dependencies_config(self):
    # 方式 1: 项目目录（推荐）
    return str(Path(__file__).parent / 'dependencies.yaml')
    
    # 方式 2: 绝对路径
    return '/path/to/your/dependencies.yaml'
    
    # 方式 3: 相对路径
    return 'path/to/dependencies.yaml'
```

### Q: 能不定义 dependencies.yaml 吗？

可以。如果不需要依赖管理，返回 `None`：

```python
@property
def dependencies_config(self):
    return None
```

### Q: 什么时候应该使用 no_deps？

**使用场景**：
1. 包的依赖声明有问题（如 `funasr` 声明依赖 `umap`，但实际需要 `umap-learn`）
2. 需要精确控制依赖版本，避免自动安装
3. 包的某些依赖在特定环境不需要

**示例**：
```yaml
groups:
  # 先安装所有真实依赖
  standard:
    index_url: null
    packages:
      - umap-learn==0.5.7  # 真实需要的包
      - numpy==1.23.5
      - scipy==1.10.1
  
  # 再用 no_deps 安装有问题的包
  special:
    index_url: null
    no_deps: true
    packages:
      - funasr==0.8.8  # 跳过其依赖检查

install_order:
  - standard
  - special
```

### Q: download_models 必须这样写吗？

**这是推荐的实现**。你可以自定义，但建议保持一致的统计输出格式。

---

## 最佳实践

### 1. 目录命名

```
✅ speaker_diarization
✅ text_generation
✅ my_awesome_project

❌ speaker-diarization
❌ text-generation
❌ my-project
```

### 2. 版本管理

```yaml
# ✅ 推荐：指定精确版本
groups:
  standard:
    packages:
      - transformers==4.35.0
      - torch==2.1.0

# ⚠️ 不推荐：不指定版本（可能升级导致不兼容）
groups:
  standard:
    packages:
      - transformers  # 版本不确定，可能导致问题
      - torch

# ✅ 可以：指定版本范围
groups:
  standard:
    packages:
      - transformers>=4.35.0,<5.0.0
```

### 3. 文件组织

```
projects/your_project/
├── __init__.py           # 简单导出
├── config.py             # 核心配置
├── dependencies.yaml     # 依赖配置（支持多索引源、no-deps）
└── README.md             # 项目说明（可选）
```

### 4. 复用代码

直接复制 `speaker_diarization/` 作为模板：

```bash
cp -r projects/speaker_diarization projects/your_project
# 然后修改文件内容
```

---

## 清单

完成以下步骤：

- [ ] 创建项目目录 `projects/your_project/`
- [ ] 创建 `config.py`（配置类，定义 `dependencies_config` 属性）
- [ ] 创建 `__init__.py`（导出类）
- [ ] 创建 `dependencies.yaml`（依赖配置，支持多索引源和 no_deps）
- [ ] 在 `loader.py` 中注册项目
- [ ] 测试配置加载
- [ ] 使用 `volume_cli.py` 测试

---

🎯 **独立目录，清晰管理！**
