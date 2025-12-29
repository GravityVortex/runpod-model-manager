# S3 上传工具使用指南

## 功能概述

`src/s3_uploader.py` 提供了可在代码中直接调用的 S3 上传方法，支持：

- 上传单个文件
- 上传整个目录
- 详细的操作日志输出
- 上传进度显示

## 快速开始

### 1. 上传单个文件

```python
from s3_uploader import upload_file

# 基本用法（使用默认子目录 /workspace/models）
success = upload_file(
    local_path='/path/to/model.bin',
    remote_key='my-model/model.bin'
)

if success:
    print("上传成功！")
```

**结果路径**：`s3://volume_id/workspace/models/my-model/model.bin`

### 2. 自定义子目录

```python
# 上传到自定义子目录
success = upload_file(
    local_path='/path/to/model.bin',
    remote_key='bert-base/model.bin',
    models_subdir='/workspace/cache'
)
```

**结果路径**：`s3://volume_id/workspace/cache/bert-base/model.bin`

### 3. 上传整个目录

```python
from s3_uploader import upload_directory

# 上传目录（不包含父目录名）
result = upload_directory(
    local_dir='/local/bert-base',
    remote_prefix='bert-base',
    models_subdir='/workspace/models'
)

print(f"上传完成: {result['success']}/{result['total']} 个文件")
```

**目录结构**：

```
/local/bert-base/
├── config.json
├── model.bin
└── tokenizer/
    └── vocab.txt
```

**上传结果**：

```
s3://volume_id/workspace/models/bert-base/config.json
s3://volume_id/workspace/models/bert-base/model.bin
s3://volume_id/workspace/models/bert-base/tokenizer/vocab.txt
```

### 4. 包含父目录名

```python
# 上传目录（包含父目录名）
result = upload_directory(
    local_dir='/local/bert-base',
    remote_prefix='v1',
    models_subdir='/workspace/models',
    include_parent_dir=True
)
```

**上传结果**：

```
s3://volume_id/workspace/models/v1/bert-base/config.json
s3://volume_id/workspace/models/v1/bert-base/model.bin
s3://volume_id/workspace/models/v1/bert-base/tokenizer/vocab.txt
```

## 参数说明

### upload_file()

| 参数            | 类型 | 默认值              | 说明                           |
| --------------- | ---- | ------------------- | ------------------------------ |
| `local_path`    | str  | 必填                | 本地文件路径                   |
| `remote_key`    | str  | None                | 远程对象键（不填则使用文件名） |
| `models_subdir` | str  | `/workspace/models` | 子目录前缀                     |
| `profile`       | str  | `runpods3`          | S3 配置 profile                |
| `verbose`       | bool | True                | 是否输出详细日志               |

**返回值**：`bool` - 上传是否成功

### upload_directory()

| 参数                 | 类型 | 默认值              | 说明                     |
| -------------------- | ---- | ------------------- | ------------------------ |
| `local_dir`          | str  | 必填                | 本地目录路径             |
| `remote_prefix`      | str  | None                | 远程前缀（作为文件夹名） |
| `models_subdir`      | str  | `/workspace/models` | 子目录前缀               |
| `include_parent_dir` | bool | False               | 是否包含父目录名         |
| `profile`            | str  | `runpods3`          | S3 配置 profile          |
| `verbose`            | bool | True                | 是否输出详细日志         |

**返回值**：`dict` - `{'total': int, 'success': int, 'failed': int}`

## 路径组成规则

```
最终 S3 路径 = models_subdir + remote_key/remote_prefix + 文件相对路径
```

### 示例

**单文件上传**：

- `models_subdir` = `/workspace/models`
- `remote_key` = `bert-base/model.bin`
- **最终路径** = `/workspace/models/bert-base/model.bin`

**目录上传（不包含父目录）**：

- `models_subdir` = `/workspace/models`
- `remote_prefix` = `bert-base`
- 文件相对路径 = `config.json`
- **最终路径** = `/workspace/models/bert-base/config.json`

**目录上传（包含父目录）**：

- `models_subdir` = `/workspace/models`
- `remote_prefix` = `v1`
- 父目录名 = `bert-base`
- 文件相对路径 = `config.json`
- **最终路径** = `/workspace/models/v1/bert-base/config.json`

## 日志输出示例

### 单文件上传

```
📂 本地文件: /path/to/model.bin
   大小: 1.23 GB

🔧 S3 配置
   Endpoint: https://s3api-us-ca-2.runpod.io/
   Region: us-ca-2
   Volume: your_volume_id

📍 目标路径: workspace/models/bert-base/model.bin
   完整 S3 路径: s3://your_volume_id/workspace/models/bert-base/model.bin

📤 开始上传...
   进度: 25.0% (314.57 MB / 1.23 GB) - 52.43 MB/s
   进度: 50.0% (629.15 MB / 1.23 GB) - 51.28 MB/s
   进度: 75.0% (943.72 MB / 1.23 GB) - 50.95 MB/s
   进度: 100.0% (1.23 GB / 1.23 GB) - 50.67 MB/s

✅ 上传成功！
   耗时: 24.8 秒
   平均速度: 50.67 MB/s
```

### 目录上传

```
📂 本地目录: /local/bert-base
   文件数量: 5
   总大小: 2.45 GB

🔧 S3 配置
   Endpoint: https://s3api-us-ca-2.runpod.io/
   Volume: your_volume_id

📤 开始上传 5 个文件...

[1/5] config.json
   → s3://your_volume_id/workspace/models/bert-base/config.json
   ✅ 成功

[2/5] model.bin
   → s3://your_volume_id/workspace/models/bert-base/model.bin
   ✅ 成功

...

============================================================
📊 上传完成
   总计: 5 个文件
   成功: 5 个
   失败: 0 个
```

## 命令行测试

```bash
# 使用默认子目录
python3 test_upload_download.py

# 指定自定义子目录
python3 test_upload_download.py --models-subdir /workspace/models/custom

# 不使用子目录前缀
python3 test_upload_download.py --models-subdir ""

# 上传指定文件
python3 test_upload_download.py --local-file /path/to/file.bin --models-subdir /workspace/models
```

## 常见问题

### Q: models_subdir 和 remote_prefix 有什么区别？

- **models_subdir**：固定的基础路径前缀，对应 RunPod Volume 挂载后的实际路径，通常为 `/workspace/models`
- **remote_prefix**：灵活的业务路径，用于区分不同的模型、版本或项目

### Q: 如何关闭详细日志？

```python
success = upload_file(
    local_path='/path/to/file.bin',
    remote_key='model.bin',
    verbose=False  # 关闭日志
)
```

### Q: 上传失败如何处理？

函数会返回 `False` 并在日志中显示错误信息。建议检查：

1. S3 配置是否正确（`~/.runpod_s3_config`）
2. 网络连接是否正常
3. Volume ID 和 datacenter 是否匹配

### Q: 可以上传到根目录吗？

可以，将 `models_subdir` 设置为空字符串：

```python
success = upload_file(
    local_path='/path/to/file.bin',
    remote_key='file.bin',
    models_subdir=''  # 上传到根目录
)
# 结果：s3://volume_id/file.bin
```

## 完整示例

```python
#!/usr/bin/env python3
from s3_uploader import upload_file, upload_directory

def main():
    # 1. 上传单个模型文件
    print("=== 上传单个文件 ===")
    success = upload_file(
        local_path='/local/models/bert-base-uncased/pytorch_model.bin',
        remote_key='bert-base-uncased/pytorch_model.bin',
        models_subdir='/workspace/models'
    )

    if not success:
        print("上传失败！")
        return

    # 2. 上传整个模型目录
    print("\n=== 上传整个目录 ===")
    result = upload_directory(
        local_dir='/local/models/bert-base-uncased',
        remote_prefix='bert-base-uncased',
        models_subdir='/workspace/models',
        include_parent_dir=False
    )

    print(f"\n总结: 成功 {result['success']}/{result['total']} 个文件")

    if result['failed'] > 0:
        print(f"警告: {result['failed']} 个文件上传失败")

if __name__ == '__main__':
    main()
```







