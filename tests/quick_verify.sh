#!/bin/bash
# 快速验证脚本

echo "=========================================="
echo "🧪 快速验证一站式部署功能"
echo "=========================================="
echo ""

# 1. 运行单元测试
echo "1️⃣  运行单元测试..."
python3 tests/test_deploy.py
if [ $? -ne 0 ]; then
    echo "❌ 单元测试失败"
    exit 1
fi
echo ""

# 2. 测试 deploy 命令帮助
echo "2️⃣  测试 deploy 命令帮助..."
python3 volume_cli.py deploy --help > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ deploy 命令帮助失败"
    exit 1
fi
echo "✅ deploy 命令帮助正常"
echo ""

# 3. 测试 deploy 命令（跳过上传）
echo "3️⃣  测试 deploy 命令（跳过上传）..."
python3 volume_cli.py deploy --project speaker-diarization --skip-upload > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ deploy 命令执行失败"
    exit 1
fi
echo "✅ deploy 命令执行正常"
echo ""

# 4. 测试项目上传脚本帮助
echo "4️⃣  测试项目上传脚本帮助..."
python3 src/projects/speaker_diarization/upload_models.py --help > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 上传脚本帮助失败"
    exit 1
fi
echo "✅ 上传脚本帮助正常"
echo ""

# 5. 测试上传脚本错误处理
echo "5️⃣  测试上传脚本错误处理..."
python3 src/projects/speaker_diarization/upload_models.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "❌ 应该返回错误码"
    exit 1
fi
echo "✅ 错误处理正常"
echo ""

echo "=========================================="
echo "✅ 所有验证通过！"
echo "=========================================="

