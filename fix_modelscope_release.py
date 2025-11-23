#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 Volume 中已安装的 ModelScope 版本检测
适用于已经安装过依赖的情况
"""
import os
import sys
import re
from pathlib import Path

def find_deps_dir():
    """查找依赖目录"""
    candidates = [
        '/workspace/python-deps',
        '/runpod-volume/python-deps',
        'D:/PycharmProjects/runpod-model-manager/volume/python-deps'  # 本地测试
    ]
    for base in candidates:
        if os.path.exists(base):
            return base
    return None

def fix_modelscope(project_name, python_version='3.10'):
    """修复 ModelScope 版本"""
    deps_base = find_deps_dir()
    if not deps_base:
        print("❌ 未找到依赖目录")
        return False
    
    version_file = Path(deps_base) / f'py{python_version}' / project_name / 'modelscope' / 'version.py'
    
    if not version_file.exists():
        print(f"❌ 未找到 ModelScope: {version_file}")
        return False
    
    print(f"📝 修改文件: {version_file}")
    
    # 备份
    backup = str(version_file) + '.backup'
    if not Path(backup).exists():
        import shutil
        shutil.copy2(version_file, backup)
        print(f"   ✅ 已备份: {backup}")
    
    # 修改
    content = version_file.read_text(encoding='utf-8')
    
    if '# PATCHED' in content:
        print("   ℹ️  已修复，无需重复操作")
        # 即使已修复，也检查并删除 AST 缓存
        _delete_ast_cache(deps_base)
        return True
    
    pattern = r"__release_datetime__\s*=\s*['\"].*?['\"]"
    replacement = "__release_datetime__ = '2024-01-01 00:00:00'  # PATCHED"
    new_content = re.sub(pattern, replacement, content)
    
    if new_content == content:
        print("   ❌ 未能匹配到 __release_datetime__")
        return False
    
    version_file.write_text(new_content, encoding='utf-8')
    print("   ✅ 修复完成")
    
    # 🔥 关键：删除 AST 索引缓存
    _delete_ast_cache(deps_base)
    
    return True

def _delete_ast_cache(deps_base):
    """删除 AST 索引缓存"""
    import shutil
    
    # 尝试多个可能的 Volume 根目录
    volume_candidates = [
        Path(deps_base).parent.parent / 'models' / 'ast_indexer',  # /xxx/python-deps -> /xxx/models/ast_indexer
        Path('/runpod-volume') / 'models' / 'ast_indexer',
        Path('/workspace') / 'models' / 'ast_indexer',
    ]
    
    for ast_cache in volume_candidates:
        if ast_cache.exists():
            print(f"\n🗑️  删除旧的 AST 索引缓存: {ast_cache}")
            try:
                shutil.rmtree(ast_cache)
                print(f"   ✅ AST 缓存已删除")
                return True
            except Exception as e:
                print(f"   ⚠️  删除缓存失败: {e}")
                return False
    
    print(f"\n   ℹ️  未找到 AST 索引缓存（可能尚未生成）")
    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='修复 ModelScope 版本检测')
    parser.add_argument('--project', required=True, help='项目名称')
    parser.add_argument('--python', default='3.10', help='Python 版本')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🛠️  修复 ModelScope 版本检测（标准方法）")
    print("=" * 70)
    
    if fix_modelscope(args.project, args.python):
        print("\n✅ 修复完成！")
        print("\n下一步：")
        print("  1. 重启 RunPod Serverless Endpoint")
        print("  2. 查看日志确认不再有 AST 扫描")
    else:
        print("\n❌ 修复失败")
        sys.exit(1)
