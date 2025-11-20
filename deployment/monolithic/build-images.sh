#!/bin/bash

# ============================================================================
# Build Monolithic Mode Docker Images
# ============================================================================
# Builds base image and monolithic application images for local deployment
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKER_REGISTRY:-arcanacloud}"
VERSION="${VERSION:-latest}"
PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building Monolithic Mode Images${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Registry: ${REGISTRY}"
echo -e "  Version: ${VERSION}"
echo -e "  Python: ${PYTHON_VERSION}"
echo -e "  Build Date: ${BUILD_DATE}"
echo -e "  Git Commit: ${GIT_COMMIT}"
echo ""

# Step 1: Build base image
echo -e "${YELLOW}Step 1: Building Base Image...${NC}"
echo -e "${BLUE}→${NC} docker build -f docker/Dockerfile.base -t ${REGISTRY}/arcana-cloud-base:${VERSION}"
docker build \
    -f docker/Dockerfile.base \
    -t ${REGISTRY}/arcana-cloud-base:${VERSION} \
    --build-arg PYTHON_VERSION=${PYTHON_VERSION} \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${GIT_COMMIT}" \
    --build-arg VERSION="${VERSION}" \
    .

echo -e "${GREEN}✓${NC} Base image built successfully"
echo ""

# Tag as latest
docker tag ${REGISTRY}/arcana-cloud-base:${VERSION} ${REGISTRY}/arcana-cloud-base:latest
echo -e "${GREEN}✓${NC} Tagged as ${REGISTRY}/arcana-cloud-base:latest"
echo ""

# Step 2: Build monolithic image
echo -e "${YELLOW}Step 2: Building Monolithic Image...${NC}"
echo -e "${BLUE}→${NC} docker build -f docker/Dockerfile.monolithic -t ${REGISTRY}/arcana-cloud-monolithic:${VERSION}"
docker build \
    -f docker/Dockerfile.monolithic \
    -t ${REGISTRY}/arcana-cloud-monolithic:${VERSION} \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${GIT_COMMIT}" \
    --build-arg VERSION="${VERSION}" \
    .

echo -e "${GREEN}✓${NC} Monolithic image built successfully"
echo ""

# Tag as latest
docker tag ${REGISTRY}/arcana-cloud-monolithic:${VERSION} ${REGISTRY}/arcana-cloud-monolithic:latest
echo -e "${GREEN}✓${NC} Tagged as ${REGISTRY}/arcana-cloud-monolithic:latest"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Images built:${NC}"
docker images | grep -E "${REGISTRY}/(arcana-cloud-base|arcana-cloud-monolithic)" | head -4
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Start services: ${BLUE}docker-compose up -d${NC}"
echo -e "  2. Check status:   ${BLUE}docker-compose ps${NC}"
echo -e "  3. View logs:      ${BLUE}docker-compose logs -f${NC}"
echo ""
