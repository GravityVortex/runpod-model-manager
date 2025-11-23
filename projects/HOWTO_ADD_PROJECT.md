# 如何添加新项目

## 项目结构

每个项目独立一个目录，包含所有相关配置：

```
projects/
├── speaker_diarization/          # 项目目录（使用下划线）
│   ├── __init__.py               # 导出配置类
│   ├── config.py                 # 项目配置
│   └── requirements.txt          # 依赖列表
├── your_project/                 # 你的新项目
│   ├── __init__.py
│   ├── config.py
│   └── requirements.txt
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
    def requirements_file(self):
        """requirements.txt 路径"""
        current_dir = Path(__file__).parent
        return str(current_dir / 'requirements.txt')
    
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

## 步骤 4：创建 requirements.txt

### `projects/your_project/requirements.txt`

```txt
# 你的项目依赖
# Python 3.10

# 基础依赖
transformers==4.35.0
torch==2.1.0

# API 服务（如果需要）
fastapi
uvicorn

# RunPod
runpod

# 其他依赖
# ...
```

**提示**：
- 建议指定版本号（`==`）
- 可以添加注释（`#`）
- 空行会被忽略

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
└── requirements.txt
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
    def requirements_file(self):
        return str(Path(__file__).parent / 'requirements.txt')
    
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

**requirements.txt**：
```txt
# Text Generation 依赖
transformers==4.36.0
torch==2.1.0
accelerate
sentencepiece
fastapi
uvicorn
runpod
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

### Q: requirements.txt 必须在项目目录吗？

**推荐放在项目目录**，但也可以指向其他位置：

```python
@property
def requirements_file(self):
    # 方式 1: 项目目录（推荐）
    return str(Path(__file__).parent / 'requirements.txt')
    
    # 方式 2: 绝对路径
    return '/path/to/your/requirements.txt'
    
    # 方式 3: 相对路径
    return 'path/to/requirements.txt'
```

### Q: 能不定义 requirements.txt 吗？

可以。如果不需要依赖管理，返回 `None`：

```python
@property
def requirements_file(self):
    return None
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

```txt
# ✅ 推荐：指定版本
transformers==4.35.0
torch==2.1.0

# ⚠️  不推荐：不指定版本（可能升级导致不兼容）
transformers
torch

# ✅ 可以：指定范围
transformers>=4.35.0,<5.0.0
```

### 3. 文件组织

```
projects/your_project/
├── __init__.py           # 简单导出
├── config.py             # 核心配置
├── requirements.txt      # 依赖列表
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
- [ ] 创建 `config.py`（配置类）
- [ ] 创建 `__init__.py`（导出类）
- [ ] 创建 `requirements.txt`（依赖列表）
- [ ] 在 `loader.py` 中注册项目
- [ ] 测试配置加载
- [ ] 使用 `volume_cli.py` 测试

---

🎯 **独立目录，清晰管理！**
