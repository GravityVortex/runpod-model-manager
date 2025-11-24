# RunPod Model Manager - 操作指南

## 这是什么

在 RunPod Volume 上管理 Python 依赖和 AI 模型：
- ✅ 依赖和模型只装一次，永久保留在 Volume
- ✅ 更新时只装变化的部分（增量更新，节省时间）
- ✅ 不同项目依赖独立隔离，互不干扰

---

## 快速上手

### 步骤0：创建 Network Volume（一次性）

如果你还没有 Volume，需要先创建一个。

#### 0.1 访问 Storage 页面

访问 RunPod 控制台：https://www.runpod.io/console/user/storage

#### 0.2 创建 Volume

1. **点击 "+ Network Volume"**

2. **配置 Volume**：
   - **Name**: 随意命名（如 `ai-models-volume`）
   - **Size**: 至少 15GB（推荐 20GB），后期也能动态添加，可以先买小点的
   - **Region**: **选择你常用的地区**（如 `US-CA-1`）

3. **点击 "Create"**，等待创建完成（约 10 秒）

⚠️ **重要注意事项**：
- 💰 **地区选择**：选择价格便宜、网络快的地区
- 📍 **地区一致**：后续所有 Pod 必须选择**相同地区**，否则无法挂载 Volume
- 💾 **容量规划**：依赖约 800M，一个项目如果带有torch等机器学习模型，那么建议一个项目给到10G的空间

---

### 步骤1：初始化 Volume（临时 Pod）

#### 1.1 创建临时 Pod

访问 RunPod 控制台：https://www.runpod.io/console/pods

1. **点击 "+ Deploy"**

2. **选择模板**：
   - 推荐：`RunPod PyTorch` 或任意带 Python 的镜像
   - **Region**: **必须选择与 Volume 相同的地区**
   - GPU：选择最便宜的即可（如 RTX 4000）

3. **配置 Network Volume**：
   - 在 "Network Volume" 部分（界面上方横着的）

   ![image-20251124143350685](/Users/dashuai/Library/Application Support/typora-user-images/image-20251124143350685.png)

   - 选择你刚创建的 Volume

4. 滚动到页面下方，Pod Template需要根据你依赖的cuda和python版本来选择，比如你的是cu121，python310（插一嘴，这个配置尽量其他模型就保持不变了），那么就选择**runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04**，减少后期安装依赖不必要的麻烦

![image-20251124144216800](/Users/dashuai/Library/Application Support/typora-user-images/image-20251124144216800.png)

5. Instance Pricing，这里你就选择spot就好，怎么便宜怎么来

6. **点击 "Deploy"**，等待 Pod 启动

⚠️ **注意事项**：
- Volume 挂载路径必须放在 `/workspace` 下面（cd /workspace）
- GPU 选最便宜的即可，不影响安装速度
- 临时 Pod 可以随时删除，数据永久保存在 Volume

#### 1.2 打开 Web Terminal

1. 在 Pods 列表中找到刚创建的 Pod

2. 点击 **"Connect"** 按钮

   ![image-20251124151718132](/Users/dashuai/Library/Application Support/typora-user-images/image-20251124151718132.png)

3. 打开，稍等片刻后，点击 **"Open Web Terminal"**

4. 等待终端加载完成

#### 1.3 执行安装命令

在 Web Terminal 中执行：

```bash
# 1. Clone 项目
cd /workspace
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 2. 安装管理工具依赖（按理说只做第一次）
pip install -r requirements.txt

# 3. 一键安装项目（依赖 + 模型）
python3 volume_cli.py setup --project speaker-diarization

# 或分步执行：
# python3 volume_cli.py deps install --project speaker-diarization
# python3 volume_cli.py models download --project speaker-diarization
```

**等待安装完成**（约 10 分钟）

⚠️ **安装过程说明**：
- 首次安装约 10 分钟（下载 PyTorch 和模型较大）
- 会自动检测并安装正确的 Python 版本
- 出现 "Building wheel" 是正常现象，请耐心等待

#### 1.4 验证安装

```bash
# 查看状态
python3 volume_cli.py status --project speaker-diarization

# 查看依赖占用空间
du -sh /workspace/python-deps/py3.10/speaker-diarization/
# 约 800M

# 查看模型占用空间
du -sh /workspace/models/
# 约 8-10GB
```

#### 1.5 删除临时 Pod

1. 返回 RunPod Pods 页面
2. 找到刚才的临时 Pod
3. 点击右侧 **"⋮"** → **"Stop"** → 确认删除

**重要**：Volume 中的依赖和模型已永久保存，删除 Pod 不影响。

### 步骤2：业务项目使用

依赖和模型安装完成后，业务项目如何使用 Volume 中的资源？

详见业务项目文档：
- **说话人分割项目**: [GravityVortex/zhesheng-model-speaker-reg](https://github.com/GravityVortex/zhesheng-model-speaker-reg)
  - `RUNPOD_DEPLOY.md` - 完整部署指南
  - `Dockerfile.serverless` - 生产环境 Dockerfile
  - `api.py` - FastAPI 服务代码

**关键配置**：
```dockerfile
# Dockerfile.serverless 中设置环境变量指向 Volume
ENV PYTHONPATH=/runpod-volume/python-deps/py3.10/speaker-diarization:$PYTHONPATH \
    MODELSCOPE_CACHE=/runpod-volume/models
```

### 步骤3：增量更新

```bash
# 1. 修改配置文件 projects/speaker_diarization/dependencies.yaml
# 2. 创建临时 Pod，挂载同一个 Volume（地区必须一致）
cd /workspace/runpod-model-manager
git pull

# 3. 增量安装（只装变化的包）
python3 volume_cli.py deps install --project speaker-diarization
# 耗时：20 秒（vs 完整安装 10 分钟）

# 4. 强制重装（可选）
python3 volume_cli.py deps install --project speaker-diarization --force
```

💡 **性能对比**：
- ⚡ 增量更新：20 秒（只装变化的包）
- 🔄 完整重装：10 分钟（`--force` 参数）

---

## 关联业务项目

本工具（runpod-model-manager）负责依赖和模型管理，具体的业务实现在独立项目中：

- **说话人分割项目**: [GravityVortex/zhesheng-model-speaker-reg](https://github.com/GravityVortex/zhesheng-model-speaker-reg)
  - 业务代码（api.py, mydemo.py）
  - API 接口文档
  - 部署配置（Dockerfile.serverless）
  - 性能指标和测试

### 项目联动方式

1. **依赖配置同步**：
   ```yaml
   # runpod-model-manager/projects/speaker_diarization/dependencies.yaml
   # 与业务项目的 requirements.txt 保持一致
   ```

2. **模型列表同步**：
   ```python
   # runpod-model-manager/projects/speaker_diarization/config.py
   # models 列表与业务项目使用的模型一致
   ```

3. **Volume 路径约定**：
   ```bash
   # 两个项目使用统一的 Volume 路径
   /runpod-volume/python-deps/py3.10/speaker-diarization
   /runpod-volume/models
   ```

---

## ⚠️ 重要注意事项

### Volume 配置
- 📍 **地区一致**：所有 Pod 必须与 Volume 在**同一地区**（这是最重要的！）
- ✅ **路径一致**：所有 Pod 必须挂载到同一路径（`/workspace` 或 `/runpod-volume`）
- ✅ **容量预留**：至少 15GB（依赖 800M + 模型 8-10GB）
- ✅ **数据持久**：删除 Pod 不影响 Volume 数据

### 安装过程
- ⏱️ **首次安装**：10 分钟左右，需下载大量依赖和模型
- ⚡ **增量更新**：20 秒左右，只装变化的包
- 🔄 **自动处理**：自动检测 Python 版本并安装

### 常见问题
- ❓ **看不到 Volume 选项**：检查 Pod 和 Volume 是否在同一地区
- ❓ **安装失败**：检查网络连接，重新运行命令即可
- ❓ **找不到包**：确认 `requirements.txt` 已安装（管理工具依赖）
- ❓ **版本冲突**：工具会自动处理，无需手动干预

---

## 📚 附录

### Volume 目录结构

```
/runpod-volume/ 或 /workspace/
├── .metadata/                    # 元数据（追踪已安装的依赖）
├── python-deps/                  # Python 依赖（按版本隔离）
│   ├── py3.10/
│   │   └── speaker-diarization/ # 项目依赖目录
│   └── py3.11/
│       └── other-project/
└── models/                       # AI 模型（所有项目共享）
    └── hub/
```

### 如何添加新项目

参考：[projects/HOWTO_ADD_PROJECT.md](./projects/HOWTO_ADD_PROJECT.md)

### 技术细节

参考：[MODELSCOPE_AST_FIX.md](./MODELSCOPE_AST_FIX.md) - ModelScope 兼容性技术文档

---

**最后更新**: 2024-11-24
