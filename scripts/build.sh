#!/bin/bash
# ============================================================================
# Arcana Cloud - Build Script
# ============================================================================
# Builds Docker images for all deployment modes
# ============================================================================

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGISTRY="${DOCKER_REGISTRY:-docker.io/arcanacloud}"
VERSION="${VERSION:-latest}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
PUSH_IMAGES=false
BUILD_MODE="all"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build Docker images for Arcana Cloud application

OPTIONS:
    -m, --mode MODE         Build mode: all, base, monolithic, layered, microservices (default: all)
    -r, --registry REGISTRY Docker registry (default: docker.io/arcanacloud)
    -v, --version VERSION   Image version tag (default: latest)
    -p, --push              Push images to registry after building
    -h, --help              Show this help message

EXAMPLES:
    # Build all images
    ./build.sh

    # Build only base image
    ./build.sh --mode base

    # Build and push monolithic image
    ./build.sh --mode monolithic --push

    # Build with custom version
    ./build.sh --version 1.2.3 --push

EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            BUILD_MODE="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -p|--push)
            PUSH_IMAGES=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Print build configuration
print_info "============================================"
print_info "Arcana Cloud - Docker Build"
print_info "============================================"
print_info "Registry:     $REGISTRY"
print_info "Version:      $VERSION"
print_info "Build Date:   $BUILD_DATE"
print_info "Git Commit:   $GIT_COMMIT"
print_info "Build Mode:   $BUILD_MODE"
print_info "Push Images:  $PUSH_IMAGES"
print_info "============================================"
echo

# Function to build Docker image
build_image() {
    local name=$1
    local dockerfile=$2
    local image_tag="${REGISTRY}/${name}:${VERSION}"
    local latest_tag="${REGISTRY}/${name}:latest"

    print_info "Building ${name}..."

    docker build \
        --build-arg PYTHON_VERSION=3.14.0 \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VCS_REF="${GIT_COMMIT}" \
        --build-arg VERSION="${VERSION}" \
        -t "${image_tag}" \
        -t "${latest_tag}" \
        -f "${PROJECT_ROOT}/${dockerfile}" \
        "${PROJECT_ROOT}"

    if [ $? -eq 0 ]; then
        print_success "Built ${image_tag}"

        if [ "$PUSH_IMAGES" = true ]; then
            print_info "Pushing ${image_tag}..."
            docker push "${image_tag}"
            docker push "${latest_tag}"
            if [ $? -eq 0 ]; then
                print_success "Pushed ${image_tag}"
            else
                print_error "Failed to push ${image_tag}"
                return 1
            fi
        fi
    else
        print_error "Failed to build ${image_tag}"
        return 1
    fi

    echo
}

# Function to build base image
build_base() {
    print_info "Building base image..."
    build_image "arcana-cloud-base" "docker/Dockerfile.base"
}

# Function to build monolithic image
build_monolithic() {
    print_info "Building monolithic image..."
    build_image "arcana-cloud-monolithic" "docker/Dockerfile.monolithic"
}

# Function to build layered images
build_layered() {
    print_info "Building layered deployment images..."
    build_image "arcana-cloud-controller" "docker/Dockerfile.controller"
    build_image "arcana-cloud-service" "docker/Dockerfile.service"
    build_image "arcana-cloud-repository" "docker/Dockerfile.repository"
}

# Function to build microservices images
build_microservices() {
    print_info "Building microservices images..."
    # For now, using monolithic dockerfile as template
    # In production, create specific Dockerfiles for each microservice
    print_warning "Microservices mode uses monolithic Dockerfile as base"
    build_image "arcana-cloud-auth" "docker/Dockerfile.monolithic"
    build_image "arcana-cloud-user" "docker/Dockerfile.monolithic"
}

# Main build logic
cd "${PROJECT_ROOT}"

case $BUILD_MODE in
    all)
        build_base
        build_monolithic
        build_layered
        build_microservices
        ;;
    base)
        build_base
        ;;
    monolithic)
        build_base
        build_monolithic
        ;;
    layered)
        build_base
        build_layered
        ;;
    microservices)
        build_base
        build_microservices
        ;;
    *)
        print_error "Invalid build mode: $BUILD_MODE"
        usage
        ;;
esac

# Print summary
print_info "============================================"
print_success "Build completed successfully!"
print_info "============================================"
echo

# Show built images
print_info "Built images:"
docker images | grep -E "(arcana-cloud|REPOSITORY)" | head -20

exit 0
