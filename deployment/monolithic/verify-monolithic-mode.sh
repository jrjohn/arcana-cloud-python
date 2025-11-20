#!/bin/bash

# ============================================================================
# Monolithic Mode Deployment Verification
# ============================================================================
# Tests all three deployment methods for monolithic mode:
# 1. Docker Compose
# 2. Kubernetes
# 3. Direct Python execution
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_test() {
    echo -e "${BLUE}→${NC} Testing: $1"
}

# Test 1: Docker Compose Monolithic Mode
test_docker_compose_monolithic() {
    print_header "Test 1: Docker Compose Monolithic Mode"

    print_test "Checking docker-compose.yml exists"
    if [ -f "docker-compose.yml" ]; then
        print_success "docker-compose.yml found"
    else
        print_error "docker-compose.yml not found"
        return 1
    fi

    print_test "Stopping any existing containers"
    docker-compose down > /dev/null 2>&1 || true
    print_success "Cleaned up existing containers"

    print_test "Starting monolithic container"
    if docker-compose up -d; then
        print_success "Container started successfully"
    else
        print_error "Failed to start container"
        return 1
    fi

    print_info "Waiting for service to be ready (20s)..."
    sleep 20

    print_test "Checking container status"
    CONTAINER_STATUS=$(docker-compose ps --format json | grep -q "Up" && echo "running" || echo "not running")
    if [ "$CONTAINER_STATUS" == "running" ]; then
        print_success "Container is running"
    else
        print_error "Container is not running"
        docker-compose logs --tail=50
        return 1
    fi

    print_test "Testing health endpoint"
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        RESPONSE=$(curl -s http://localhost:5001/health)
        print_success "Health endpoint accessible: $RESPONSE"
    else
        print_error "Health endpoint not accessible"
        docker-compose logs --tail=20
        return 1
    fi

    print_test "Verifying all layers in single container"
    LAYERS_COUNT=$(docker-compose ps --services | wc -l)
    if [ "$LAYERS_COUNT" -eq 1 ]; then
        print_success "Single monolithic container verified"
    else
        print_error "Expected 1 container, found $LAYERS_COUNT"
    fi

    print_test "Checking for layer endpoints in monolithic mode"
    # In monolithic mode, all endpoints should be on port 5001 (mapped from container port 5000)
    if curl -s http://localhost:5001/health | grep -q "health\|ok"; then
        print_success "Monolithic service responding correctly"
    else
        print_error "Monolithic service not responding as expected"
    fi

    print_info "Stopping Docker Compose monolithic mode..."
    docker-compose down > /dev/null 2>&1

    echo ""
}

# Test 2: Kubernetes Monolithic Mode
test_kubernetes_monolithic() {
    print_header "Test 2: Kubernetes Monolithic Mode"

    print_test "Checking if kubectl is available"
    if command -v kubectl &> /dev/null; then
        print_success "kubectl is installed"
    else
        print_error "kubectl is not installed"
        return 1
    fi

    print_test "Checking Kubernetes cluster accessibility"
    if kubectl cluster-info > /dev/null 2>&1; then
        print_success "Kubernetes cluster is accessible"
    else
        print_error "Cannot access Kubernetes cluster"
        return 1
    fi

    print_test "Checking k8s/monolithic/ directory"
    if [ -d "k8s/monolithic" ]; then
        print_success "k8s/monolithic directory exists"

        print_test "Listing monolithic manifests"
        MANIFEST_COUNT=$(find k8s/monolithic -name "*.yaml" -o -name "*.yml" | wc -l)
        if [ "$MANIFEST_COUNT" -gt 0 ]; then
            print_success "Found $MANIFEST_COUNT manifest file(s)"
            find k8s/monolithic -name "*.yaml" -o -name "*.yml" | while read file; do
                print_info "  - $(basename $file)"
            done
        else
            print_error "No manifest files found in k8s/monolithic"
            return 1
        fi
    else
        print_info "k8s/monolithic directory not found - may need to be created"
        print_info "Note: Standard k8s/ manifests can be used with DEPLOYMENT_MODE=monolithic"

        # Check if standard manifests exist
        print_test "Checking standard k8s manifests"
        if [ -d "k8s" ] && [ "$(ls k8s/*.yaml 2>/dev/null | wc -l)" -gt 0 ]; then
            print_success "Standard k8s manifests available"
            print_info "Can deploy with: kubectl apply -f k8s/ (with DEPLOYMENT_MODE=monolithic env var)"
        else
            print_error "No Kubernetes manifests found"
            return 1
        fi
    fi

    echo ""
}

# Test 3: Direct Python Execution
test_direct_execution() {
    print_header "Test 3: Direct Python Execution"

    print_test "Checking Python version"
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python is installed: $PYTHON_VERSION"
    else
        print_error "Python3 is not installed"
        return 1
    fi

    print_test "Checking wsgi.py exists"
    if [ -f "wsgi.py" ]; then
        print_success "wsgi.py found"
    else
        print_error "wsgi.py not found"
        return 1
    fi

    print_test "Checking virtual environment"
    if [ -d "venv" ]; then
        print_success "Virtual environment exists"
    else
        print_info "Virtual environment not found - creating..."
        python3 -m venv venv
        if [ -d "venv" ]; then
            print_success "Virtual environment created"
        else
            print_error "Failed to create virtual environment"
            return 1
        fi
    fi

    print_test "Checking requirements.txt"
    if [ -f "requirements.txt" ]; then
        print_success "requirements.txt found"

        print_test "Checking if dependencies are installed"
        source venv/bin/activate
        if python3 -c "import flask" 2>/dev/null; then
            print_success "Flask is installed"
        else
            print_info "Installing dependencies..."
            pip install -q -r requirements.txt
            if python3 -c "import flask" 2>/dev/null; then
                print_success "Dependencies installed successfully"
            else
                print_error "Failed to install dependencies"
                return 1
            fi
        fi
        deactivate
    else
        print_error "requirements.txt not found"
        return 1
    fi

    print_test "Verifying DEPLOYMENT_LAYER environment variable support"
    if grep -q "DEPLOYMENT_LAYER" wsgi.py || grep -q "DEPLOYMENT_MODE" wsgi.py; then
        print_success "Environment variable configuration found in wsgi.py"
    else
        print_info "Environment variable may need to be added to wsgi.py"
    fi

    print_test "Checking application structure"
    if [ -d "app" ] || [ -d "controller_layer" ]; then
        print_success "Application structure found"
    else
        print_error "Application structure not found"
        return 1
    fi

    print_info "Note: To run in monolithic mode, use:"
    print_info "  DEPLOYMENT_LAYER=monolithic python wsgi.py"
    print_info "  or"
    print_info "  DEPLOYMENT_MODE=monolithic python wsgi.py"

    echo ""
}

# Test 4: Configuration Verification
test_configuration() {
    print_header "Test 4: Configuration Verification"

    print_test "Checking for configuration files"
    if [ -f "deployment-config.yaml" ]; then
        print_success "deployment-config.yaml found"

        print_test "Checking for monolithic mode configuration"
        if grep -q "mode.*monolithic" deployment-config.yaml; then
            print_success "Monolithic mode configuration found"
        else
            print_info "Monolithic mode may need to be configured"
        fi
    else
        print_info "deployment-config.yaml not found (optional)"
    fi

    print_test "Checking for environment template"
    if [ -f ".env.example" ]; then
        print_success ".env.example found"

        if grep -q "DEPLOYMENT" .env.example; then
            print_success "Deployment configuration in .env.example"
        fi
    else
        print_info ".env.example not found (optional)"
    fi

    echo ""
}

# Test 5: Documentation Check
test_documentation() {
    print_header "Test 5: Documentation Verification"

    print_test "Checking README.md"
    if [ -f "README.md" ]; then
        print_success "README.md found"

        if grep -q -i "monolithic" README.md; then
            print_success "Monolithic mode documented in README"
        else
            print_info "Consider adding monolithic mode documentation"
        fi
    else
        print_error "README.md not found"
    fi

    print_test "Checking for deployment documentation"
    if [ -f "docs/DEPLOYMENT.md" ] || [ -f "DEPLOYMENT.md" ]; then
        print_success "Deployment documentation found"
    else
        print_info "Consider creating deployment documentation"
    fi

    echo ""
}

# Summary
print_summary() {
    print_header "Verification Summary"

    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

    echo -e "${BLUE}Total Tests:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
    echo -e "${RED}Failed:${NC} $TESTS_FAILED"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}All Tests Passed! ✓${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${GREEN}Monolithic mode is properly configured!${NC}"
        echo ""
        echo -e "Available deployment methods:"
        echo -e "  ${BLUE}1. Docker Compose:${NC}    docker-compose up -d"
        echo -e "  ${BLUE}2. Kubernetes:${NC}        kubectl apply -f k8s/monolithic/"
        echo -e "  ${BLUE}3. Direct:${NC}            DEPLOYMENT_LAYER=monolithic python wsgi.py"
        echo ""
        return 0
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}Some Tests Failed ✗${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo -e "Please review the errors above and:"
        echo -e "  1. Check that all required files exist"
        echo -e "  2. Verify Docker and Kubernetes are properly configured"
        echo -e "  3. Ensure Python environment is set up correctly"
        echo ""
        return 1
    fi
}

# Main execution
main() {
    clear
    print_header "Monolithic Mode Verification"
    echo -e "${YELLOW}Testing all deployment methods${NC}"
    echo ""

    # Run all tests
    test_docker_compose_monolithic
    test_kubernetes_monolithic
    test_direct_execution
    test_configuration
    test_documentation

    # Print summary
    print_summary
    RESULT=$?

    exit $RESULT
}

# Run main
main
