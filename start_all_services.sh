#!/bin/bash
# Start all gRPC microservices with correct environment

# Kill existing processes
pkill -9 -f "repository_service_server"
pkill -9 -f "user_service_server"
pkill -9 -f "controller_server"
sleep 2

# Activate venv and set common variables
source venv/bin/activate
export DEPLOYMENT_MODE=microservices
export COMMUNICATION_PROTOCOL=grpc
export DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test"
export TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test"

# Create logs directory
mkdir -p logs

# Start Repository Layer (port 50052)
export DEPLOYMENT_LAYER=repository
python3 -m app.grpc_protos.servers.repository_service_server > logs/repository-grpc.log 2>&1 &
echo "Started Repository gRPC Server (PID: $!)"
sleep 3

# Start Service Layer (port 50051)
export DEPLOYMENT_LAYER=service
export USER_REPO_URLS="localhost:50052"
python3 -m app.grpc_protos.servers.user_service_server > logs/service-grpc.log 2>&1 &
echo "Started Service gRPC Server (PID: $!)"
sleep 3

# Start Controller Layer (port 5003)
export DEPLOYMENT_LAYER=controller
export USER_SERVICE_URLS="localhost:50051"
export PORT=5003
python3 -m app.controller_server > logs/controller-http.log 2>&1 &
echo "Started Controller HTTP Server (PID: $!)"
sleep 3

# Check health
curl -s http://localhost:5003/health
echo ""
echo "All services started!"
