#!/bin/bash
# K8s+gRPC Benchmark Script

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PYTHONPATH=/Users/jrjohn/Documents/projects/arcana-cloud-python:$PYTHONPATH \
    DEPLOYMENT_MODE=microservices \
    COMMUNICATION_PROTOCOL=grpc \
    SERVICE_URL=http://localhost:8080 \
    REPOSITORY_URL=http://localhost:8080 \
    CONTROLLER_URL=http://localhost:8080 \
    DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud" \
    TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud" \
    venv/bin/python -m pytest tests/integration/ \
    -v \
    --html="docs/test-reports/benchmarks/k8s-grpc-${TIMESTAMP}.html" \
    --self-contained-html \
    --json-report \
    --json-report-file="docs/test-reports/benchmarks/k8s-grpc-${TIMESTAMP}.json" \
    --tb=line \
    2>&1 | tee "docs/test-reports/benchmarks/k8s-grpc-${TIMESTAMP}.txt"
