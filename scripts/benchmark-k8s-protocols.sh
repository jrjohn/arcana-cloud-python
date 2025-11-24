#!/bin/bash
# ============================================================================
# Kubernetes Protocol Benchmark Script
# ============================================================================
# Compares gRPC vs HTTP performance in Kubernetes environment
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="arcana-cloud"
CONTROLLER_URL="http://localhost:8080"
REPORT_DIR="docs/test-reports/benchmarks"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create report directory
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Kubernetes Protocol Benchmark${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check current protocol
check_protocol() {
    kubectl get configmap arcana-cloud-config -n "$NAMESPACE" -o yaml | grep "COMMUNICATION_PROTOCOL:" | awk '{print $2}'
}

# Function to clean test database
clean_database() {
    echo -e "${YELLOW}Cleaning test database (preserving fixture users)...${NC}"
    # Delete all non-fixture users and their tokens
    # This preserves testuser and admin so tests can rely on them
    kubectl exec -n "$NAMESPACE" mysql-0 -- mysql -u arcana -parcana_pass arcana_cloud -e "
        SET FOREIGN_KEY_CHECKS=0;
        -- Delete tokens for non-fixture users
        DELETE FROM oauth_tokens WHERE user_id NOT IN (
            SELECT id FROM users WHERE username IN ('testuser', 'admin')
        );
        -- Delete all non-fixture users
        DELETE FROM users WHERE username NOT IN ('testuser', 'admin');
        SET FOREIGN_KEY_CHECKS=1;
    " 2>&1 | grep -v "Warning: Using a password"
    echo -e "${GREEN}✓ Database cleaned (fixture users preserved)${NC}"
}

# Function to populate test fixtures
populate_fixtures() {
    echo -e "${YELLOW}Populating test fixtures...${NC}"
    # Run the script and capture output, filtering only warnings
    if venv/bin/python3 scripts/populate-test-fixtures.py --namespace "$NAMESPACE" 2>&1 | grep -v "DeprecationWarning" | grep -v "mysql: \[Warning\]" > /tmp/fixtures-output.log 2>&1; then
        # Show summary from the output
        grep "✓" /tmp/fixtures-output.log | tail -1
    else
        echo -e "${RED}✗ Fixture population failed${NC}"
        cat /tmp/fixtures-output.log
        return 1
    fi
}

# Function to switch protocol
switch_protocol() {
    local protocol=$1
    echo -e "${YELLOW}Switching to $protocol mode...${NC}"

    # Update configmap
    kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
        -p='[{"op": "replace", "path": "/data/COMMUNICATION_PROTOCOL", "value":"'$protocol'"}]'

    # Update URL configurations based on protocol
    if [ "$protocol" = "grpc" ]; then
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/USER_REPO_URLS", "value":"repository-layer:50052"}]'
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/USER_SERVICE_URLS", "value":"service-layer:50051"}]'
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/REPOSITORY_URL", "value":"repository-layer:50052"}]'
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/SERVICE_URL", "value":"service-layer:50051"}]'
    else
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/USER_REPO_URLS", "value":"http://repository-layer:5002"}]'
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/USER_SERVICE_URLS", "value":"http://service-layer:5001"}]'
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/REPOSITORY_URL", "value":"http://repository-layer:5002"}]'
        kubectl patch configmap arcana-cloud-config -n "$NAMESPACE" --type='json' \
            -p='[{"op": "replace", "path": "/data/SERVICE_URL", "value":"http://service-layer:5001"}]'
    fi

    # Update deployment environment variables (these override ConfigMap)
    echo "Updating deployment environment variables..."

    if [ "$protocol" = "grpc" ]; then
        # gRPC mode - use gRPC ports without http:// prefix
        kubectl set env deployment/repository-layer -n "$NAMESPACE" \
            COMMUNICATION_PROTOCOL=grpc
        kubectl set env deployment/service-layer -n "$NAMESPACE" \
            COMMUNICATION_PROTOCOL=grpc \
            USER_REPO_URLS=repository-layer:50052 \
            REPOSITORY_URL=repository-layer:50052
        kubectl set env deployment/controller-layer -n "$NAMESPACE" \
            COMMUNICATION_PROTOCOL=grpc \
            USER_SERVICE_URLS=service-layer:50051 \
            SERVICE_URL=service-layer:50051 \
            AUTH_SERVICE_URLS=service-layer:50051 \
            REPOSITORY_URL=repository-layer:50052 \
            USER_REPO_URLS=repository-layer:50052
    else
        # HTTP mode - use HTTP URLs with http:// prefix
        kubectl set env deployment/repository-layer -n "$NAMESPACE" \
            COMMUNICATION_PROTOCOL=http
        kubectl set env deployment/service-layer -n "$NAMESPACE" \
            COMMUNICATION_PROTOCOL=http \
            USER_REPO_URLS=http://repository-layer:5002 \
            REPOSITORY_URL=http://repository-layer:5002
        kubectl set env deployment/controller-layer -n "$NAMESPACE" \
            COMMUNICATION_PROTOCOL=http \
            USER_SERVICE_URLS=http://service-layer:5001 \
            SERVICE_URL=http://service-layer:5001 \
            AUTH_SERVICE_URLS=http://service-layer:5001 \
            REPOSITORY_URL=http://repository-layer:5002 \
            USER_REPO_URLS=http://repository-layer:5002
    fi

    # Restart deployments to pick up new config
    echo "Restarting deployments..."
    kubectl rollout restart deployment/repository-layer -n "$NAMESPACE"
    kubectl rollout restart deployment/service-layer -n "$NAMESPACE"
    kubectl rollout restart deployment/controller-layer -n "$NAMESPACE"

    # Wait for rollout to complete
    echo "Waiting for deployments to be ready..."
    kubectl rollout status deployment/repository-layer -n "$NAMESPACE" --timeout=180s
    kubectl rollout status deployment/service-layer -n "$NAMESPACE" --timeout=180s
    kubectl rollout status deployment/controller-layer -n "$NAMESPACE" --timeout=180s

    # Additional wait for services to fully initialize
    echo "Waiting for services to initialize..."
    sleep 30

    echo -e "${GREEN}✓ Switched to $protocol mode${NC}"
}

# Function to run benchmark
run_benchmark() {
    local protocol=$1
    local output_file="$REPORT_DIR/k8s-${protocol}-${TIMESTAMP}.html"
    local json_file="$REPORT_DIR/k8s-${protocol}-${TIMESTAMP}.json"

    echo -e "${BLUE}Running $protocol benchmark...${NC}"

    # Kill any existing port-forwards to port 8080
    echo "Cleaning up existing port-forwards..."
    pkill -f "kubectl port-forward.*8080:5000" || true
    sleep 2

    # Set up port-forward to controller service
    echo "Setting up port-forward to controller service..."
    kubectl port-forward -n "$NAMESPACE" svc/controller-layer 8080:5000 > /dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    sleep 5

    # Verify port-forward is working
    echo "Verifying port-forward connection..."
    if ! curl -f http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Port-forward health check failed, but continuing...${NC}"
    else
        echo -e "${GREEN}✓ Port-forward established${NC}"
    fi

    # Set environment variables for tests
    export DEPLOYMENT_MODE=microservices
    export COMMUNICATION_PROTOCOL=$protocol
    export SERVICE_URL=$CONTROLLER_URL
    export REPOSITORY_URL=$CONTROLLER_URL
    export CONTROLLER_URL=$CONTROLLER_URL
    export DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud"
    export TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud"

    # Run pytest with timing
    PYTHONPATH=/Users/jrjohn/Documents/projects/arcana-cloud-python:$PYTHONPATH \
        venv/bin/python -m pytest tests/integration/ \
        -v \
        --html="$output_file" \
        --self-contained-html \
        --json-report \
        --json-report-file="$json_file" \
        --tb=short \
        2>&1 | tee "$REPORT_DIR/k8s-${protocol}-${TIMESTAMP}.log"

    # Clean up port-forward
    echo "Cleaning up port-forward..."
    kill $PORT_FORWARD_PID 2>/dev/null || true
    pkill -f "kubectl port-forward.*8080:5000" || true

    echo -e "${GREEN}✓ $protocol benchmark complete${NC}"
    echo "  HTML Report: $output_file"
    echo "  JSON Report: $json_file"
}

# Main execution
echo "Current protocol: $(check_protocol)"
echo ""

# Clean database and populate fixtures before benchmarking
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Preparing Test Environment${NC}"
echo -e "${BLUE}========================================${NC}"
clean_database
populate_fixtures

# Run gRPC benchmark first (if not already in gRPC mode)
CURRENT_PROTOCOL=$(check_protocol)
if [ "$CURRENT_PROTOCOL" != "grpc" ]; then
    switch_protocol "grpc"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Running gRPC Benchmark${NC}"
echo -e "${BLUE}========================================${NC}"
run_benchmark "grpc"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Switching to HTTP Mode${NC}"
echo -e "${BLUE}========================================${NC}"
switch_protocol "http"

# Clean database again before HTTP tests to ensure fresh state
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Preparing for HTTP Tests${NC}"
echo -e "${BLUE}========================================${NC}"
clean_database
populate_fixtures

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Running HTTP Benchmark${NC}"
echo -e "${BLUE}========================================${NC}"
run_benchmark "http"

# Generate comparison report
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Generating Comparison Report${NC}"
echo -e "${BLUE}========================================${NC}"

GRPC_JSON="$REPORT_DIR/k8s-grpc-${TIMESTAMP}.json"
HTTP_JSON="$REPORT_DIR/k8s-http-${TIMESTAMP}.json"

if [ -f "$GRPC_JSON" ] && [ -f "$HTTP_JSON" ]; then
    python -c "
import json
import sys

# Load results
with open('$GRPC_JSON', 'r') as f:
    grpc_data = json.load(f)
with open('$HTTP_JSON', 'r') as f:
    http_data = json.load(f)

# Extract metrics
grpc_duration = grpc_data.get('duration', 0)
http_duration = http_data.get('duration', 0)
grpc_passed = grpc_data['summary'].get('passed', 0)
http_passed = http_data['summary'].get('passed', 0)
grpc_failed = grpc_data['summary'].get('failed', 0)
http_failed = http_data['summary'].get('failed', 0)
grpc_total = grpc_data['summary'].get('total', 0)
http_total = http_data['summary'].get('total', 0)

# Calculate improvements
if http_duration > 0:
    speed_improvement = ((http_duration - grpc_duration) / http_duration) * 100
else:
    speed_improvement = 0

print('\n' + '='*60)
print('KUBERNETES BENCHMARK COMPARISON REPORT')
print('='*60)
print(f'\nTest Suite: Integration Tests')
print(f'Timestamp: $TIMESTAMP')
print(f'\ngRPC Mode:')
print(f'  Duration: {grpc_duration:.2f}s')
print(f'  Passed: {grpc_passed}/{grpc_total}')
print(f'  Failed: {grpc_failed}')
print(f'\nHTTP Mode:')
print(f'  Duration: {http_duration:.2f}s')
print(f'  Passed: {http_passed}/{http_total}')
print(f'  Failed: {http_failed}')
print(f'\nPerformance Comparison:')
if speed_improvement > 0:
    print(f'  gRPC is {speed_improvement:.1f}% FASTER than HTTP')
elif speed_improvement < 0:
    print(f'  gRPC is {abs(speed_improvement):.1f}% SLOWER than HTTP')
else:
    print(f'  gRPC and HTTP have similar performance')
print(f'  Time saved: {http_duration - grpc_duration:.2f}s')
print('\n' + '='*60)
" | tee "$REPORT_DIR/k8s-comparison-${TIMESTAMP}.txt"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Benchmark Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Reports saved to: $REPORT_DIR"
echo ""
