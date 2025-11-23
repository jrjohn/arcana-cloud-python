#!/usr/bin/env python3
"""
Initialize test database with schema
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DEPLOYMENT_LAYER'] = 'repository'  # Repository layer has DB access

from app import create_app
from app.Extensions import db

def init_database():
    """Initialize database schema"""
    app = create_app('testing')

    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database schema created successfully")

if __name__ == '__main__':
    init_database()
