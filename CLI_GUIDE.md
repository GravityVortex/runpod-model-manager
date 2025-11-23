# Volume CLI 使用指南

统一的命令行工具，管理 RunPod Volume 中的依赖和模型。

---

## 设计架构

```
volume_cli.py (统一入口)
├── commands/
│   ├── status.py         # 状态查看
│   ├── dependencies.py   # 依赖管理
│   ├── models.py         # 模型管理
│   ├── setup.py          # 一键设置
│   ├── clean.py          # 清理
│   └── utils.py          # 共用工具
├── projects/             # 项目配置
├── downloaders/          # 下载器
└── volume_manager.py     # Volume 管理器（增量逻辑）
```

---

## 基础命令

### 查看帮助

```bash
python3 volume_cli.py --help
python3 volume_cli.py deps --help
python3 volume_cli.py models --help
```

### 查看状态

```bash
# 查看所有项目
python3 volume_cli.py status

# 查看特定项目
python3 volume_cli.py status --project speaker-diarization
```

**输出示例**：
```
============================================================
📊 RunPod Volume 状态
============================================================
📂 Volume 路径: /workspace

已安装项目: 2

📦 speaker-diarization
   依赖: 13 个 (800M)
   模型: 4 个
   更新: 2025-11-23T11:00:00

📦 text-generation
   依赖: 8 个 (500M)
   模型: 2 个
   更新: 2025-11-23T10:30:00
```

---

## 依赖管理（deps）

### 安装依赖（增量）

```bash
# 增量安装（只装新增的）
python3 volume_cli.py deps install --project speaker-diarization

# 使用国内镜像
python3 volume_cli.py deps install --project speaker-diarization \
    --mirror https://mirrors.aliyun.com/pypi/simple/

# 强制重新安装所有依赖
python3 volume_cli.py deps install --project speaker-diarization --force
```

**增量安装示例**：
```
============================================================
🔧 依赖管理（增量）
============================================================

📦 项目: speaker-diarization
📂 Volume: /workspace
🐍 Python: 3.10
📊 定义依赖数: 15

🔍 检测到依赖变化:
  ➕ 新增: 2
     - fastapi-cors
     - pydantic

✅ 安装完成！
📊 统计:
  总计: 15
  安装: 2
  跳过: 13

💾 占用空间: 850M
```

### 列出依赖

```bash
python3 volume_cli.py deps list --project speaker-diarization
```

**输出**：
```
============================================================
📦 项目: speaker-diarization
============================================================
🐍 Python 版本: 3.10
📊 依赖数量: 13

 1. modelscope
 2. funasr
 3. transformers
 4. torch
 ...
```

### 检查依赖完整性

```bash
python3 volume_cli.py deps check --project speaker-diarization
```

**输出**：
```
============================================================
🔍 检查依赖完整性: speaker-diarization
============================================================

✅ modelscope
✅ funasr
✅ transformers
❌ torch: No module named 'torch'

============================================================
📊 检查结果
============================================================
✅ 成功: 12
❌ 失败: 1

缺失的包:
  - torch

💡 重新安装:
   python3 volume_cli.py deps install --project speaker-diarization --force
```

---

## 模型管理（models）

### 下载模型（增量）

```bash
# 增量下载（只下载新增的）
python3 volume_cli.py models download --project speaker-diarization

# 强制重新下载
python3 volume_cli.py models download --project speaker-diarization --force
```

**增量下载示例**：
```
============================================================
📥 模型下载
============================================================

📦 项目: speaker-diarization
📂 Volume: /workspace
📍 模型路径: /workspace/models
📊 模型数量: 4

🔍 检测到模型变化:
  ➕ 新增: 1
     - damo/new-model (modelscope)

[1/4] iic/speech_campplus_speaker-diarization_common (modelscope)
  ⏭️  已存在，跳过
[2/4] damo/speech_fsmn_vad_zh-cn-16k-common-pytorch (modelscope)
  ⏭️  已存在，跳过
[3/4] damo/speech_campplus_sv_zh-cn_16k-common (modelscope)
  ⏭️  已存在，跳过
[4/4] damo/new-model (modelscope)
  ✅ 下载完成

============================================================
📊 下载统计
============================================================
✅ 下载成功: 1
⏭️  跳过（已存在）: 3

✅ 所有模型下载完成
```

### 列出模型

```bash
python3 volume_cli.py models list --project speaker-diarization
```

**输出**：
```
============================================================
📦 项目: speaker-diarization
============================================================
📊 模型数量: 4

📁 MODELSCOPE (4 个)
   1. iic/speech_campplus_speaker-diarization_common
   2. damo/speech_fsmn_vad_zh-cn-16k-common-pytorch
   3. damo/speech_campplus_sv_zh-cn_16k-common
   4. damo/speech_campplus-transformer_scl_zh-cn_16k-common
```

### 验证模型完整性

```bash
python3 volume_cli.py models verify --project speaker-diarization
```

**输出**：
```
============================================================
🔍 验证模型完整性: speaker-diarization
============================================================

✅ [1/4] iic/speech_campplus_speaker-diarization_common
✅ [2/4] damo/speech_fsmn_vad_zh-cn-16k-common-pytorch
✅ [3/4] damo/speech_campplus_sv_zh-cn_16k-common
❌ [4/4] damo/missing-model

============================================================
📊 验证结果
============================================================
✅ 存在: 3
❌ 缺失: 1

缺失的模型:
  - damo/missing-model

💡 下载缺失的模型:
   python3 volume_cli.py models download --project speaker-diarization
```

---

## 一键设置（setup）

同时安装依赖和下载模型：

```bash
# 完整设置
python3 volume_cli.py setup --project speaker-diarization

# 只安装依赖
python3 volume_cli.py setup --project speaker-diarization --skip-models

# 只下载模型
python3 volume_cli.py setup --project speaker-diarization --skip-deps

# 使用国内镜像
python3 volume_cli.py setup --project speaker-diarization \
    --mirror https://mirrors.aliyun.com/pypi/simple/
```

**输出**：
```
============================================================
🚀 一键设置项目
============================================================

📦 项目: speaker-diarization

步骤 1/2: 安装依赖
------------------------------------------------------------
[依赖安装输出...]

步骤 2/2: 下载模型
------------------------------------------------------------
[模型下载输出...]

============================================================
✅ 设置完成！
============================================================

📝 下一步:
   1. 删除临时 Pod
   2. 在项目 Dockerfile.serverless 中配置环境变量
   3. 推送代码到 GitHub
   4. 在 RunPod Console 部署 Serverless Endpoint

查看详细文档: VOLUME_SETUP_GUIDE.md
```

---

## 清理（clean）

清理项目数据：

```bash
# 清理依赖
python3 volume_cli.py clean --project speaker-diarization --deps

# 清理模型记录（不删除实际文件）
python3 volume_cli.py clean --project speaker-diarization --models

# 清理所有（依赖+模型+元数据）
python3 volume_cli.py clean --project speaker-diarization --all
```

**交互确认**：
```
============================================================
🗑️  清理项目数据
============================================================

📦 项目: speaker-diarization
📂 Volume: /workspace

⚠️  将清理: 依赖, 模型, 元数据

确认删除？(yes/N): yes

🗑️  删除依赖: /workspace/python-deps/py3.10/speaker-diarization
  ✅ 已删除

⚠️  注意: 模型文件被多项目共享，只清理元数据记录
  ✅ 已清理 4 个模型记录

🗑️  删除元数据: /workspace/.metadata/speaker-diarization.json
  ✅ 已删除

============================================================
✅ 清理完成
============================================================

💡 重新安装:
   python3 volume_cli.py setup --project speaker-diarization
```

---

## 完整工作流

### 初次安装

```bash
# 1. Clone 项目
cd /workspace
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 2. 一键设置
python3 volume_cli.py setup --project speaker-diarization

# 3. 查看状态
python3 volume_cli.py status --project speaker-diarization

# 4. 验证
python3 volume_cli.py deps check --project speaker-diarization
python3 volume_cli.py models verify --project speaker-diarization

# 5. 删除 Pod
```

### 依赖更新

```bash
# 1. 创建临时 Pod
# 2. 拉取最新代码
cd /workspace/runpod-model-manager
git pull

# 3. 查看当前状态
python3 volume_cli.py status --project speaker-diarization

# 4. 增量更新依赖
python3 volume_cli.py deps install --project speaker-diarization

# 5. 下载新模型（如果有）
python3 volume_cli.py models download --project speaker-diarization

# 6. 验证
python3 volume_cli.py deps check --project speaker-diarization
python3 volume_cli.py models verify --project speaker-diarization

# 7. 删除 Pod
```

### 故障排查

```bash
# 1. 检查依赖
python3 volume_cli.py deps check --project speaker-diarization

# 2. 检查模型
python3 volume_cli.py models verify --project speaker-diarization

# 3. 如果有问题，强制重装
python3 volume_cli.py deps install --project speaker-diarization --force
python3 volume_cli.py models download --project speaker-diarization --force
```

---

## 进阶用法

### 多项目管理

```bash
# 查看所有项目
python3 volume_cli.py status

# 设置多个项目
python3 volume_cli.py setup --project speaker-diarization
python3 volume_cli.py setup --project text-generation
python3 volume_cli.py setup --project image-classification

# Volume 结构
/workspace/
├── .metadata/
│   ├── speaker-diarization.json
│   ├── text-generation.json
│   └── image-classification.json
├── python-deps/
│   ├── py3.10/
│   │   ├── speaker-diarization/
│   │   └── image-classification/
│   └── py3.11/
│       └── text-generation/
└── models/  # 所有项目共享
```

### 自定义镜像源

```bash
# 清华源
python3 volume_cli.py deps install --project speaker-diarization \
    --mirror https://pypi.tuna.tsinghua.edu.cn/simple

# 阿里云源
python3 volume_cli.py deps install --project speaker-diarization \
    --mirror https://mirrors.aliyun.com/pypi/simple/

# 官方源
python3 volume_cli.py deps install --project speaker-diarization \
    --mirror https://pypi.org/simple
```

---

## 与旧工具对比

| 旧方式 | 新 CLI | 优势 |
|--------|--------|------|
| `install_dependencies.py` | `volume_cli.py deps install` | 统一接口 |
| `download_models.py` | `volume_cli.py models download` | 统一接口 |
| `volume_status.py` | `volume_cli.py status` | 统一接口 |
| 分散的脚本 | 单一入口点 | 易于记忆和使用 |
| 无依赖/模型分离 | 清晰的命令分组 | 逻辑清晰 |
| 手动组合 | `setup` 一键完成 | 更方便 |

---

## 相关文档

- [VOLUME_SETUP_GUIDE.md](./VOLUME_SETUP_GUIDE.md) - Volume 设置和增量更新
- [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md) - 生产环境最佳实践
- [README.md](./README.md) - 项目总览

---

## 故障排除

### 找不到 Volume

```
❌ 未找到可写的 Volume 挂载点
```

**解决**：
- 确保 Pod 挂载了 Volume
- 检查挂载路径（/workspace 或 /runpod-volume）
- 或设置环境变量：`export RUNPOD_VOLUME_PATH=/your/path`

### 依赖导入失败

```
❌ torch: No module named 'torch'
```

**解决**：
```bash
# 检查依赖
python3 volume_cli.py deps check --project speaker-diarization

# 强制重装
python3 volume_cli.py deps install --project speaker-diarization --force
```

### 模型缺失

```
❌ [4/4] damo/missing-model
```

**解决**：
```bash
# 验证模型
python3 volume_cli.py models verify --project speaker-diarization

# 下载缺失模型
python3 volume_cli.py models download --project speaker-diarization
```

---

🎯 **简洁、统一、高效的 Volume 管理！**
