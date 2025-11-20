#!/bin/bash
# ============================================================================
# Health Check Script
# ============================================================================
# Universal health check script for all deployment modes
# Checks both liveness and readiness based on SERVICE_PORT
# ============================================================================

set -e

# Get service port from environment variable
PORT=${SERVICE_PORT:-5000}
DEPLOYMENT_LAYER=${DEPLOYMENT_LAYER:-monolithic}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to check liveness
check_liveness() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}[OK]${NC} Liveness check passed (HTTP $response)"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} Liveness check failed (HTTP $response)"
        return 1
    fi
}

# Function to check readiness (includes dependency checks)
check_readiness() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/ready 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}[OK]${NC} Readiness check passed (HTTP $response)"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} Readiness check failed (HTTP $response)"
        return 1
    fi
}

# Main health check logic
main() {
    echo "Health check for ${DEPLOYMENT_LAYER} layer on port ${PORT}"

    # Always check liveness
    if ! check_liveness; then
        exit 1
    fi

    # For production, also check readiness
    if [ "$FLASK_ENV" = "production" ]; then
        if ! check_readiness; then
            exit 1
        fi
    fi

    echo -e "${GREEN}[SUCCESS]${NC} All health checks passed"
    exit 0
}

main
