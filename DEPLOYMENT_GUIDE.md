# RunPod 一站式部署指南

本指南介绍如何在 RunPod 环境中一站式部署项目，包括模型上传和依赖安装。

---

## 目录

- [前置条件](#前置条件)
- [部署方式](#部署方式)
- [完整部署流程](#完整部署流程)
- [验证部署](#验证部署)
- [业务容器配置](#业务容器配置)
- [常见问题](#常见问题)

---

## 前置条件

### 1. S3 配置

创建配置文件 `~/.runpod_s3_config`：

```ini
[runpods3]
aws_access_key_id = user_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
aws_secret_access_key = rps_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
datacenter = US-IL-1
volume_id = your_volume_id
```

获取凭证：
- 登录 RunPod 控制台
- 进入 Volume 详情页
- 点击 "S3 Credentials" 获取

### 2. Volume 创建

- 在支持 S3 API 的 datacenter 创建 Volume
- 支持的 datacenter：`US-IL-1`, `US-CA-2`, `US-KS-2`, `EU-RO-1`, `EU-CZ-1`, `EUR-IS-1`

### 3. 本地模型文件

准备好需要上传的模型文件目录。

---

## 部署方式

本工具提供三种部署方式，根据需求选择：

### 方式 1: 使用 deploy 命令（推荐）

**适用场景**：一站式部署，自动化程度最高

```bash
python3 volume_cli.py deploy \
  --project speaker-diarization \
  --models-dir /path/to/local/models
```

**优势**：
- ✅ 一个命令完成模型上传
- ✅ 自动输出依赖安装命令
- ✅ 自动输出验证清单和配置示例

### 方式 2: 使用项目专属脚本

**适用场景**：只需要上传模型，不需要完整部署指南

```bash
python3 src/projects/speaker_diarization/upload_models.py \
  --models-dir /path/to/local/models
```

**优势**：
- ✅ 项目自包含，脚本在项目目录内
- ✅ 极简调用，只需 8 行代码

### 方式 3: 仅输出部署指南

**适用场景**：模型已上传，只需要查看部署步骤

```bash
python3 volume_cli.py deploy \
  --project speaker-diarization \
  --skip-upload
```

---

## 完整部署流程

### 步骤 1: 本地上传模型

在本地机器执行：

```bash
python3 volume_cli.py deploy \
  --project speaker-diarization \
  --models-dir /Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/speaker-reg/models
```

**输出示例**：

```
============================================================
🚀 一站式部署: speaker-diarization
============================================================

[1/4] 📤 上传模型到 S3
────────────────────────────────────────────────────────────
🚀 上传 speaker-diarization 模型到 S3

本地目录: /Users/dashuai/Downloads/.../speaker-reg/models
远程前缀: speaker-reg
Volume路径: /runpod-volume/models/speaker-reg/

📂 本地目录: /Users/dashuai/Downloads/.../speaker-reg/models
   文件数量: 21
   总大小: 31.47 MB

📤 开始上传 21 个文件...

[1/21] iic/speech_campplus_sv_zh_en_16k-common_advanced/campplus_cn_en_common.pt
   ✅ 成功

...

============================================================
📊 上传完成: 21/21
============================================================
✅ 所有文件上传成功！

[2/4] 📋 临时 Pod 依赖安装命令
────────────────────────────────────────────────────────────
在 RunPod 控制台创建临时 Pod，执行以下命令：

  git clone https://github.com/xxx/runpod-model-manager.git
  cd runpod-model-manager
  pip install -r requirements.txt
  python3 volume_cli.py deps install --project speaker-diarization

[3/4] ✅ 验证清单
────────────────────────────────────────────────────────────
□ 模型: /runpod-volume/models/speaker-reg/
□ 依赖: /runpod-volume/python-deps/py3.10/speaker-diarization/

验证命令:
  python3 volume_cli.py status --project speaker-diarization

[4/4] 🐳 业务容器配置
────────────────────────────────────────────────────────────
# handler.py
import sys
sys.path.insert(0, '/runpod-volume/python-deps/py3.10/speaker-diarization')

import os
os.environ['MODELSCOPE_CACHE'] = '/runpod-volume/models'

============================================================
✅ 部署指南已生成
============================================================
```

### 步骤 2: 创建临时 Pod 安装依赖

1. 在 RunPod 控制台创建临时 Pod
   - 选择支持 S3 的 datacenter（与 Volume 相同）
   - 挂载 Volume
   - 选择合适的 GPU（或 CPU）

2. 在 Pod 终端执行上述输出的命令：

```bash
git clone https://github.com/xxx/runpod-model-manager.git
cd runpod-model-manager
pip install -r requirements.txt
python3 volume_cli.py deps install --project speaker-diarization
```

**依赖安装输出示例**：

```
============================================================
🔧 依赖管理（增量）
============================================================

📦 项目: speaker-diarization
📂 Volume: /runpod-volume
🐍 需要 Python: 3.10
🐍 当前 Python: 3.10
📝 配置文件: src/projects/speaker_diarization/dependencies.yaml
✅ 配置文件存在
✅ Python 版本匹配

============================================================
📦 使用配置文件安装依赖
============================================================

🔍 检查依赖变更...
   Python 版本: 3.10
   配置包数量: 45

📦 首次安装，开始安装所有依赖...

============================================================
📦 开始安装依赖
============================================================

────────────────────────────────────────────────────────────
📦 安装组: pytorch
   PyTorch with CUDA 12.1 support
   包数量: 2
   索引 URL: https://download.pytorch.org/whl/cu121
────────────────────────────────────────────────────────────

💻 命令: pip install torch==2.4.1 torchaudio==2.4.1 -t /runpod-volume/python-deps/py3.10/speaker-diarization --index-url https://download.pytorch.org/whl/cu121

...

✅ 组 'pytorch' 安装成功

...

============================================================
✅ 安装完成！
============================================================
📊 统计: 总计 45, 安装 45, 失败 0

📝 使用说明:
  FROM python:3.10
  ENV PYTHONPATH=/runpod-volume/python-deps/py3.10/speaker-diarization:$PYTHONPATH
```

### 步骤 3: 验证部署

在临时 Pod 中执行：

```bash
python3 volume_cli.py status --project speaker-diarization
```

**验证输出示例**：

```
============================================================
📊 Volume 状态
============================================================
📂 Volume 路径: /runpod-volume

项目: speaker-diarization
  依赖数量: 45
  模型数量: 4
  最后更新: 2025-12-25T10:30:00

✅ 所有项目状态正常
```

### 步骤 4: 删除临时 Pod

依赖安装完成后，可以删除临时 Pod，Volume 中的数据会保留。

---

## 业务容器配置

### Serverless Handler 示例

```python
# handler.py
import sys
import os

# 引入 Volume 依赖
sys.path.insert(0, '/runpod-volume/python-deps/py3.10/speaker-diarization')

# 设置模型缓存
os.environ['MODELSCOPE_CACHE'] = '/runpod-volume/models'

import runpod

def handler(event):
    """业务逻辑"""
    # 现在可以导入项目依赖
    from modelscope.pipelines import pipeline
    
    # 加载模型（从 Volume 缓存）
    diarization_pipeline = pipeline(
        task='speaker-diarization',
        model='iic/speech_campplus_speaker-diarization_common'
    )
    
    # 处理请求
    audio_path = event['input']['audio_path']
    result = diarization_pipeline(audio_path)
    
    return {"status": "success", "result": result}

runpod.serverless.start({"handler": handler})
```

### Dockerfile 示例

```dockerfile
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制业务代码
COPY . /app
WORKDIR /app

# 安装 RunPod SDK（业务依赖已在 Volume 中）
RUN pip install runpod

# 设置环境变量（在 RunPod 控制台配置）
# ENV PYTHONPATH=/runpod-volume/python-deps/py3.10/speaker-diarization:$PYTHONPATH
# ENV MODELSCOPE_CACHE=/runpod-volume/models

CMD ["python", "handler.py"]
```

### RunPod 控制台配置

在 Serverless Endpoint 配置中：

1. **Volume 挂载**：选择已部署的 Volume
2. **环境变量**：
   ```
   PYTHONPATH=/runpod-volume/python-deps/py3.10/speaker-diarization:$PYTHONPATH
   MODELSCOPE_CACHE=/runpod-volume/models
   ```

---

## 验证方法

### 1. 检查模型文件

```bash
ls -lh /runpod-volume/models/speaker-reg/
```

应该看到上传的模型文件。

### 2. 检查依赖目录

```bash
ls -lh /runpod-volume/python-deps/py3.10/speaker-diarization/
```

应该看到安装的 Python 包。

### 3. 测试导入

```bash
python3 -c "
import sys
sys.path.insert(0, '/runpod-volume/python-deps/py3.10/speaker-diarization')
import torch
import modelscope
print('✅ 依赖导入成功')
print(f'PyTorch 版本: {torch.__version__}')
print(f'ModelScope 版本: {modelscope.__version__}')
"
```

### 4. 测试模型加载

```bash
python3 -c "
import sys
import os
sys.path.insert(0, '/runpod-volume/python-deps/py3.10/speaker-diarization')
os.environ['MODELSCOPE_CACHE'] = '/runpod-volume/models'

from modelscope.pipelines import pipeline
pipeline = pipeline(
    task='speaker-diarization',
    model='iic/speech_campplus_speaker-diarization_common'
)
print('✅ 模型加载成功')
"
```

---

## 常见问题

### Q1: 模型上传失败怎么办？

**检查**：
1. S3 配置文件是否正确（`~/.runpod_s3_config`）
2. Volume 是否在支持 S3 的 datacenter
3. 网络连接是否正常
4. 本地模型文件路径是否正确

**解决**：
```bash
# 重新上传
python3 volume_cli.py deploy \
  --project speaker-diarization \
  --models-dir /path/to/models
```

### Q2: 依赖安装很慢怎么办？

**使用国内镜像源**：

```bash
python3 volume_cli.py deps install \
  --project speaker-diarization \
  --mirror https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: Python 版本不匹配怎么办？

工具会自动检测并尝试安装正确的 Python 版本。如果失败：

```bash
# 手动安装
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-pip

# 使用正确版本重新运行
python3.10 volume_cli.py deps install --project speaker-diarization
```

### Q4: 如何更新已部署的项目？

**更新模型**：
```bash
python3 volume_cli.py deploy \
  --project speaker-diarization \
  --models-dir /path/to/new/models
```

**更新依赖**：
```bash
# 修改 dependencies.yaml 后
python3 volume_cli.py deps install \
  --project speaker-diarization \
  --force
```

### Q5: 如何清理项目数据？

```bash
# 清理依赖
python3 volume_cli.py clean --project speaker-diarization --deps

# 清理模型元数据（不删除实际文件）
python3 volume_cli.py clean --project speaker-diarization --models

# 清理所有
python3 volume_cli.py clean --project speaker-diarization --all
```

### Q6: 多个项目如何共享 Volume？

每个项目的模型和依赖都按项目名隔离：

```
/runpod-volume/
├── models/
│   ├── speaker-diarization/  # 项目1
│   └── text-generation/      # 项目2
└── python-deps/
    └── py3.10/
        ├── speaker-diarization/  # 项目1
        └── text-generation/      # 项目2
```

分别部署即可：

```bash
# 部署项目1
python3 volume_cli.py deploy --project speaker-diarization --models-dir /path1

# 部署项目2
python3 volume_cli.py deploy --project text-generation --models-dir /path2
```

---

## 相关文档

- [模型部署技术对比](MODEL_DEPLOYMENT_GUIDE.md)
- [S3 上传详细指南](S3_UPLOAD_GUIDE.md)
- [项目配置指南](src/projects/PROJECT_SETUP.md)

---

**最后更新**: 2025-12-25

