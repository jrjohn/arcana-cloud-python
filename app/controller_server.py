"""
Controller Layer Server Entry Point
Handles HTTP requests, routing, and API endpoints
"""
import os
from app import create_app

# Get configuration from environment
config_name = os.getenv('FLASK_ENV', 'production')

# Create Flask application for controller layer
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(config_name == 'development')
    )
