#!/bin/bash

# Build script for K8sGPT AI Analyzer containers
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${REGISTRY:-localhost:5000}"
IMAGE_NAME="${IMAGE_NAME:-k8sgpt-ai-analyzer}"
TAG="${TAG:-latest}"

echo -e "${BLUE}🚀 Building K8sGPT AI Analyzer containers${NC}"
echo -e "${BLUE}Registry: ${REGISTRY}${NC}"
echo -e "${BLUE}Image: ${IMAGE_NAME}${NC}"
echo -e "${BLUE}Tag: ${TAG}${NC}"

# Build WebUI container
echo -e "${YELLOW}📦 Building WebUI container...${NC}"
docker build -f Dockerfile -t "${REGISTRY}/${IMAGE_NAME}/webui:${TAG}" ../../../ai

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ WebUI container built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build WebUI container${NC}"
    exit 1
fi

# Build Ollama container with pre-loaded models
echo -e "${YELLOW}🤖 Building Ollama container...${NC}"
docker build -f Dockerfile.ollama -t "${REGISTRY}/${IMAGE_NAME}/ollama:${TAG}" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Ollama container built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Ollama container${NC}"
    exit 1
fi

# Push containers if registry is not localhost
if [[ "$REGISTRY" != localhost* ]]; then
    echo -e "${YELLOW}📤 Pushing containers to registry...${NC}"

    echo -e "${BLUE}Pushing WebUI container...${NC}"
    docker push "${REGISTRY}/${IMAGE_NAME}/webui:${TAG}"

    echo -e "${BLUE}Pushing Ollama container...${NC}"
    docker push "${REGISTRY}/${IMAGE_NAME}/ollama:${TAG}"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ All containers pushed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to push containers${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}🎉 All containers built successfully!${NC}"
echo -e "${BLUE}WebUI Image: ${REGISTRY}/${IMAGE_NAME}/webui:${TAG}${NC}"
echo -e "${BLUE}Ollama Image: ${REGISTRY}/${IMAGE_NAME}/ollama:${TAG}${NC}"

# Show disk usage
echo -e "${YELLOW}💾 Container images:${NC}"
docker images | grep "${IMAGE_NAME}"