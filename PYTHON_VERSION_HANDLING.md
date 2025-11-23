# Python 版本自动检测和处理

## 功能说明

CLI 会自动检测当前 Python 版本与项目要求的版本是否匹配，并提供智能处理。

---

## 自动检测流程

```bash
python3 volume_cli.py deps install --project speaker-diarization
```

### 场景1：版本匹配 ✅

```
============================================================
🔧 依赖管理（增量）
============================================================

📦 项目: speaker-diarization
📂 Volume: /workspace
🐍 需要 Python: 3.10
🐍 当前 Python: 3.10
📊 定义依赖数: 13
✅ Python 版本匹配

# 继续安装...
```

### 场景2：版本不匹配（已安装需要的版本）✅

```
============================================================
🔧 依赖管理（增量）
============================================================

📦 项目: speaker-diarization
📂 Volume: /workspace
🐍 需要 Python: 3.10
🐍 当前 Python: 3.11
📊 定义依赖数: 13

⚠️  Python 版本不匹配！
   需要: 3.10
   当前: 3.11

✅ 检测到系统已安装 Python 3.10
   使用 python3.10 重新运行...

# 自动切换到 Python 3.10 继续安装
```

### 场景3：版本不匹配（自动安装）✅

```
============================================================
🔧 依赖管理（增量）
============================================================

📦 项目: speaker-diarization
📂 Volume: /workspace
🐍 需要 Python: 3.10
🐍 当前 Python: 3.11
📊 定义依赖数: 13

⚠️  Python 版本不匹配！
   需要: 3.10
   当前: 3.11

🔧 系统未安装 Python 3.10
📥 开始自动安装...

[1/3] 更新包列表...
      ✓ 完成
[2/3] 安装 Python 3.10...
      ✓ 安装完成
[3/3] 验证安装...
      ✓ Python 3.10.12

✅ Python 3.10 安装成功！
   使用 python3.10 重新运行...

# 自动切换到 Python 3.10 继续
```

---

## 自动化流程

系统会自动处理 Python 版本问题，无需用户干预：

1. **检测版本**：自动检测当前 Python 版本
2. **查找已安装版本**：检查系统是否已安装需要的版本
3. **自动切换**：如果已安装，自动切换到正确版本
4. **自动安装**：如果未安装，自动安装需要的版本
5. **验证并继续**：验证安装后自动继续

**优势**：
- ✅ 零交互，完全自动化
- ✅ 智能检测，自动适配
- ✅ 详细日志，过程透明
- ✅ 错误处理，明确提示

---

## 实际操作示例

### 示例1：在标准 PyTorch Pod 中（Python 3.10）

```bash
# Pod 系统 Python
python3 --version
# Python 3.10.12

# 项目配置
python_version = '3.10'

# 安装（自动匹配）
python3 volume_cli.py deps install --project speaker-diarization
# ✅ Python 版本匹配
# 安装到: /workspace/python-deps/py3.10/speaker-diarization/
```

### 示例2：在新版 Pod 中（Python 3.11）

```bash
# Pod 系统 Python
python3 --version
# Python 3.11.5

# 项目配置
python_version = '3.10'

# 安装（检测到不匹配）
python3 volume_cli.py deps install --project speaker-diarization
# ⚠️  Python 版本不匹配！

# 选项A：安装 Python 3.10
apt-get update && apt-get install -y python3.10 python3.10-pip
python3.10 volume_cli.py deps install --project speaker-diarization
# ✅ 使用 3.10 安装

# 选项B：修改项目配置使用 3.11
vim projects/speaker-diarization/config.py
# python_version = '3.11'
python3 volume_cli.py deps install --project speaker-diarization
# ✅ 使用 3.11 安装
```

---

## 版本隔离原理

### Volume 目录结构

```
/workspace/python-deps/
├── py3.10/              # Python 3.10 的依赖
│   └── speaker-diarization/
│       ├── torch/       # Python 3.10 编译的
│       └── ...
└── py3.11/              # Python 3.11 的依赖
    └── text-generation/
        ├── torch/       # Python 3.11 编译的
        └── ...
```

### 为什么必须版本匹配？

Python 包的二进制扩展（.so, .pyd）是针对特定 Python 版本编译的：

```python
# Python 3.10 安装的包
torch/_C.cpython-310-x86_64-linux-gnu.so

# Python 3.11 无法使用，会报错：
ImportError: ... undefined symbol: PyUnicode_DecodeUTF8
```

---

## 最佳实践

### 1. 保持版本一致

```python
# 项目配置
python_version = '3.10'

# Pod 安装时
python3.10 volume_cli.py deps install --project my-project

# 项目 Dockerfile
FROM python:3.10
ENV PYTHONPATH=/runpod-volume/python-deps/py3.10/my-project:$PYTHONPATH
```

### 2. 明确记录版本

```python
# projects/my_project/config.py
class MyProject(BaseProject):
    @property
    def python_version(self):
        return '3.10'  # 明确指定，不要用变量
```

### 3. 选择合适的 Pod 模板

创建临时 Pod 时，选择与项目匹配的 Python 版本：

| Pod 模板 | Python 版本 | 适用项目 |
|----------|-------------|----------|
| PyTorch 2.1 | 3.10 | Python 3.10 项目 |
| PyTorch 2.4 | 3.11 | Python 3.11 项目 |
| TensorFlow 2.15 | 3.11 | Python 3.11 项目 |

---

## 常见问题

### Q: 能不能自动安装需要的 Python 版本？

A: 不建议。理由：
1. 需要 root 权限
2. 可能影响系统稳定性
3. 安装耗时较长

建议：选择正确的 Pod 模板或手动安装。

### Q: 如果忘记当前用的什么版本怎么办？

A: 查看已安装的依赖目录：

```bash
ls /workspace/python-deps/
# 输出: py3.10  py3.11

# 查看某个项目
ls /workspace/python-deps/*/speaker-diarization
# 输出: /workspace/python-deps/py3.10/speaker-diarization
```

### Q: 可以同时支持多个 Python 版本吗？

A: 可以！每个项目独立配置：

```python
# 项目A使用 3.10
class ProjectA(BaseProject):
    python_version = '3.10'

# 项目B使用 3.11
class ProjectB(BaseProject):
    python_version = '3.11'
```

分别安装：
```bash
python3.10 volume_cli.py deps install --project project-a
python3.11 volume_cli.py deps install --project project-b
```

---

## 错误处理

### 错误：命令找不到

```bash
python3.10 volume_cli.py deps install --project my-project
# bash: python3.10: command not found
```

**解决**：
```bash
# 检查可用版本
ls /usr/bin/python*

# 安装需要的版本
apt-get update
apt-get install -y python3.10 python3.10-pip
```

### 错误：版本仍然不对

```bash
python3.10 --version
# Python 3.10.12

python3.10 volume_cli.py deps install --project my-project
# 🐍 当前 Python: 3.13  ← 为什么？
```

**原因**：可能有虚拟环境或别名

**解决**：
```bash
# 使用绝对路径
/usr/bin/python3.10 volume_cli.py deps install --project my-project
```

---

## 总结

✅ **自动检测**：CLI 自动检测版本匹配  
✅ **智能提示**：给出3种解决方案  
✅ **交互确认**：避免误操作  
✅ **版本隔离**：不同版本的包互不干扰  

🎯 **核心：让用户明确知道版本问题，而不是默默出错！**
