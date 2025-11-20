# 架构设计

## 设计模式

采用**策略模式 + 工厂模式 + 插件化架构**：

```
BaseDownloader (下载器基类)
    ↑
    ├─ ModelScopeDownloader
    ├─ HuggingFaceDownloader
    └─ CustomDownloader
         ↓
    DownloaderFactory (工厂)
         ↓
BaseProject (项目基类)
    ↑
    ├─ SpeakerDiarizationProject
    └─ YourCustomProject
         ↓
    ProjectLoader (统一管理)
         ↓
    download_models.py (调度器)
```

## 核心组件

### 1. BaseDownloader (下载器基类)

```python
class BaseDownloader(ABC):
    def is_available(self) -> bool: ...
    def download(self, model_id: str) -> bool: ...
    def check_model_exists(self, model_id: str) -> bool: ...
```

**职责**: 定义下载器接口规范

### 2. 具体下载器类

```python
class ModelScopeDownloader(BaseDownloader):
    def download(self, model_id: str) -> bool:
        # ModelScope 下载逻辑
        ...

class HuggingFaceDownloader(BaseDownloader):
    def download(self, model_id: str) -> bool:
        # HuggingFace 下载逻辑
        ...
```

**职责**: 实现各自渠道的下载逻辑

### 3. DownloaderFactory (工厂类)

```python
class DownloaderFactory:
    _downloaders = {
        'modelscope': ModelScopeDownloader,
        'huggingface': HuggingFaceDownloader,
    }
    
    @classmethod
    def get_downloader(cls, source, model_cache): ...
```

**职责**: 
- 注册所有下载器
- 根据源名称创建下载器实例

### 4. BaseProject (项目基类)

```python
class BaseProject(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def models(self) -> Dict[str, List[str]]: ...
    
    @abstractmethod
    def download_models(self, model_cache: str): ...
```

**职责**: 定义项目接口规范

### 5. 具体项目类

```python
class SpeakerDiarizationProject(BaseProject):
    def download_models(self, model_cache: str):
        for model_id, source in self.get_all_models():
            downloader = DownloaderFactory.get_downloader(source, model_cache)
            if not downloader.check_model_exists(model_id):
                downloader.download(model_id)
```

**职责**: 
- 定义项目模型列表
- 实现自己的下载逻辑

### 6. ProjectLoader (统一加载器)

```python
class ProjectLoader:
    PROJECTS = [
        SpeakerDiarizationProject(),
    ]
    
    @classmethod
    def get_all_projects(cls): ...
```

**职责**: 
- 注册所有项目
- 提供项目查询接口

### 7. download_models.py (调度器)

**职责**:
- 检测 RunPod Volume
- 调度各项目执行下载
- 环境配置

## 工作流程

```
1. 创建项目配置
   └─ 继承 BaseProject
   └─ 实现 name、models 和 download_models

2. 注册项目
   └─ 在 ProjectLoader.PROJECTS 添加实例

3. 运行下载
   └─ python download_models.py --all
   └─ ProjectLoader 获取所有项目
   └─ 逐个调用 project.download_models()
   └─ 项目内部使用 DownloaderFactory 获取下载器
   └─ 下载器执行实际下载

4. 其他项目使用
   └─ 挂载同一个 Volume
   └─ 直接加载模型
```

## 扩展性

### 添加新项目

1. 在 `projects/` 创建 `new_project.py`
2. 继承 `BaseProject`，实现抽象方法
3. 在 `projects/loader.py` 的 `ProjectLoader` 注册

```python
from .base import BaseProject
from downloaders import DownloaderFactory

class NewProject(BaseProject):
    @property
    def name(self):
        return "new-project"
    
    @property
    def models(self):
        return {'modelscope': [...]}
    
    def download_models(self, model_cache: str):
        # 使用工厂获取下载器
        for model_id, source in self.get_all_models():
            downloader = DownloaderFactory.get_downloader(source, model_cache)
            ...
```

### 添加新的下载源

1. 创建下载器类 (`downloaders/custom_downloader.py`)：

```python
from .base_downloader import BaseDownloader

class CustomDownloader(BaseDownloader):
    def is_available(self) -> bool:
        return True
    
    def download(self, model_id: str) -> bool:
        # 自定义下载逻辑
        ...
```

2. 在工厂注册（修改 `downloaders/factory.py`）：

```python
from .custom_downloader import CustomDownloader

class DownloaderFactory:
    _downloaders = {
        'modelscope': ModelScopeDownloader,
        'huggingface': HuggingFaceDownloader,
        'custom': CustomDownloader,  # 新增
    }
```

3. 在项目中使用：

```python
@property
def models(self):
    return {
        'custom': ['model-id'],
    }
```

## 设计优势

- ✅ **高内聚低耦合**: 下载器、项目、调度器各司其职
- ✅ **单一职责**: 每个类只负责一件事
- ✅ **开放封闭**: 对扩展开放，对修改封闭
- ✅ **依赖倒置**: 依赖抽象而非具体实现
- ✅ **易于测试**: 各组件可独立测试
- ✅ **易于扩展**: 新增下载源只需添加类，无需修改现有代码
