#!/bin/bash
# ============================================================================
# Kubernetes Manifests Validation Script
# ============================================================================
# This script validates all Kubernetes manifests using dry-run mode
# Usage: ./scripts/test-k8s-manifests.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

print_success "kubectl is installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"

echo ""
print_step "Testing Kubernetes Deployment Steps (Dry Run)"
echo "================================================"
echo ""

# Step 1: Namespace
print_step "Step 1: Validating namespace.yaml"
if kubectl apply -f k8s/namespace.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "namespace.yaml is valid"
else
    print_error "namespace.yaml validation failed"
    kubectl apply -f k8s/namespace.yaml --dry-run=client
    exit 1
fi

# Step 2: Secrets
print_step "Step 2: Validating secrets.yaml"
if kubectl apply -f k8s/secrets.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "secrets.yaml is valid"
else
    print_error "secrets.yaml validation failed"
    kubectl apply -f k8s/secrets.yaml --dry-run=client
    exit 1
fi

# Step 3: ConfigMap
print_step "Step 3: Validating configmap.yaml"
if kubectl apply -f k8s/configmap.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "configmap.yaml is valid"
else
    print_error "configmap.yaml validation failed"
    kubectl apply -f k8s/configmap.yaml --dry-run=client
    exit 1
fi

# Step 4: PVC
print_step "Step 4: Validating pvc.yaml"
if kubectl apply -f k8s/pvc.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "pvc.yaml is valid"
else
    print_error "pvc.yaml validation failed"
    kubectl apply -f k8s/pvc.yaml --dry-run=client
    exit 1
fi

# Step 5: Database Deployments
print_step "Step 5: Validating mysql-deployment.yaml"
if kubectl apply -f k8s/mysql-deployment.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "mysql-deployment.yaml is valid"
else
    print_error "mysql-deployment.yaml validation failed"
    kubectl apply -f k8s/mysql-deployment.yaml --dry-run=client
    exit 1
fi

print_step "Step 5b: Validating redis-deployment.yaml"
if kubectl apply -f k8s/redis-deployment.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "redis-deployment.yaml is valid"
else
    print_error "redis-deployment.yaml validation failed"
    kubectl apply -f k8s/redis-deployment.yaml --dry-run=client
    exit 1
fi

# Step 6: Application Deployments
print_step "Step 6a: Validating repository-deployment.yaml"
if kubectl apply -f k8s/repository-deployment.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "repository-deployment.yaml is valid"
else
    print_error "repository-deployment.yaml validation failed"
    kubectl apply -f k8s/repository-deployment.yaml --dry-run=client
    exit 1
fi

print_step "Step 6b: Validating service-deployment.yaml"
if kubectl apply -f k8s/service-deployment.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "service-deployment.yaml is valid"
else
    print_error "service-deployment.yaml validation failed"
    kubectl apply -f k8s/service-deployment.yaml --dry-run=client
    exit 1
fi

print_step "Step 6c: Validating controller-deployment.yaml"
if kubectl apply -f k8s/controller-deployment.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "controller-deployment.yaml is valid"
else
    print_error "controller-deployment.yaml validation failed"
    kubectl apply -f k8s/controller-deployment.yaml --dry-run=client
    exit 1
fi

# Step 7: Services
print_step "Step 7: Validating services.yaml"
if kubectl apply -f k8s/services.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "services.yaml is valid"
else
    print_error "services.yaml validation failed"
    kubectl apply -f k8s/services.yaml --dry-run=client
    exit 1
fi

# Step 8: Ingress
print_step "Step 8: Validating ingress.yaml"
if kubectl apply -f k8s/ingress.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "ingress.yaml is valid"
else
    print_error "ingress.yaml validation failed"
    kubectl apply -f k8s/ingress.yaml --dry-run=client
    exit 1
fi

# Step 9: HPA
print_step "Step 9: Validating hpa.yaml"
if kubectl apply -f k8s/hpa.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "hpa.yaml is valid"
else
    print_error "hpa.yaml validation failed"
    kubectl apply -f k8s/hpa.yaml --dry-run=client
    exit 1
fi

# Step 10: RBAC
print_step "Step 10: Validating rbac.yaml"
if kubectl apply -f k8s/rbac.yaml --dry-run=client > /dev/null 2>&1; then
    print_success "rbac.yaml is valid"
else
    print_error "rbac.yaml validation failed"
    kubectl apply -f k8s/rbac.yaml --dry-run=client
    exit 1
fi

echo ""
echo "================================================"
print_success "All Kubernetes manifests are valid! ✓"
echo ""
print_warning "Note: This was a dry-run validation only."
print_warning "To actually deploy, run the commands from the README."
echo ""
print_step "Quick Deploy Command:"
echo "  kubectl apply -f k8s/"
echo ""
