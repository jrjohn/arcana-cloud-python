#!/bin/bash
# ============================================================================
# Service Layer Health Check
# ============================================================================
# Protocol-aware health check that works with both HTTP and gRPC modes
# ============================================================================

set -e

PROTOCOL=${COMMUNICATION_PROTOCOL:-http}

if [ "$PROTOCOL" = "grpc" ]; then
    # For gRPC mode, check if the gRPC server port is listening
    # Using Python to check if the process is listening on the gRPC port
    python3 -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('localhost', 50051)); s.close()" 2>/dev/null
    exit $?
else
    # For HTTP mode, use curl to check the health endpoint
    curl -f http://localhost:5001/health || exit 1
fi
