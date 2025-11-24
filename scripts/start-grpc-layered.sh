#!/bin/bash
# Start Layered Mode with gRPC Communication
# Repository: Direct DB | Service: gRPC | Controller: HTTP REST API

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Layered Mode (gRPC)${NC}"
echo "========================================"

# Set environment variables
export DEPLOYMENT_MODE=layered
export COMMUNICATION_PROTOCOL=grpc
export DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test"
export TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test"

# Initialize database
echo -e "${YELLOW}Cleaning and initializing database...${NC}"
python3 scripts/init_test_db.py

# Clean up any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "python.*repository_server.py" 2>/dev/null || true
pkill -f "python.*service_server.py" 2>/dev/null || true
pkill -f "python.*controller_server.py" 2>/dev/null || true
sleep 2

# Start Repository Layer (Direct DB - no gRPC server needed)
echo -e "${YELLOW}Repository Layer: Direct database access (no server)${NC}"

# Start Service Layer gRPC Server (port 50051)
echo -e "${YELLOW}Starting Service Layer gRPC Server (port 50051)...${NC}"
export DEPLOYMENT_LAYER=service
export REPOSITORY_URL="direct"  # Service uses direct DB access
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
    kill $SERVICE_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Layered Mode (gRPC) started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Architecture:"
echo "  Controller (HTTP) :5003 → Service (gRPC) :50051 → Repository (Direct DB)"
echo ""
echo "Service gRPC:  localhost:50051"
echo "Controller API: http://localhost:5003"
echo ""
echo "PIDs: Service=$SERVICE_PID, Controller=$CONTROLLER_PID"
echo ""
echo "To stop all layers, run:"
echo "kill $CONTROLLER_PID $SERVICE_PID"
