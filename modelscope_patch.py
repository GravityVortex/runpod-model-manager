"""
ModelScope AST 兼容性补丁
修复 Python 3.10/3.11 环境下的 ClassDef.type_params AttributeError

问题根源:
- modelscope 1.10.0/1.15.0 的 AST 索引器在扫描时访问 ClassDef.type_params
- type_params 是 Python 3.12 (PEP 695) 引入的属性
- Python 3.10/3.11 的 ast.ClassDef 没有此属性

解决方案:
在导入 modelscope 之前为 AST 节点类添加缺失的属性

相关 Issue:
- https://github.com/modelscope/modelscope/issues/920
- https://github.com/modelscope/modelscope/issues/1072
- https://github.com/modelscope/modelscope/issues/894
"""
import ast
import sys

def patch_ast_for_modelscope():
    """
    为 Python < 3.12 的 AST 节点添加 type_params 属性

    适用场景:
    - Python 3.10, 3.11
    - modelscope 版本: 1.10.0, 1.15.0 及其他受影响版本
    """
    python_version = sys.version_info

    if python_version >= (3, 12):
        # Python 3.12+ 已原生支持，无需 patch
        return

    # 需要添加 type_params 的 AST 节点类型
    node_types_to_patch = [
        'ClassDef',   # 类定义
        'FunctionDef', # 函数定义
        'AsyncFunctionDef'  # 异步函数定义
    ]

    # 使用工厂函数避免闭包问题
    def make_patched_init(original_init):
        """工厂函数：为每个节点类型创建独立的 patched_init"""
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            if not hasattr(self, 'type_params'):
                self.type_params = []
        return patched_init

    patched_count = 0
    for node_type_name in node_types_to_patch:
        node_type = getattr(ast, node_type_name, None)
        if node_type is None:
            continue

        # 检查是否已有 type_params 属性
        if hasattr(node_type, 'type_params'):
            continue

        # 添加 type_params 到 _fields
        if hasattr(node_type, '_fields'):
            original_fields = node_type._fields
            if 'type_params' not in original_fields:
                node_type._fields = original_fields + ('type_params',)

        # 使用工厂函数创建 patched_init
        node_type.__init__ = make_patched_init(node_type.__init__)
        patched_count += 1

    print(f"✅ AST 补丁已应用 (Python {python_version.major}.{python_version.minor}.{python_version.micro}, {patched_count} 个节点类型)")

# 自动执行补丁
if __name__ != "__main__":
    # 作为模块导入时自动应用
    patch_ast_for_modelscope()
else:
    # 直接运行时测试
    print("测试 ModelScope AST 补丁...")
    patch_ast_for_modelscope()

    # 验证补丁
    test_code = """
class TestClass:
    pass
"""
    tree = ast.parse(test_code)
    class_node = tree.body[0]
    assert hasattr(class_node, 'type_params'), "❌ 补丁失败: ClassDef 没有 type_params"
    print(f"✅ 补丁测试通过: ClassDef.type_params = {class_node.type_params}")
