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
from app.models.user import User, UserRole, UserStatus

def init_database():
    """Initialize database schema and create test users"""
    app = create_app('testing')

    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database schema created successfully")

        # Create test users if they don't exist
        testuser = User.query.filter_by(username='testuser').first()
        if not testuser:
            testuser = User(
                username='testuser',
                email='test@example.com',
                password=os.environ.get('TEST_USER_PASSWORD', '')
            )
            testuser.first_name = 'Test'
            testuser.last_name = 'User'
            testuser.role = UserRole.USER
            testuser.status = UserStatus.ACTIVE
            testuser.is_active = True
            db.session.add(testuser)
            print("✅ Created test user: testuser")
        else:
            # Reset password in case it was changed
            testuser.setPassword(os.environ.get('TEST_USER_PASSWORD', ''))
            testuser.status = UserStatus.ACTIVE
            testuser.is_active = True
            print("✅ Updated test user: testuser")

        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=os.environ.get('ADMIN_INIT_PASSWORD', '')
            )
            admin_user.first_name = 'Admin'
            admin_user.last_name = 'User'
            admin_user.role = UserRole.ADMIN
            admin_user.status = UserStatus.ACTIVE
            admin_user.is_active = True
            db.session.add(admin_user)
            print("✅ Created admin user: admin")
        else:
            # Reset password in case it was changed
            admin_user.setPassword(os.environ.get('ADMIN_INIT_PASSWORD', ''))
            admin_user.status = UserStatus.ACTIVE
            admin_user.is_active = True
            print("✅ Updated admin user: admin")

        db.session.commit()
        print("✅ Test users initialized successfully")

if __name__ == '__main__':
    init_database()
