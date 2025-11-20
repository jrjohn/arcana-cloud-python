#!/bin/bash

# ============================================================================
# Docker Image Build Script for uWSGI-based Deployment
# ============================================================================
# Builds all Docker images with uWSGI for high-performance deployment
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
echo -e "${BLUE}Building uWSGI Docker Images${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Registry: ${GREEN}${REGISTRY}${NC}"
echo -e "Version:  ${GREEN}${VERSION}${NC}"
echo -e "Server:   ${GREEN}uWSGI${NC}"
echo ""

# Function to build an image
build_image() {
    local layer=$1
    local dockerfile=$2
    local tag="${REGISTRY}/arcana-cloud-${layer}-uwsgi:${VERSION}"

    echo -e "${BLUE}==>${NC} Building ${GREEN}${layer}${NC} layer with uWSGI..."

    if docker build ${BUILD_ARGS} \
        -t "${tag}" \
        -f "${dockerfile}" \
        .; then
        echo -e "${GREEN}✓${NC} Successfully built ${tag}"

        # Tag as latest
        docker tag "${tag}" "${REGISTRY}/arcana-cloud-${layer}-uwsgi:latest"
        echo -e "${GREEN}✓${NC} Tagged as ${REGISTRY}/arcana-cloud-${layer}-uwsgi:latest"

        return 0
    else
        echo -e "${RED}✗${NC} Failed to build ${layer}"
        return 1
    fi
}

# Build all layers
echo -e "${YELLOW}Building Repository Layer with uWSGI...${NC}"
build_image "repository" "Dockerfile.repository.uwsgi" || exit 1
echo ""

echo -e "${YELLOW}Building Service Layer with uWSGI...${NC}"
build_image "service" "Dockerfile.service.uwsgi" || exit 1
echo ""

echo -e "${YELLOW}Building Controller Layer with uWSGI...${NC}"
build_image "controller" "Dockerfile.controller.uwsgi" || exit 1
echo ""

# List built images
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Built Images:${NC}"
echo -e "${BLUE}========================================${NC}"
docker images | grep "arcana-cloud" | grep "uwsgi" | grep -E "${VERSION}|latest"
echo ""

# Push images if requested
if [ "$PUSH" = true ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Pushing Images to Registry${NC}"
    echo -e "${BLUE}========================================${NC}"

    for layer in repository service controller; do
        echo -e "${BLUE}==>${NC} Pushing ${GREEN}${layer}${NC}..."
        docker push "${REGISTRY}/arcana-cloud-${layer}-uwsgi:${VERSION}"
        docker push "${REGISTRY}/arcana-cloud-${layer}-uwsgi:latest"
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
echo -e "  1. Apply Nginx Ingress configuration:"
echo -e "     ${BLUE}kubectl apply -f k8s/nginx-ingress.yaml${NC}"
echo -e ""
echo -e "  2. Update deployments to use uWSGI images:"
echo -e "     ${BLUE}kubectl rollout restart deployment -n arcana-cloud${NC}"
echo -e ""
echo -e "  3. Verify deployment:"
echo -e "     ${BLUE}kubectl get pods -n arcana-cloud${NC}"
echo -e "     ${BLUE}kubectl get ingress -n arcana-cloud${NC}"
echo ""
