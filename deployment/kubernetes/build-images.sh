#!/bin/bash

# ============================================================================
# Docker Image Build Script for Kubernetes
# ============================================================================
# Builds all Docker images for the layered architecture
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKER_REGISTRY:-arcanacloud}"
VERSION="${VERSION:-latest}"
BUILD_ARGS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            BUILD_ARGS="--no-cache"
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building Docker Images${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Registry: ${GREEN}${REGISTRY}${NC}"
echo -e "Version:  ${GREEN}${VERSION}${NC}"
echo ""

# Function to build an image
build_image() {
    local layer=$1
    local dockerfile=$2
    local tag="${REGISTRY}/arcana-cloud-${layer}:${VERSION}"

    echo -e "${BLUE}==>${NC} Building ${GREEN}${layer}${NC} layer..."

    if docker build ${BUILD_ARGS} \
        -t "${tag}" \
        -f "${dockerfile}" \
        .; then
        echo -e "${GREEN}✓${NC} Successfully built ${tag}"

        # Tag as latest
        docker tag "${tag}" "${REGISTRY}/arcana-cloud-${layer}:latest"
        echo -e "${GREEN}✓${NC} Tagged as ${REGISTRY}/arcana-cloud-${layer}:latest"

        return 0
    else
        echo -e "${RED}✗${NC} Failed to build ${layer}"
        return 1
    fi
}

# Build all layers
echo -e "${YELLOW}Building Repository Layer...${NC}"
build_image "repository" "Dockerfile.repository" || exit 1
echo ""

echo -e "${YELLOW}Building Service Layer...${NC}"
build_image "service" "Dockerfile.service" || exit 1
echo ""

echo -e "${YELLOW}Building Controller Layer...${NC}"
build_image "controller" "Dockerfile.controller" || exit 1
echo ""

# List built images
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Built Images:${NC}"
echo -e "${BLUE}========================================${NC}"
docker images | grep "arcana-cloud" | grep -E "${VERSION}|latest"
echo ""

# Push images if requested
if [ "$PUSH" = true ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Pushing Images to Registry${NC}"
    echo -e "${BLUE}========================================${NC}"

    for layer in repository service controller; do
        echo -e "${BLUE}==>${NC} Pushing ${GREEN}${layer}${NC}..."
        docker push "${REGISTRY}/arcana-cloud-${layer}:${VERSION}"
        docker push "${REGISTRY}/arcana-cloud-${layer}:latest"
        echo -e "${GREEN}✓${NC} Pushed ${layer}"
    done

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All images pushed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${YELLOW}⚠${NC} Images not pushed (use --push to push to registry)"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. For local Kubernetes (Docker Desktop/Minikube):"
echo -e "     ${BLUE}# Images are ready to use${NC}"
echo -e "     ${BLUE}kubectl apply -f k8s/${NC}"
echo -e ""
echo -e "  2. To push to a registry:"
echo -e "     ${BLUE}./scripts/build-images.sh --push${NC}"
echo -e ""
echo -e "  3. To build with a custom registry:"
echo -e "     ${BLUE}./scripts/build-images.sh --registry myregistry.io/myproject${NC}"
echo ""
