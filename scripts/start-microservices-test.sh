#!/bin/bash
# Start all layers for testing in MICROSERVICES mode (with full HTTP communication)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Microservices Mode (Local)${NC}"
echo "========================================"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Activate venv
source venv/bin/activate

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Set common environment
export DATABASE_URL="sqlite:///$PROJECT_ROOT/arcana_test.db"
export SECRET_KEY="test-secret-key"
export JWT_SECRET_KEY="test-jwt-secret"
export FLASK_ENV="testing"

# Kill any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "repository_server.py" 2>/dev/null || true
pkill -f "service_server.py" 2>/dev/null || true
pkill -f "controller_server.py" 2>/dev/null || true
sleep 2

# Start Repository Layer (port 5002)
echo -e "${YELLOW}Starting Repository Layer (port 5002)...${NC}"
export DEPLOYMENT_MODE=microservices
export DEPLOYMENT_LAYER=repository
export PORT=5002
python app/repository_server.py > logs/repository.log 2>&1 &
REPO_PID=$!
echo "Repository PID: $REPO_PID"
sleep 3

# Check if repository is running
if curl -f http://localhost:5002/health 2>/dev/null; then
    echo -e "${GREEN}✅ Repository Layer started${NC}"
else
    echo -e "${RED}❌ Repository Layer failed to start${NC}"
    cat logs/repository.log
    exit 1
fi

# Start Service Layer (port 5001)
echo -e "${YELLOW}Starting Service Layer (port 5001)...${NC}"
export DEPLOYMENT_MODE=microservices
export DEPLOYMENT_LAYER=service
export PORT=5001
export REPOSITORY_URL="http://localhost:5002"
export USER_REPO_URLS="http://localhost:5002"
python app/service_server.py > logs/service.log 2>&1 &
SERVICE_PID=$!
echo "Service PID: $SERVICE_PID"
sleep 3

# Check if service is running
if curl -f http://localhost:5001/health 2>/dev/null; then
    echo -e "${GREEN}✅ Service Layer started${NC}"
else
    echo -e "${RED}❌ Service Layer failed to start${NC}"
    cat logs/service.log
    kill $REPO_PID 2>/dev/null || true
    exit 1
fi

# Start Controller Layer (port 5003 - avoiding macOS AirPlay on 5000)
echo -e "${YELLOW}Starting Controller Layer (port 5003)...${NC}"
export DEPLOYMENT_MODE=microservices
export DEPLOYMENT_LAYER=controller
export PORT=5003
export SERVICE_URL="http://localhost:5001"
export USER_SERVICE_URLS="http://localhost:5001"
python app/controller_server.py > logs/controller.log 2>&1 &
CONTROLLER_PID=$!
echo "Controller PID: $CONTROLLER_PID"
sleep 3

# Check if controller is running
if curl -f http://localhost:5003/health 2>/dev/null; then
    echo -e "${GREEN}✅ Controller Layer started${NC}"
else
    echo -e "${RED}❌ Controller Layer failed to start${NC}"
    cat logs/controller.log
    kill $SERVICE_PID $REPO_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All layers started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Repository: http://localhost:5002/health"
echo "Service:    http://localhost:5001/health"
echo "Controller: http://localhost:5003/health"
echo ""
echo "PIDs: Repo=$REPO_PID, Service=$SERVICE_PID, Controller=$CONTROLLER_PID"
echo ""
echo "To stop all layers, run:"
echo "kill $CONTROLLER_PID $SERVICE_PID $REPO_PID"
