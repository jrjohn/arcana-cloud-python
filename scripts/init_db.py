#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and optionally seeds data
"""
import os
import sys

# Set deployment mode
os.environ['DEPLOYMENT_MODE'] = 'monolithic'
os.environ['DEPLOYMENT_LAYER'] = 'monolithic'

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole, UserStatus

def init_database():
    """Initialize database with tables"""
    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)

    app = create_app('development')

    with app.app_context():
        print("\n1. Dropping all existing tables...")
        db.drop_all()
        print("   ✓ All tables dropped")

        print("\n2. Creating all tables...")
        db.create_all()
        print("   ✓ All tables created")

        print("\n3. Creating admin user...")
        try:
            # Check if admin exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@arcana.com',
                    password=os.environ.get('ADMIN_INIT_PASSWORD', ''),
                    first_name='System',
                    last_name='Administrator',
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    is_verified=True,
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print(f"   ✓ Admin user created (username: admin)")
            else:
                print(f"   ! Admin user already exists")
        except Exception as e:
            print(f"   ✗ Error creating admin: {str(e)}")
            db.session.rollback()

        print("\n4. Creating test users...")
        try:
            # Create a few test users
            test_users = [
                {
                    'username': 'testuser1',
                    'email': 'testuser1@example.com',
                    'password': os.environ.get('TEST_USER_PASSWORD', ''),
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'role': UserRole.USER
                },
                {
                    'username': 'testuser2',
                    'email': 'testuser2@example.com',
                    'password': os.environ.get('TEST_USER_PASSWORD', ''),
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'role': UserRole.USER
                },
            ]

            for user_data in test_users:
                # Check if user exists
                existing = User.query.filter_by(username=user_data['username']).first()
                if not existing:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        role=user_data['role'],
                        status=UserStatus.ACTIVE,
                        is_verified=True,
                        is_active=True
                    )
                    db.session.add(user)
                    print(f"   ✓ Created user: {user_data['username']}")
                else:
                    print(f"   ! User already exists: {user_data['username']}")

            db.session.commit()
            print(f"   ✓ Test users created")

        except Exception as e:
            print(f"   ✗ Error creating test users: {str(e)}")
            db.session.rollback()

        # Summary
        print("\n" + "=" * 60)
        print("Database Initialization Complete")
        print("=" * 60)

        # Count users
        user_count = User.query.count()
        admin_count = User.query.filter_by(role=UserRole.ADMIN).count()

        print(f"\nTotal users: {user_count}")
        print(f"Admin users: {admin_count}")
        print(f"Regular users: {user_count - admin_count}")

        print("\n✓ Ready to test API!")


if __name__ == '__main__':
    init_database()
