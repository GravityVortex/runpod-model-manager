# RunPod 模型管理完整指南

本文档介绍如何在 RunPod 环境中管理模型，包括两种主要方式：**S3 上传**和**在线下载**。

---

## 目录

- [方式一：S3 上传（推荐用于大模型）](#方式一s3-上传推荐用于大模型)
- [方式二：在线下载（推荐用于首次部署）](#方式二在线下载推荐用于首次部署)
- [使用场景对比](#使用场景对比)
- [常见问题](#常见问题)

---

## 方式一：S3 上传（推荐用于大模型）

### 适用场景

- ✅ 已有本地模型文件
- ✅ 模型文件较大（>1GB）
- ✅ 需要快速部署到多个 Pod
- ✅ 避免重复下载，节省时间

### 前置条件

1. **创建支持 S3 的 Volume**

   - 在支持 S3 API 的 datacenter 创建 Volume
   - 支持的 datacenter：`US-IL-1`, `US-CA-2`, `US-KS-2`, `EU-RO-1`, `EU-CZ-1`, `EUR-IS-1`

2. **配置 S3 凭证**

创建配置文件 `~/.runpod_s3_config`：

```ini
[runpods3]
aws_access_key_id = user_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
aws_secret_access_key = rps_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
datacenter = US-IL-1
volume_id = your_volume_id
```

获取凭证方式：

- 登录 RunPod 控制台
- 进入 Volume 详情页
- 点击 "S3 Credentials" 获取

### 使用方法

#### 1. 上传单个文件

```python
from s3_uploader import upload_file

# 上传模型文件
success = upload_file(
    local_path='/path/to/model.bin',
    remote_key='my-model/model.bin',
    models_subdir='/workspace/models'
)

if success:
    print("✅ 上传成功")
```

**结果路径**：`/workspace/models/my-model/model.bin`

#### 2. 上传整个目录

```python
from s3_uploader import upload_directory

# 上传整个模型目录
result = upload_directory(
    local_dir='/local/bert-base',
    remote_prefix='bert-base',
    models_subdir='/workspace/models',
    include_parent_dir=False
)

print(f"上传完成: {result['success']}/{result['total']} 个文件")
```

**目录结构保留**：

```
本地: /local/bert-base/config.json
S3:   /workspace/models/bert-base/config.json
```

#### 3. 实际案例：上传 speaker-reg 模型

```python
from s3_uploader import upload_directory

result = upload_directory(
    local_dir='/Users/dashuai/Downloads/个人文件夹/音频转换/这声-推理模型/推理模型/speaker-reg/models',
    remote_prefix='speaker-reg',
    models_subdir='/workspace/models',
    include_parent_dir=False
)
```

**上传结果**：

- 文件数量：21 个
- 总大小：31.47 MB
- S3 路径：`/workspace/models/speaker-reg/`

#### 4. 验证上传结果

```bash
# 列出 S3 上的文件
python3 list_s3_files.py --prefix workspace/models/speaker-reg/
```

### 参数说明

| 参数                           | 说明                   | 默认值              |
| ------------------------------ | ---------------------- | ------------------- |
| `local_path` / `local_dir`     | 本地文件/目录路径      | 必填                |
| `remote_key` / `remote_prefix` | 远程路径（业务目录名） | 可选                |
| `models_subdir`                | 基础路径前缀           | `/workspace/models` |
| `include_parent_dir`           | 是否包含父目录名       | `False`             |
| `verbose`                      | 是否显示详细日志       | `True`              |

### 日志输出示例

```
📂 本地目录: /local/speaker-reg/models
   文件数量: 21
   总大小: 31.47 MB

🔧 S3 配置
   Endpoint: https://s3api-us-il-1.runpod.io/
   Volume: dkhgi7iqpu

📤 开始上传 21 个文件...

[1/21] iic/speech_campplus_sv_zh_en_16k-common_advanced/campplus_cn_en_common.pt
   → s3://dkhgi7iqpu/workspace/models/speaker-reg/iic/speech_campplus_sv_zh_en_16k-common_advanced/campplus_cn_en_common.pt
   ✅ 成功

...

============================================================
📊 上传完成
   总计: 21 个文件
   成功: 21 个
   失败: 0 个
```

---

## 方式二：在线下载（推荐用于首次部署）

### 适用场景

- ✅ 首次部署项目
- ✅ 模型托管在 ModelScope/HuggingFace
- ✅ 自动管理依赖和模型
- ✅ 增量更新支持

### 前置条件

1. **准备项目配置**

创建项目目录结构：

```
src/projects/
└── your-project/
    ├── __init__.py
    ├── config.py          # 项目配置
    └── dependencies.yaml  # 依赖配置
```

2. **配置依赖文件**

`dependencies.yaml` 示例：

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
      - torchaudio==2.4.1

  modelscope:
    packages:
      - modelscope==1.20.1
      - funasr==1.2.7

install_order:
  - pytorch
  - modelscope
```

3. **配置项目文件**

`config.py` 示例：

```python
from projects.base import BaseProject

class YourProject(BaseProject):
    @property
    def name(self) -> str:
        return "your-project"

    @property
    def dependencies_file(self) -> str:
        return "src/projects/your-project/dependencies.yaml"

    @property
    def models(self) -> dict:
        return {
            'modelscope': [
                'iic/speech_campplus_sv_zh_en_16k-common_advanced',
                'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch'
            ]
        }

    def download_models(self, model_cache: str):
        """下载模型"""
        from downloaders.factory import DownloaderFactory

        print(f"\n{'='*60}")
        print(f"📦 项目: {self.name}")
        print(f"{'='*60}\n")

        all_models = []
        for source, model_list in self.models.items():
            for model_id in model_list:
                all_models.append((model_id, source))

        success = 0
        failed = []

        for i, (model_id, source) in enumerate(all_models, 1):
            print(f"[{i}/{len(all_models)}] {model_id} ({source})")

            try:
                downloader = DownloaderFactory.get_downloader(source, model_cache)
            except ValueError as e:
                print(f"  ❌ {e}")
                failed.append(model_id)
                continue

            if downloader.check_model_exists(model_id):
                print(f"  ⏭️  已存在，跳过")
                continue

            if downloader.download(model_id):
                print(f"  ✅ 下载完成")
                success += 1
            else:
                print(f"  ❌ 下载失败")
                failed.append(model_id)

        print(f"\n{'='*60}")
        print(f"📊 下载完成: {success}/{len(all_models)}")
        if failed:
            print(f"❌ 失败: {', '.join(failed)}")
        print(f"{'='*60}")
```

### 使用方法

#### 1. 一键设置（依赖 + 模型）

```bash
# 安装依赖并下载模型
python3 volume_cli.py setup --project your-project
```

#### 2. 仅安装依赖

```bash
# 安装项目依赖
python3 volume_cli.py deps install --project your-project

# 强制重新安装
python3 volume_cli.py deps install --project your-project --force

# 使用自定义镜像源
python3 volume_cli.py deps install --project your-project --mirror https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 仅下载模型

```bash
# 下载项目模型
python3 volume_cli.py models download --project your-project

# 强制重新下载
python3 volume_cli.py models download --project your-project --force
```

#### 4. 查看状态

```bash
# 查看所有项目状态
python3 volume_cli.py status

# 查看指定项目
python3 volume_cli.py status --project your-project
```

#### 5. 验证模型

```bash
# 验证模型完整性
python3 volume_cli.py models verify --project your-project
```

### 实际案例：speaker-diarization 项目

#### 项目配置

**dependencies.yaml**：

```yaml
groups:
  pytorch:
    index_url: "https://download.pytorch.org/whl/cu121"
    packages:
      - torch==2.4.1
      - torchaudio==2.4.1

  modelscope:
    packages:
      - modelscope==1.20.1
      - funasr==1.2.7
      - onnxruntime-gpu==1.20.1

install_order:
  - pytorch
  - modelscope
```

**config.py**：

```python
@property
def models(self) -> dict:
    return {
        'modelscope': [
            'iic/speech_campplus_sv_zh_en_16k-common_advanced',
            'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
            'iic/speech_campplus_speaker-diarization_common'
        ]
    }
```

#### 部署步骤

```bash
# 1. 一键设置
python3 volume_cli.py setup --project speaker-diarization

# 2. 查看状态
python3 volume_cli.py status --project speaker-diarization

# 3. 验证模型
python3 volume_cli.py models verify --project speaker-diarization
```

### 模型存储路径

下载的模型会存储在：

**ModelScope 模型**：

```
/workspace/models/hub/
└── iic/
    ├── speech_campplus_sv_zh_en_16k-common_advanced/
    └── speech_fsmn_vad_zh-cn-16k-common-pytorch/
```

**HuggingFace 模型**：

```
/workspace/models/models--/
└── organization--model-name/
```

---

## 使用场景对比

| 场景                | S3 上传                  | 在线下载             |
| ------------------- | ------------------------ | -------------------- |
| **首次部署**        | ❌ 需要先本地下载        | ✅ 直接从源下载      |
| **大模型（>10GB）** | ✅ 上传一次，多次使用    | ⚠️ 每次都要下载      |
| **多 Pod 部署**     | ✅ 共享 Volume，无需重复 | ⚠️ 每个 Pod 都要下载 |
| **离线环境**        | ✅ 支持                  | ❌ 需要网络          |
| **版本控制**        | ✅ 手动管理              | ✅ 自动管理          |
| **依赖管理**        | ❌ 需要单独处理          | ✅ 自动安装          |
| **增量更新**        | ❌ 需要重新上传          | ✅ 自动检测          |

### 推荐方案

#### 方案 1：混合使用（推荐）

```bash
# 1. 使用在线下载安装依赖
python3 volume_cli.py deps install --project your-project

# 2. 使用 S3 上传大模型
python3 upload_your_models.py

# 3. 在线下载小模型
python3 volume_cli.py models download --project your-project
```

#### 方案 2：纯 S3 上传

适用于：

- 完全离线环境
- 模型文件已在本地
- 需要精确控制版本

```python
# 上传所有内容
upload_directory(
    local_dir='/local/project',
    remote_prefix='project',
    models_subdir='/workspace'
)
```

#### 方案 3：纯在线下载

适用于：

- 首次部署
- 模型托管在公开平台
- 需要自动更新

```bash
python3 volume_cli.py setup --project your-project
```

---

## 常见问题

### Q1: S3 上传和在线下载可以混用吗？

**可以**。推荐做法：

- 大模型（>1GB）使用 S3 上传
- 小模型和依赖使用在线下载
- 依赖始终使用在线下载（自动管理版本）

### Q2: 如何选择 models_subdir？

**推荐使用 `/workspace/models`**：

- 符合 RunPod 的标准目录结构
- 与在线下载的路径一致
- 便于统一管理

### Q3: S3 上传后如何在容器中访问？

挂载 Volume 后，文件路径为：

```
S3: workspace/models/speaker-reg/model.pt
容器: /workspace/models/speaker-reg/model.pt
```

### Q4: 在线下载的模型存储在哪里？

- **ModelScope**: `/workspace/models/hub/`
- **HuggingFace**: `/workspace/models/models--/`

### Q5: 如何验证文件是否上传成功？

```bash
# 列出 S3 文件
python3 list_s3_files.py --prefix workspace/models/

# 或在容器中
ls -lh /workspace/models/
```

### Q6: 上传失败怎么办？

检查：

1. S3 配置是否正确（`~/.runpod_s3_config`）
2. Volume 是否在支持 S3 的 datacenter
3. 网络连接是否正常
4. 文件路径是否正确

### Q7: 如何清理测试文件？

```bash
# 清理项目数据
python3 volume_cli.py clean --project your-project --all

# 或手动删除 S3 文件（需要编写脚本）
```

### Q8: 依赖安装很慢怎么办？

```bash
# 使用国内镜像源
python3 volume_cli.py deps install --project your-project \
  --mirror https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 快速参考

### S3 上传命令

```bash
# 上传单个文件
python3 -c "from s3_uploader import upload_file; upload_file('/local/file', 'remote/file')"

# 上传目录
python3 upload_your_models.py

# 列出文件
python3 list_s3_files.py --prefix workspace/models/
```

### 在线下载命令

```bash
# 一键设置
python3 volume_cli.py setup --project PROJECT_NAME

# 安装依赖
python3 volume_cli.py deps install --project PROJECT_NAME

# 下载模型
python3 volume_cli.py models download --project PROJECT_NAME

# 查看状态
python3 volume_cli.py status --project PROJECT_NAME
```

---

## 相关文档

- [S3 上传详细指南](S3_UPLOAD_GUIDE.md)
- [项目配置指南](src/projects/PROJECT_SETUP.md)
- [完整使用指南](COMPLETE_USAGE_GUIDE.md)
- [设置指南](SETUP_GUIDE.md)

---

**最后更新**: 2025-12-14
