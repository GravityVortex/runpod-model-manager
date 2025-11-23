# RunPod Model Manager - 操作步骤

## 这个项目是什么

管理 RunPod Volume 上的 Python 依赖和 AI 模型。
- 依赖和模型只装一次，永久保留
- 更新时只装变化的部分
- 不同项目依赖互不干扰

## Volume 目录结构

```
/runpod-volume/ 或 /workspace/
├── .metadata/                           # 元数据（追踪已安装的依赖）
│   ├── speaker-diarization-py3.10.json # 每个项目+版本一个元数据文件
│   └── text-generation-py3.11.json
│
├── python-deps/                         # Python 依赖（按版本隔离）
│   ├── py3.10/
│   │   └── speaker-diarization/        # 项目依赖目录
│   │       ├── torch/
│   │       ├── transformers/
│   │       ├── funasr/
│   │       └── ... (40+ 个包)
│   └── py3.11/
│       └── text-generation/
│
└── models/                              # AI 模型（所有项目共享）
    └── hub/
        ├── iic/speech_campplus_speaker-diarization_common/
        ├── damo/speech_fsmn_vad_zh-cn-16k-common-pytorch/
        └── ... (更多模型)
```

## 当前项目：Speaker Diarization（说话人分割）

识别音频中谁在什么时候说话。

依赖的模型（从 ModelScope 下载）：
- speech_campplus_speaker-diarization_common
- speech_fsmn_vad_zh-cn-16k-common-pytorch  
- speech_campplus_sv_zh-cn_16k-common
- speech_campplus-transformer_scl_zh-cn_16k-common

依赖的 Python 包（40+ 个）：
- PyTorch 2.4.1
- FunASR 0.8.8
- transformers、onnxruntime、librosa 等

## 操作步骤

### 步骤1：初始化 Volume（临时 Pod）

#### 1.1 创建临时 Pod

访问 RunPod 控制台：https://www.runpod.io/console/pods

1. **点击 "+ Deploy"**

2. **选择模板**：
   - 推荐：`RunPod PyTorch` 或任意带 Python 的镜像
   - GPU：选择最便宜的即可（如 RTX 4000）

3. **配置 Network Volume**：
   - 在 "Network Volume" 部分
   - 选择你的 Volume（如果没有，先创建一个 15GB+ 的 Volume）
   - Mount Path: `/workspace`

4. **点击 "Deploy"**，等待 Pod 启动（约 30 秒）

#### 1.2 打开 Web Terminal

1. 在 Pods 列表中找到刚创建的 Pod
2. 点击 **"Connect"** 按钮
3. 选择 **"Start Web Terminal"**
4. 等待终端加载完成

#### 1.3 执行安装命令

在 Web Terminal 中执行：

```bash
# 1. Clone 项目
cd /workspace
git clone https://github.com/GravityVortex/runpod-model-manager.git
cd runpod-model-manager

# 2. 安装管理工具依赖
pip install -r requirements.txt

# 3. 一键安装项目（依赖 + 模型）
python3 volume_cli.py setup --project speaker-diarization

# 或分步执行：
# python3 volume_cli.py deps install --project speaker-diarization
# python3 volume_cli.py models download --project speaker-diarization
```

**等待安装完成**（约 10 分钟）

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
# 2. 创建临时 Pod，挂载同一个 Volume
cd /workspace/runpod-model-manager
git pull

# 3. 增量安装（只装变化的包）
python3 volume_cli.py deps install --project speaker-diarization
# 耗时：20 秒（vs 完整安装 10 分钟）

# 4. 强制重装（可选）
python3 volume_cli.py deps install --project speaker-diarization --force
```

---

## 技术架构

### 🏗️ 核心模块

```
runpod-model-manager/
├── volume_cli.py              # CLI 入口（argparse）
├── volume_manager.py          # Volume 管理核心
│   ├── _load_metadata()       # 加载元数据（追踪已安装的依赖）
│   ├── check_dependencies_changed()  # 检测依赖变化
│   ├── install_dependencies_from_config()  # 增量安装
│   └── _fix_modelscope_release_date()  # ModelScope 兼容性修复
├── dependency_installer.py    # 依赖安装器（解析 YAML）
├── downloaders/               # 模型下载器
│   ├── modelscope_downloader.py
│   └── huggingface_downloader.py
└── commands/                  # CLI 命令实现
    ├── dependencies.py        # deps 命令
    ├── models.py             # models 命令
    └── setup.py              # setup 命令
```

### 🔄 增量安装原理

```python
# 伪代码
def install_dependencies_from_config(project_name, config_file):
    # 1. 读取元数据
    old_deps = load_metadata(project_name)  # {'torch==2.4.0': {}, 'funasr==0.8.7': {}}
    
    # 2. 读取配置文件
    new_deps = parse_yaml(config_file)  # ['torch==2.4.1', 'funasr==0.8.8', 'pandas==2.0.0']
    
    # 3. 比较变化
    added = ['pandas==2.0.0']      # 新增的包
    removed = []                   # 删除的包
    updated = ['torch==2.4.1', 'funasr==0.8.8']  # 版本更新的包
    
    # 4. 决定安装策略
    if removed:
        # 有删除 → 全量重装（避免依赖残留）
        full_reinstall()
    elif added or updated:
        # 只有新增/更新 → 增量安装（快速）
        pip install --upgrade --target /volume/deps pandas==2.0.0 torch==2.4.1 funasr==0.8.8
    else:
        # 无变化 → 跳过
        print("依赖未变化，跳过安装")
    
    # 5. 更新元数据
    save_metadata(project_name, new_deps)
```

### 🎯 关键优化

1. **直接在正式目录安装**（新）
   - 旧方案：复制 5000+ 文件到临时目录 → 安装 → 替换（耗时 30s）
   - 新方案：直接 `pip install --upgrade` 到正式目录（耗时 5s）
   - 提升：6倍速度

2. **按 Python 版本隔离元数据**
   - 文件名：`speaker-diarization-py3.10.json`
   - 避免不同版本的依赖冲突

3. **支持 `--no-deps` 选项**
   - 解决 funasr 的 `umap` vs `umap-learn` 包名问题
   - 手动声明所有依赖，跳过 pip 依赖检查

4. **ModelScope 兼容性自动修复**
   - 修改 `__release_datetime__` 为过去日期
   - 跳过 AST 扫描，避免 Python 3.10 的 `type_params` 错误

---

## 常见问题

### Q1: 为什么需要两次 `pip install`？

**A**: 两个不同的目的：

1. **第一次**（临时 Pod）：`pip install -r requirements.txt`
   - 安装管理工具依赖（pyyaml, modelscope）
   - 让 `volume_cli.py` 能运行

2. **第二次**（volume_cli.py 执行）：`volume_cli.py deps install`
   - 安装业务项目依赖（torch, funasr）
   - 安装到 Volume，供 Serverless Pod 使用

### Q2: 增量安装真的安全吗？

**A**: 安全，因为：
- `pip install --upgrade` 不会删除旧版本，只是覆盖
- 如果安装失败，旧版本依然可用
- 如果检测到删除包，会自动切换到全量重装

### Q3: funasr 的 `--no-deps` 会导致缺少依赖吗？

**A**: 不会，因为：
- funasr 的所有依赖已在 `dependencies.yaml` 中显式声明
- 参考官方 `setup.py` 确认了依赖列表
- `--no-deps` 只是跳过 pip 的依赖检查，包本身正常安装

### Q4: 如何添加新项目？

**A**: 参考 [projects/HOWTO_ADD_PROJECT.md](./projects/HOWTO_ADD_PROJECT.md)

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

**最后更新**: 2024-11-24
