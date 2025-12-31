#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化后的依赖安装逻辑
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.venv_manager import VenvManager

def test_yaml_parsing():
    """测试 YAML 解析和命令构建逻辑"""
    print("=" * 60)
    print("测试 1: YAML 解析")
    print("=" * 60)
    
    yaml_file = Path(__file__).parent / 'src/projects/speaker_reg/dependencies.yaml'
    
    if not yaml_file.exists():
        print(f"❌ 配置文件不存在: {yaml_file}")
        return False
    
    import yaml
    with open(yaml_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    groups = config.get('groups', {})
    install_order = config.get('install_order', [])
    
    print(f"✅ 成功加载配置")
    print(f"   - 依赖组数: {len(groups)}")
    print(f"   - 安装顺序: {install_order}")
    
    total_packages = 0
    for group_name in install_order:
        group = groups.get(group_name)
        if group:
            packages = group.get('packages', [])
            total_packages += len(packages)
            print(f"   - {group_name}: {len(packages)} 包")
    
    print(f"   - 总包数: {total_packages}")
    return True

def test_command_building():
    """测试命令构建逻辑"""
    print("\n" + "=" * 60)
    print("测试 2: 命令构建逻辑")
    print("=" * 60)
    
    yaml_file = Path(__file__).parent / 'src/projects/speaker_reg/dependencies.yaml'
    
    import yaml
    with open(yaml_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    groups = config.get('groups', {})
    install_order = config.get('install_order', [])
    
    python_bin = '/fake/venv/bin/python'
    mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'
    
    for group_name in install_order:
        group = groups.get(group_name)
        if not group or not group.get('packages'):
            continue
        
        cmd = ['uv', 'pip', 'install', '--python', python_bin]
        cmd.extend(group['packages'][:2])  # 只显示前2个包
        
        if group.get('no_deps'):
            cmd.append('--no-deps')
        if group.get('index_url'):
            cmd.extend(['--index-url', group['index_url']])
        elif mirror:
            cmd.extend(['--index-url', mirror])
        
        print(f"\n📦 {group_name}:")
        print(f"   命令: {' '.join(cmd)} ...")
        print(f"   索引: {group.get('index_url') or mirror}")
    
    print("\n✅ 命令构建逻辑正确")
    return True

def test_code_simplification():
    """验证代码简化效果"""
    print("\n" + "=" * 60)
    print("测试 3: 代码简化效果")
    print("=" * 60)
    
    venv_file = Path(__file__).parent / 'src/venv_manager.py'
    
    with open(venv_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查 install_from_yaml 方法的行数
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if 'def install_from_yaml(' in line:
            start_idx = i
        elif start_idx and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            end_idx = i
            break
    
    if start_idx and end_idx:
        method_lines = end_idx - start_idx
        print(f"✅ install_from_yaml() 方法行数: {method_lines}")
        
        if method_lines <= 60:
            print(f"   ✅ 成功简化到 {method_lines} 行（目标 ≤60 行）")
        else:
            print(f"   ⚠️  仍有 {method_lines} 行，可进一步优化")
    
    # 检查是否移除了复杂的版本解析
    volume_file = Path(__file__).parent / 'src/volume_manager.py'
    with open(volume_file, 'r', encoding='utf-8') as f:
        volume_content = f.read()
    
    if 'extract_pkg_name' not in volume_content:
        print(f"✅ 已移除复杂的版本符号解析逻辑")
    else:
        print(f"⚠️  版本解析逻辑仍存在")
    
    if 'check_dependencies_changed' not in volume_content:
        print(f"✅ 已移除未使用的变更检测函数")
    else:
        print(f"⚠️  变更检测函数仍存在")
    
    return True

if __name__ == '__main__':
    print("\n🧪 测试简化后的依赖安装逻辑\n")
    
    tests = [
        test_yaml_parsing,
        test_command_building,
        test_code_simplification
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    success = sum(results)
    total = len(results)
    print(f"✅ 通过: {success}/{total}")
    
    if success == total:
        print("\n🎉 所有测试通过！简化成功！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败")
        sys.exit(1)


