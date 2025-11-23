# 项目结构说明

## 目录组织

```
runpod-model-manager/
├── volume_cli.py                # 🎯 统一 CLI 入口
├── volume_manager.py            # Volume 增量管理器
├── install_dependencies.py      # 依赖安装（旧接口）
├── download_models.py           # 模型下载（旧接口）
│
├── commands/                    # CLI 命令模块
│   ├── status.py               # 状态查看
│   ├── dependencies.py         # 依赖管理
│   ├── models.py               # 模型管理
│   ├── setup.py                # 一键设置
│   └── clean.py                # 清理
│
├── downloaders/                 # 下载器模块
│   ├── base_downloader.py      # 下载器基类
│   ├── factory.py              # 下载器工厂
│   ├── modelscope_downloader.py
│   └── huggingface_downloader.py
│
└── projects/                    # 项目配置
    ├── base.py                 # 项目基类
    ├── loader.py               # 项目加载器
    ├── HOWTO_ADD_PROJECT.md    # 添加项目指南
    │
    ├── speaker_diarization/    # 项目1（独立目录）
    │   ├── __init__.py         # 导出配置类
    │   ├── config.py           # 项目配置
    │   └── requirements.txt    # 依赖列表
    │
    └── your_project/            # 项目2（添加更多）
        ├── __init__.py
        ├── config.py
        └── requirements.txt
```

---

## 核心概念

### 1. 独立项目目录

每个项目独立一个目录，包含所有相关配置：

```
projects/speaker_diarization/
├── __init__.py           # 导出配置类
├── config.py             # 项目配置（模型、依赖、Python 版本）
└── requirements.txt      # 依赖列表（标准格式）
```

**优势**：
- ✅ 清晰隔离
- ✅ 易于管理
- ✅ 便于版本控制
- ✅ 可独立复制/分享

### 2. 统一 CLI

所有操作通过 `volume_cli.py` 统一入口：

```bash
# 状态查看
python3 volume_cli.py status

# 依赖管理
python3 volume_cli.py deps install --project <name>

# 模型管理
python3 volume_cli.py models download --project <name>

# 一键设置
python3 volume_cli.py setup --project <name>
```

### 3. 增量更新

通过 `volume_manager.py` 实现：
- 元数据追踪（`.metadata/项目名.json`）
- 智能检测变化（新增/移除）
- 只安装新增的依赖
- 只下载新增的模型

### 4. Python 版本隔离

依赖按 Python 版本分目录：

```
/runpod-volume/
└── python-deps/
    ├── py3.10/
    │   ├── speaker-diarization/
    │   └── project-a/
    └── py3.11/
        ├── text-generation/
        └── project-b/
```

---

## 添加新项目

### 快速步骤

```bash
# 1. 创建目录
mkdir -p projects/my_project

# 2. 复制模板
cp -r projects/speaker_diarization/* projects/my_project/

# 3. 修改配置
# 编辑 projects/my_project/config.py
# 编辑 projects/my_project/requirements.txt

# 4. 注册项目
# 编辑 projects/loader.py，添加导入和注册

# 5. 测试
python3 -m projects.loader
```

详细步骤：[projects/HOWTO_ADD_PROJECT.md](./projects/HOWTO_ADD_PROJECT.md)

---

## 工作流

### 初次设置

```bash
# 在临时 Pod 中
cd /workspace
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 一键设置项目
python3 volume_cli.py setup --project speaker-diarization
```

### 增量更新

```bash
# 在临时 Pod 中
cd /workspace/runpod-model-manager
git pull

# 增量更新（只装新增的）
python3 volume_cli.py deps install --project speaker-diarization
python3 volume_cli.py models download --project speaker-diarization
```

### 查看状态

```bash
# 查看所有项目
python3 volume_cli.py status

# 查看特定项目
python3 volume_cli.py status --project speaker-diarization
```

---

## 文件说明

### 核心文件

| 文件 | 用途 | 是否修改 |
|------|------|---------|
| `volume_cli.py` | 统一 CLI 入口 | ❌ |
| `volume_manager.py` | 增量管理器 | ❌ |
| `projects/base.py` | 项目基类 | ❌ |
| `projects/loader.py` | 项目加载器 | ✅ 注册新项目 |
| `projects/*/config.py` | 项目配置 | ✅ 添加项目 |
| `projects/*/requirements.txt` | 依赖列表 | ✅ 添加项目 |

### 文档文件

| 文件 | 说明 |
|------|------|
| `README.md` | 项目总览 |
| `CLI_GUIDE.md` | CLI 使用指南 |
| `VOLUME_SETUP_GUIDE.md` | Volume 设置指南 |
| `PRODUCTION_GUIDE.md` | 生产环境指南 |
| `projects/HOWTO_ADD_PROJECT.md` | 添加项目指南 |
| `PROJECT_STRUCTURE.md` | 本文档 |

---

## 命名规范

### 目录名

**必须是合法的 Python 模块名**（使用下划线）：

```bash
✅ speaker_diarization
✅ text_generation
✅ my_awesome_project

❌ speaker-diarization  # 不能用连字符
❌ text-generation
❌ my-project
```

### 项目名称

**可以使用连字符**（在 `config.py` 的 `name` 属性中）：

```python
@property
def name(self):
    return "speaker-diarization"  # ✅ 可以用连字符
```

### 文件名

```
✅ config.py           # 配置文件
✅ requirements.txt    # 依赖列表
✅ __init__.py         # 导出文件
❌ setup.py            # 避免与 Python 标准名冲突
```

---

## 最佳实践

### 1. 目录组织

```
projects/your_project/
├── __init__.py           # 简单导出
├── config.py             # 核心配置
├── requirements.txt      # 依赖列表
└── README.md             # 项目说明（可选）
```

### 2. 版本控制

```txt
# requirements.txt
transformers==4.35.0  # ✅ 明确版本
torch==2.1.0          # ✅ 明确版本

transformers          # ❌ 不推荐
```

### 3. 代码复用

直接复制 `speaker_diarization` 作为模板：

```bash
cp -r projects/speaker_diarization projects/your_project
# 然后修改文件内容
```

### 4. 测试验证

```bash
# 测试配置加载
python3 -c "
from projects.loader import get_project
project = get_project('your-project')
print(f'Project: {project.name}')
print(f'Dependencies: {len(project.dependencies)}')"

# 查看所有项目
python3 -m projects.loader
```

---

## Volume 结构

### 完整 Volume 布局

```
/runpod-volume/  或  /workspace/
├── .metadata/                    # 元数据（增量追踪）
│   ├── speaker-diarization.json
│   └── text-generation.json
│
├── python-deps/                  # Python 依赖
│   ├── py3.10/                   # Python 3.10
│   │   ├── speaker-diarization/
│   │   └── audio-processing/
│   └── py3.11/                   # Python 3.11
│       ├── text-generation/
│       └── image-classification/
│
└── models/                       # 模型（所有项目共享）
    └── hub/
        ├── iic/
        ├── damo/
        └── meta-llama/
```

### 元数据格式

```json
{
  "project": "speaker-diarization",
  "dependencies": {
    "modelscope": {
      "installed_at": "2025-11-23T11:00:00"
    }
  },
  "models": {
    "iic/model": {
      "source": "modelscope",
      "installed_at": "2025-11-23T11:00:00"
    }
  },
  "last_updated": "2025-11-23T11:00:00"
}
```

---

## 扩展

### 添加新下载源

1. 在 `downloaders/` 创建新下载器
2. 继承 `BaseDownloader`
3. 在 `factory.py` 注册
4. 在项目配置中使用

### 自定义命令

1. 在 `commands/` 创建新命令
2. 在 `volume_cli.py` 注册
3. 实现命令逻辑

---

## 故障排除

### 导入错误

```
ModuleNotFoundError: No module named 'projects.my-project'
```

**原因**：目录名使用了连字符  
**解决**：使用下划线 `my_project`

### 依赖未找到

```
⚠️  requirements.txt 未找到: ...
```

**原因**：路径不正确  
**解决**：检查 `requirements_file` 返回的路径

### 模型下载失败

**检查**：
```bash
python3 volume_cli.py models verify --project <name>
```

---

## 相关文档

- [README.md](./README.md) - 项目总览
- [CLI_GUIDE.md](./CLI_GUIDE.md) - CLI 完整指南
- [VOLUME_SETUP_GUIDE.md](./VOLUME_SETUP_GUIDE.md) - Volume 设置
- [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md) - 生产环境
- [projects/HOWTO_ADD_PROJECT.md](./projects/HOWTO_ADD_PROJECT.md) - 添加项目

---

🎯 **清晰独立，易于扩展！**
