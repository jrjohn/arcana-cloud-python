#!/bin/bash
# ============================================================================
# Test Layered Mode with Docker Compose
# ============================================================================
# This script starts all layers in Docker containers and runs integration tests
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Arcana Cloud - Layered Mode Testing${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Clean up any existing containers
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true

# Build and start all layers
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.test.yml build

echo -e "${YELLOW}Starting all layers...${NC}"
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
MAX_WAIT=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}All services are healthy!${NC}"
        break
    fi
    echo "Waiting... ($ELAPSED/$MAX_WAIT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}Services failed to become healthy within $MAX_WAIT seconds${NC}"
    docker-compose -f docker-compose.test.yml logs
    docker-compose -f docker-compose.test.yml down -v
    exit 1
fi

# Show service status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker-compose -f docker-compose.test.yml ps

# Check health endpoints
echo ""
echo -e "${YELLOW}Checking health endpoints...${NC}"
curl -f http://localhost:5000/health || echo -e "${RED}Controller health check failed${NC}"
curl -f http://localhost:5001/health || echo -e "${RED}Service health check failed${NC}"
curl -f http://localhost:5002/health || echo -e "${RED}Repository health check failed${NC}"

# Run tests against the running services
echo ""
echo -e "${GREEN}Running integration tests...${NC}"
export DEPLOYMENT_MODE=layered
export DEPLOYMENT_LAYER=controller
export SERVICE_URL=http://localhost:5001
export DATABASE_URL=sqlite:///arcana_test.db

pytest tests/ -v --tb=short \
  --html=docs/test-reports/layered/layered-test-report-docker.html \
  --self-contained-html \
  --cov=app \
  --cov-report=html:docs/test-reports/layered/coverage-docker \
  --cov-report=term-missing \
  2>&1 | tee docs/test-reports/layered/test-output-docker.log

TEST_EXIT_CODE=${PIPESTATUS[0]}

# Cleanup
echo ""
echo -e "${YELLOW}Cleaning up containers...${NC}"
docker-compose -f docker-compose.test.yml down -v

# Report results
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo -e "${RED}========================================${NC}"
fi

exit $TEST_EXIT_CODE
