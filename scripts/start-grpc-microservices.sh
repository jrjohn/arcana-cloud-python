#!/bin/bash
# Start Microservices Mode with gRPC Communication
# Repository: gRPC | Service: gRPC | Controller: HTTP REST API

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Microservices Mode (gRPC)${NC}"
echo "========================================"

# Set environment variables
export DEPLOYMENT_MODE=microservices
export COMMUNICATION_PROTOCOL=grpc
export DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test"
export TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test"

# Initialize database
echo -e "${YELLOW}Cleaning and initializing database...${NC}"
python3 scripts/init_test_db.py

# Clean up any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "python.*repository_service_server.py" 2>/dev/null || true
pkill -f "python.*user_service_server.py" 2>/dev/null || true
pkill -f "python.*controller_server.py" 2>/dev/null || true
sleep 2

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Repository Layer gRPC Server (port 50052)
echo -e "${YELLOW}Starting Repository Layer gRPC Server (port 50052)...${NC}"
export DEPLOYMENT_LAYER=repository
python3 -m app.grpc_protos.servers.repository_service_server > logs/repository-grpc.log 2>&1 &
REPO_PID=$!
echo "Repository gRPC PID: $REPO_PID"

# Wait for repository to be ready
sleep 3
if ps -p $REPO_PID > /dev/null; then
    echo -e "${GREEN}✅ Repository Layer gRPC Server started${NC}"
else
    echo -e "${RED}❌ Repository Layer failed to start${NC}"
    cat logs/repository-grpc.log
    exit 1
fi

# Start Service Layer gRPC Server (port 50051)
echo -e "${YELLOW}Starting Service Layer gRPC Server (port 50051)...${NC}"
export DEPLOYMENT_LAYER=service
export USER_REPO_URLS="localhost:50052"  # Service connects to Repository via gRPC
python3 -m app.grpc_protos.servers.user_service_server > logs/service-grpc.log 2>&1 &
SERVICE_PID=$!
echo "Service gRPC PID: $SERVICE_PID"

# Wait for service to be ready
sleep 3
if ps -p $SERVICE_PID > /dev/null; then
    echo -e "${GREEN}✅ Service Layer gRPC Server started${NC}"
else
    echo -e "${RED}❌ Service Layer failed to start${NC}"
    cat logs/service-grpc.log
    kill $REPO_PID 2>/dev/null || true
    exit 1
fi

# Start Controller Layer HTTP Server (port 5003)
echo -e "${YELLOW}Starting Controller Layer HTTP Server (port 5003)...${NC}"
export DEPLOYMENT_LAYER=controller
export USER_SERVICE_URLS="localhost:50051"  # Controller connects to Service via gRPC
export PORT=5003
python3 -m app.controller_server > logs/controller-http.log 2>&1 &
CONTROLLER_PID=$!
echo "Controller HTTP PID: $CONTROLLER_PID"

# Wait for controller to be ready
sleep 3
if curl -s http://localhost:5003/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Controller Layer started${NC}"
else
    echo -e "${RED}❌ Controller Layer failed to start${NC}"
    cat logs/controller-http.log
    kill $SERVICE_PID $REPO_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Microservices Mode (gRPC) started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Architecture:"
echo "  Controller (HTTP) :5003 → Service (gRPC) :50051 → Repository (gRPC) :50052"
echo ""
echo "Repository gRPC: localhost:50052"
echo "Service gRPC:    localhost:50051"
echo "Controller API:  http://localhost:5003"
echo ""
echo "PIDs: Repo=$REPO_PID, Service=$SERVICE_PID, Controller=$CONTROLLER_PID"
echo ""
echo "To stop all layers, run:"
echo "kill $CONTROLLER_PID $SERVICE_PID $REPO_PID"
