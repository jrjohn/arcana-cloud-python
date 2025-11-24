#!/bin/bash
# ============================================================================
# Service Layer Entrypoint
# ============================================================================
# Initializes the service layer before starting the application
# ============================================================================

set -e

echo "============================================"
echo "Starting Arcana Cloud - Service Layer"
echo "============================================"

# Detect communication protocol
PROTOCOL=${COMMUNICATION_PROTOCOL:-http}

# Wait for repository layer to be ready (only for HTTP mode)
# gRPC servers don't respond to simple TCP checks, so we skip this for gRPC
if [ "$PROTOCOL" != "grpc" ]; then
    echo "Waiting for repository layer to be available..."
    for repo_url in ${USER_REPO_URLS//,/ }; do
        # Remove protocol prefix if present (http:// or grpc://)
        repo_url=$(echo $repo_url | sed -e 's|^[a-z]*://||')
        # Extract host and port
        host=$(echo $repo_url | sed -e 's|:.*||')
        port=$(echo $repo_url | sed -e 's|.*:||' -e 's|/.*||')

        echo "Waiting for $host:$port..."
        timeout 60 bash -c "until nc -z $host $port; do sleep 1; done"
        echo "$host:$port is available"
    done
    echo "Repository layer is ready"
else
    echo "gRPC mode: Skipping TCP connectivity check (gRPC servers will handle connections)"
fi

# Start appropriate server
echo "Communication protocol: ${PROTOCOL}"

if [ "$PROTOCOL" = "grpc" ]; then
    echo "Starting gRPC server on port ${GRPC_PORT:-50051}..."
    exec python -m app.grpc_protos.servers.grpc_server_runner
else
    echo "Starting HTTP Flask server on port ${SERVICE_PORT}..."
    exec "$@"
fi
