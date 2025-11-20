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

# Wait for repository layer to be ready
echo "Waiting for repository layer to be available..."
for repo_url in ${USER_REPO_URLS//,/ }; do
    host=$(echo $repo_url | sed -e 's|^http://||' -e 's|:.*||')
    port=$(echo $repo_url | sed -e 's|.*:||' -e 's|/.*||')

    echo "Waiting for $host:$port..."
    timeout 60 bash -c "until nc -z $host $port; do sleep 1; done"
    echo "$host:$port is available"
done

echo "Repository layer is ready"

# Execute the main command
echo "Starting service application on port ${SERVICE_PORT}..."
exec "$@"
