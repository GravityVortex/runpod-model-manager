# ModelScope AST 索引问题修复指南

> **快速解决方案**：本项目已自动集成修复功能，依赖安装时会自动修复。如需手动修复已安装的依赖，参见[手动修复](#手动修复已安装的依赖)。

---

## 🚨 问题现象

在 RunPod Serverless 环境中使用 ModelScope 时遇到：

```python
AttributeError: 'ClassDef' object has no attribute 'type_params'
```

**原因**：Python 3.10/3.11 环境下，ModelScope 的 AST 扫描访问了不存在的 `type_params` 属性（Python 3.12+ 特性）。

---

## ✅ 推荐方案：修改版本发布日期

**原理**：利用 ModelScope 自身的版本检测机制
- 将 `modelscope/version.py` 中的 `__release_datetime__` 改为过去的日期
- ModelScope 认为这是正式发布版本 → **自动跳过 AST 扫描**

**优势**：
- ✅ 利用官方机制，不破坏代码逻辑
- ✅ 简单可靠，只改一个字符串值
- ✅ 本项目已自动集成

---

## 🎯 解决方案对比

| 方案 | 可靠性 | 说明 |
|------|--------|------|
| **修改版本日期** ⭐ | ✅ 完美 | 利用官方机制，本项目已自动集成 |
| AST 补丁 | ⚠️ 部分有效 | 只影响 `ast`，不影响 `gast` |
| ~~环境变量~~ | ❌ 不生效 | ModelScope 不支持 |

---

## 🚀 使用方法

### 方法 1：自动修复（推荐）✅

**本项目已集成**，安装依赖时自动修复，无需手动操作：

```bash
# 使用项目工具安装依赖时，会自动修复
python volume_manager.py install --project speaker-diarization --config dependencies.yaml
```

输出示例：
```
✅ 依赖安装完成！

🛠️  后处理: 修复 ModelScope 版本检测...
   ✅ ModelScope 已标记为正式版本（跳过 AST 扫描）
   ℹ️  原理：发布日期在过去 → 正式版本 → 跳过 AST 扫描
```

---

### 方法 2：手动修复已安装的依赖

#### 使用修复脚本（推荐）

```bash
# 在 RunPod Pod 中运行
python fix_modelscope_release.py --project speaker-diarization --python 3.10
```

#### 直接编辑文件（最快）

```bash
# 1. 找到文件
vi /workspace/python-deps/py3.10/speaker-diarization/modelscope/version.py

# 2. 找到这一行（大约在第 5-10 行）：
#    __release_datetime__ = '2025-12-31 23:59:59'  # 或其他未来日期

# 3. 改成：
#    __release_datetime__ = '2024-01-01 00:00:00'

# 4. 保存退出
```

---

## ✅ 验证修复

```bash
# 检查修改是否生效
grep "__release_datetime__" /workspace/python-deps/py3.10/speaker-diarization/modelscope/version.py
```

**重启后日志应显示**：不再有 `AST-Scanning` 和 `type_params` 错误

---

## 💡 常见问题

**Q: 修改版本日期安全吗？**  
A: 完全安全。利用 ModelScope 自身的版本检测机制，不破坏代码逻辑。

**Q: 会影响功能吗？**  
A: 不会。AST 索引仅用于开发时代码索引，不影响模型推理。

**Q: 需要每次都修复吗？**  
A: 只需一次。修改后会保留在 Volume 中，除非重新安装 ModelScope。

**Q: 为什么不用环境变量？**  
A: ModelScope 没有官方的禁用环境变量。

---

## 📚 参考资料

- [ModelScope Issues #920](https://github.com/modelscope/modelscope/issues/920)
- [PEP 695 – Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [modelscope/utils/ast_utils.py](https://github.com/modelscope/modelscope/blob/master/modelscope/utils/ast_utils.py)

---

**2025-11-23** | GravityVortex Team
