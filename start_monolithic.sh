#!/bin/bash
#
# Start Flask in Monolithic Mode with SQLite
#

set -e

echo "============================================================"
echo "Starting Arcana Cloud in Monolithic Mode"
echo "============================================================"

# Set environment variables
export DEPLOYMENT_MODE=monolithic
export DEPLOYMENT_LAYER=monolithic
export DATABASE_URL="sqlite:////Users/jrjohn/Documents/projects/arcana-cloud-python/arcana_test.db"

echo ""
echo "Configuration:"
echo "  DEPLOYMENT_MODE: $DEPLOYMENT_MODE"
echo "  DEPLOYMENT_LAYER: $DEPLOYMENT_LAYER"
echo "  DATABASE_URL: $DATABASE_URL"

# Verify database exists
if [ ! -f "/Users/jrjohn/Documents/projects/arcana-cloud-python/arcana_test.db" ]; then
    echo ""
    echo "Error: Database file not found!"
    echo "Run: export DATABASE_URL='sqlite:////Users/jrjohn/Documents/projects/arcana-cloud-python/arcana_test.db' && python3 init_db.py"
    exit 1
fi

echo ""
echo "Database file: $(ls -lh /Users/jrjohn/Documents/projects/arcana-cloud-python/arcana_test.db | awk '{print $5}')"

# Kill any existing Flask process
echo ""
echo "Checking for existing Flask processes..."
if lsof -ti:5555 > /dev/null 2>&1; then
    echo "Killing existing process on port 5555..."
    lsof -ti:5555 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Activate virtualenv and start Flask
echo ""
echo "Starting Flask application..."
source venv/bin/activate

# Start Flask in foreground (use & for background)
python3 -m flask --app wsgi run --port 5555
