#!/bin/bash
# ============================================================================
# Repository Layer Entrypoint
# ============================================================================
# Initializes the repository layer and runs database migrations
# ============================================================================

set -e

echo "============================================"
echo "Starting Arcana Cloud - Repository Layer"
echo "============================================"

# Extract database host and port from DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | sed -e 's|.*@||' -e 's|:.*||')
DB_PORT=$(echo $DATABASE_URL | sed -e 's|.*:||' -e 's|/.*||')

# Wait for database to be ready
echo "Waiting for database ${DB_HOST}:${DB_PORT}..."
timeout 90 bash -c "until nc -z ${DB_HOST} ${DB_PORT}; do sleep 1; done"
echo "Database is available"

# Wait for Redis to be ready
if [ ! -z "$REDIS_URL" ]; then
    REDIS_HOST=$(echo $REDIS_URL | sed -e 's|.*://||' -e 's|:.*||')
    REDIS_PORT=$(echo $REDIS_URL | sed -e 's|.*:||' -e 's|/.*||')

    echo "Waiting for Redis ${REDIS_HOST}:${REDIS_PORT}..."
    timeout 60 bash -c "until nc -z ${REDIS_HOST} ${REDIS_PORT}; do sleep 1; done"
    echo "Redis is available"
fi

# Run database migrations (only in repository layer)
echo "Running database migrations..."
flask db upgrade || {
    echo "Warning: Database migration failed. Continuing startup..."
}

echo "Repository layer initialization complete"

# Execute the main command
echo "Starting repository application on port ${SERVICE_PORT}..."
exec "$@"
