#!/bin/bash
# RunPod Serverless 镜像构建脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RunPod Serverless 镜像构建工具${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查参数
if [ -z "$1" ]; then
    echo -e "${RED}错误: 请提供 Docker Hub 用户名${NC}"
    echo ""
    echo "用法: ./build-serverless.sh <dockerhub-username> [tag]"
    echo ""
    echo "示例:"
    echo "  ./build-serverless.sh myusername"
    echo "  ./build-serverless.sh myusername v1.0"
    exit 1
fi

DOCKERHUB_USERNAME=$1
TAG=${2:-latest}
IMAGE_NAME="${DOCKERHUB_USERNAME}/runpod-model-serverless:${TAG}"

echo ""
echo -e "${YELLOW}📦 镜像名称: ${IMAGE_NAME}${NC}"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 构建镜像
echo -e "${GREEN}🔨 开始构建镜像...${NC}"
echo -e "${YELLOW}注意: 这个过程会下载所有配置的模型，可能需要较长时间${NC}"
echo ""

docker build \
    -f Dockerfile.serverless \
    -t "${IMAGE_NAME}" \
    . \
    --progress=plain

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 镜像构建成功！${NC}"

# 显示镜像信息
echo ""
echo -e "${YELLOW}📊 镜像信息:${NC}"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# 询问是否推送
echo ""
read -p "是否推送镜像到 Docker Hub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 推送镜像到 Docker Hub...${NC}"
    
    docker push "${IMAGE_NAME}"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ 部署准备完成！${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${YELLOW}下一步操作:${NC}"
        echo ""
        echo "1. 登录 RunPod: https://www.runpod.io/console/serverless"
        echo "2. 创建新的 Serverless Endpoint"
        echo "3. Docker 镜像填写: ${IMAGE_NAME}"
        echo "4. 选择合适的 GPU 类型"
        echo "5. Container Disk 设置为镜像大小 + 5GB"
        echo "6. 部署并获取 API Key"
        echo ""
        echo -e "${YELLOW}测试 Endpoint:${NC}"
        echo ""
        echo "curl -X POST https://api.runpod.ai/v2/{endpoint-id}/runsync \\"
        echo "  -H 'Authorization: Bearer YOUR_API_KEY' \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{"
        echo '    "input": {'
        echo '      "task": "vad",'
        echo '      "audio_url": "https://example.com/audio.wav"'
        echo "    }"
        echo "  }'"
        echo ""
    else
        echo -e "${RED}❌ 推送失败，请检查 Docker Hub 登录状态${NC}"
        echo "提示: 运行 'docker login' 登录"
        exit 1
    fi
else
    echo ""
    echo -e "${YELLOW}ℹ️  镜像已构建但未推送${NC}"
    echo "稍后推送请运行: docker push ${IMAGE_NAME}"
fi
