#!/usr/bin/env python3
"""Create test users in MySQL database"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test'
os.environ['TEST_DATABASE_URL'] = 'mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test'

from app import create_app
from app.Extensions import db
from app.models.user import User, UserRole

def create_test_users():
    """Create test users"""
    app = create_app('testing')

    with app.app_context():
        # Check if users already exist
        testuser = db.session.query(User).filter_by(username='testuser').first()
        admin = db.session.query(User).filter_by(username='admin').first()

        if not testuser:
            testuser = User(
                username='testuser',
                email='test@example.com',
                password='TestPass123',
                role=UserRole.USER
            )
            db.session.add(testuser)
            print(f"✅ Created testuser (password: TestPass123)")
        else:
            print(f"ℹ️  testuser already exists (id={testuser.id})")

        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password='AdminPass123',
                role=UserRole.ADMIN
            )
            db.session.add(admin)
            print(f"✅ Created admin (password: AdminPass123)")
        else:
            print(f"ℹ️  admin already exists (id={admin.id})")

        db.session.commit()
        print(f"\n✅ Test users ready in database")

if __name__ == '__main__':
    create_test_users()
