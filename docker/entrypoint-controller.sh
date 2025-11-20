#!/bin/bash
# ============================================================================
# Controller Layer Entrypoint
# ============================================================================
# Initializes the controller layer before starting the application
# ============================================================================

set -e

echo "============================================"
echo "Starting Arcana Cloud - Controller Layer"
echo "============================================"

# Wait for service layer to be ready
echo "Waiting for service layer to be available..."
for service_url in ${USER_SERVICE_URLS//,/ }; do
    host=$(echo $service_url | sed -e 's|^http://||' -e 's|:.*||')
    port=$(echo $service_url | sed -e 's|.*:||' -e 's|/.*||')

    echo "Waiting for $host:$port..."
    timeout 60 bash -c "until nc -z $host $port; do sleep 1; done"
    echo "$host:$port is available"
done

echo "All service dependencies are ready"

# Execute the main command
echo "Starting controller application on port ${SERVICE_PORT}..."
exec "$@"
