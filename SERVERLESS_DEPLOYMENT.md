# RunPod Serverless Endpoint 部署指南

## 🎯 Serverless 与 Pod 的区别

### 传统 Pod 模式（持续运行）
```
启动 Pod → 运行服务 → 持续收费 → 手动停止
```
- ✅ 适合：长时间运行的服务
- ❌ 成本高：即使空闲也在计费
- ✅ 可以挂载 Volume

### Serverless 模式（按需运行）
```
请求到达 → 启动容器 → 处理请求 → 返回结果 → 销毁容器
```
- ✅ 适合：间歇性请求的 API
- ✅ 成本低：只在处理请求时收费（按秒计费）
- ❌ 冷启动时间（首次请求较慢）
- ⚠️ 模型必须打包在 Docker 镜像中

---

## 🚀 Serverless 部署策略

### 核心思想：将模型打包进 Docker 镜像

由于 Serverless 容器是临时的，**不能在运行时下载模型**（会导致每次请求都很慢）。因此需要：

1. **构建时下载模型** → 打包进 Docker 镜像
2. **镜像推送到 Docker Hub**
3. **在 RunPod 创建 Serverless Endpoint**
4. **请求时直接从镜像加载模型**（秒级响应）

---

## 📦 方案 1：单项目 Docker 镜像（推荐）

适合：每个项目独立部署为 Serverless Endpoint

### 目录结构

```
my-serverless-project/
├── Dockerfile              # 构建镜像，包含模型
├── handler.py              # Serverless 处理函数
├── requirements.txt        # 依赖
└── download_models.sh      # 构建时下载模型的脚本
```

### 1. 创建下载脚本

```bash
# download_models.sh
#!/bin/bash
set -e

# 设置模型缓存目录（打包进镜像）
export MODELSCOPE_CACHE=/models
export TRANSFORMERS_CACHE=/models
export HF_HOME=/models

mkdir -p /models

# 下载你需要的模型
python3 << EOF
from modelscope import snapshot_download

# 下载模型到 /models
snapshot_download('damo/speech_fsmn_vad_zh-cn-16k-common-pytorch', cache_dir='/models')
snapshot_download('iic/speech_campplus_speaker-diarization_common', cache_dir='/models')

print("✅ 模型下载完成")
EOF
```

### 2. 创建 Dockerfile

```dockerfile
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# === 关键：构建时下载模型到镜像中 ===
COPY download_models.sh .
RUN chmod +x download_models.sh && ./download_models.sh

# 验证模型已下载
RUN ls -lh /models/hub/

# 复制处理函数
COPY handler.py .

# RunPod Serverless 需要的入口
CMD ["python", "-u", "handler.py"]
```

### 3. 创建 handler.py

```python
import os
import runpod

# 设置模型路径（从镜像中读取）
os.environ['MODELSCOPE_CACHE'] = '/models'
os.environ['TRANSFORMERS_CACHE'] = '/models'
os.environ['HF_HOME'] = '/models'

# 加载模型（容器启动时加载一次）
from modelscope.pipelines import pipeline

print("🔄 加载模型...")
vad_pipeline = pipeline(
    task='voice-activity-detection',
    model='damo/speech_fsmn_vad_zh-cn-16k-common-pytorch'
)
print("✅ 模型加载完成")


def handler(event):
    """
    处理 RunPod Serverless 请求
    
    event = {
        "input": {
            "audio_url": "https://example.com/audio.wav"
            # 或其他输入参数
        }
    }
    """
    try:
        input_data = event.get("input", {})
        
        # 你的业务逻辑
        audio_url = input_data.get("audio_url")
        
        # 使用已加载的模型进行推理
        result = vad_pipeline(audio_url)
        
        return {"output": result}
    
    except Exception as e:
        return {"error": str(e)}


# RunPod Serverless 入口
runpod.serverless.start({"handler": handler})
```

### 4. 构建和推送镜像

```bash
# 构建镜像（包含模型，会比较大）
docker build -t your-dockerhub-username/my-serverless-app:v1 .

# 推送到 Docker Hub
docker push your-dockerhub-username/my-serverless-app:v1
```

### 5. 在 RunPod 创建 Serverless Endpoint

1. 登录 RunPod → **Serverless** 页面
2. 点击 **+ New Endpoint**
3. 配置：
   ```
   Name: my-serverless-app
   Docker Image: your-dockerhub-username/my-serverless-app:v1
   GPU Type: 选择合适的 GPU
   Container Disk: 根据镜像大小（建议 10GB+）
   Max Workers: 根据需求
   ```
4. 点击 **Deploy**

### 6. 测试 Endpoint

```python
import requests

endpoint_url = "https://api.runpod.ai/v2/{your-endpoint-id}/runsync"
headers = {"Authorization": f"Bearer {your-api-key}"}

response = requests.post(
    endpoint_url,
    json={
        "input": {
            "audio_url": "https://example.com/test.wav"
        }
    },
    headers=headers
)

print(response.json())
```

---

## 📦 方案 2：使用本项目批量打包（适合多个模型）

如果你有很多模型要打包，可以用这个项目来管理：

### 1. 修改 Dockerfile（包含所有模型）

```dockerfile
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt runpod -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY modelscope_patch.py .
COPY download_models.py .
COPY downloaders/ ./downloaders/
COPY projects/ ./projects/

# === 构建时下载所有模型到 /models ===
ENV MODELSCOPE_CACHE=/models
ENV TRANSFORMERS_CACHE=/models
ENV HF_HOME=/models

RUN python download_models.py --all

# 验证模型
RUN du -sh /models && ls -lh /models/hub/

# 复制你的处理函数
COPY handler.py .

CMD ["python", "-u", "handler.py"]
```

### 2. handler.py 使用打包的模型

```python
import os
import runpod

# 模型已在 /models 中
os.environ['MODELSCOPE_CACHE'] = '/models'
os.environ['TRANSFORMERS_CACHE'] = '/models'
os.environ['HF_HOME'] = '/models'

# 加载你需要的模型
from modelscope.pipelines import pipeline

vad = pipeline(
    task='voice-activity-detection',
    model='damo/speech_fsmn_vad_zh-cn-16k-common-pytorch'
)

diarization = pipeline(
    task='speaker-diarization',
    model='iic/speech_campplus_speaker-diarization_common'
)

def handler(event):
    input_data = event.get("input", {})
    task_type = input_data.get("task")
    
    if task_type == "vad":
        result = vad(input_data["audio"])
    elif task_type == "diarization":
        result = diarization(input_data["audio"])
    else:
        return {"error": "Unknown task"}
    
    return {"output": result}

runpod.serverless.start({"handler": handler})
```

---

## 🎯 方案 3：混合方案（Network Storage + Serverless）

RunPod Serverless 也支持 Network Storage（类似 Volume），但有限制：

### 优势
- ✅ 镜像更小（不包含模型）
- ✅ 模型可以更新而不重新构建镜像

### 劣势
- ❌ 冷启动更慢（需要从 Network Storage 读取模型）
- ⚠️ 网络 I/O 可能成为瓶颈

### 配置方式

```dockerfile
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

# 不在镜像中下载模型
COPY handler.py .

# 运行时从 Network Storage 读取
CMD ["python", "-u", "handler.py"]
```

```python
# handler.py
import os

# Network Storage 挂载在 /runpod-volume
os.environ['MODELSCOPE_CACHE'] = '/runpod-volume/models'
os.environ['TRANSFORMERS_CACHE'] = '/runpod-volume/models'

# 首次请求会从 Network Storage 加载（较慢）
from modelscope.pipelines import pipeline
vad = pipeline(task='...', model='...')
```

在 RunPod 创建 Endpoint 时：
- ✅ 勾选 **Attach Network Volume**
- 选择你的 Volume
- Mount Path: `/runpod-volume`

---

## 💡 最佳实践对比

| 方案 | 镜像大小 | 冷启动速度 | 适用场景 |
|------|---------|-----------|---------|
| **方案 1：单项目单镜像** | 小 (5-10GB) | 快 ⚡ | 单一任务，生产环境 |
| **方案 2：多模型打包** | 大 (20-50GB) | 中等 | 多任务服务 |
| **方案 3：Network Storage** | 最小 (2GB) | 慢 🐌 | 开发测试，模型频繁更新 |

### 推荐选择

**生产环境（推荐方案 1）**：
- 每个模型/任务独立的镜像
- 冷启动快（1-3秒）
- 成本可控

**示例**：
```
dockerhub/vad-service:v1       → VAD Endpoint
dockerhub/diarization-service:v1 → 说话人分割 Endpoint
dockerhub/asr-service:v1       → 语音识别 Endpoint
```

**开发环境（方案 3）**：
- 使用 Network Storage
- 方便调试和更新模型
- 冷启动慢但灵活

---

## 📊 成本估算

### Serverless 计费

```
费用 = (请求处理时间) × (GPU 价格/秒) × (并发数)
```

**示例**：
- GPU: RTX 4090 @ $0.00034/秒
- 每个请求处理时间: 2 秒
- 每天 1000 个请求

```
日成本 = 2秒 × $0.00034 × 1000 = $0.68
月成本 = $0.68 × 30 = $20.4
```

**vs Pod 模式**：
- Pod 24/7 运行: RTX 4090 @ $0.69/小时 = $496/月
- Serverless 节省: 96%+

### 存储成本

**镜像方案**：
- Docker 镜像免费（Docker Hub）
- RunPod 存储小额费用

**Network Storage 方案**：
- $0.10-0.15/GB/月

---

## 🔧 完整示例项目

创建一个完整的 Serverless 项目：

```bash
mkdir my-vad-serverless
cd my-vad-serverless

# 创建文件
cat > requirements.txt << 'EOF'
modelscope
torch
runpod
EOF

cat > download_models.sh << 'EOF'
#!/bin/bash
export MODELSCOPE_CACHE=/models
export TRANSFORMERS_CACHE=/models
mkdir -p /models

python3 << PYTHON
from modelscope import snapshot_download
snapshot_download('damo/speech_fsmn_vad_zh-cn-16k-common-pytorch', cache_dir='/models')
print("✅ 模型下载完成")
PYTHON
EOF

cat > Dockerfile << 'EOF'
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY download_models.sh .
RUN chmod +x download_models.sh && ./download_models.sh
COPY handler.py .
CMD ["python", "-u", "handler.py"]
EOF

cat > handler.py << 'EOF'
import os
import runpod
os.environ['MODELSCOPE_CACHE'] = '/models'

from modelscope.pipelines import pipeline
print("🔄 加载模型...")
vad = pipeline(task='voice-activity-detection',
               model='damo/speech_fsmn_vad_zh-cn-16k-common-pytorch')
print("✅ 模型加载完成")

def handler(event):
    try:
        audio_url = event["input"]["audio_url"]
        result = vad(audio_url)
        return {"output": result}
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
EOF

# 构建
docker build -t yourusername/vad-serverless:v1 .

# 推送
docker push yourusername/vad-serverless:v1
```

---

## 🎬 总结

### Serverless Endpoint 关键点

1. **✅ 模型必须在构建时下载到镜像**
2. **✅ 使用 runpod SDK 编写 handler**
3. **✅ 镜像推送到 Docker Hub/Registry**
4. **✅ 在 RunPod 创建 Endpoint 指向镜像**
5. **✅ 通过 API 调用，按需付费**

### 与传统 Pod 的选择

| 使用场景 | 推荐方案 |
|---------|---------|
| 24/7 运行的服务 | Pod + Volume |
| 间歇性 API 请求 | **Serverless** |
| 开发测试 | Pod |
| 生产 API（低频） | **Serverless** |
| 批量处理 | Pod |

你的场景（Serverless Endpoint）应该使用**方案 1 或方案 2**！
