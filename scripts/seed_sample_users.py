#!/usr/bin/env python3
"""
Sample Users Seeder Script
Generate 28 sample users for testing Public User API
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.Extensions import db
from app.models.user import User, UserRole, UserStatus
from datetime import datetime


def generate_avatar_url(user_id: int, first_name: str) -> str:
    """
    Generate avatar URL using UI Avatars service (free, no copyright issues)
    https://ui-avatars.com/
    """
    # Use first letter of first name and user ID for unique avatars
    initials = first_name[0].upper()
    # Generate different background colors based on user_id
    colors = ['007bff', '28a745', 'dc3545', 'ffc107', '17a2b8', '6610f2', 'fd7e14', '20c997']
    bg_color = colors[user_id % len(colors)]

    return f"https://ui-avatars.com/api/?name={first_name}&background={bg_color}&color=fff&size=128"


# Sample user data (28 users) - Using common international names
SAMPLE_USERS = [
    {"first_name": "Alex", "last_name": "Chen", "email": "alex.chen@example.com"},
    {"first_name": "Maya", "last_name": "Patel", "email": "maya.patel@example.com"},
    {"first_name": "James", "last_name": "Wilson", "email": "james.wilson@example.com"},
    {"first_name": "Sofia", "last_name": "Rodriguez", "email": "sofia.rodriguez@example.com"},
    {"first_name": "Liam", "last_name": "O'Brien", "email": "liam.obrien@example.com"},
    {"first_name": "Emma", "last_name": "Schmidt", "email": "emma.schmidt@example.com"},
    {"first_name": "Noah", "last_name": "Kim", "email": "noah.kim@example.com"},
    {"first_name": "Olivia", "last_name": "Nguyen", "email": "olivia.nguyen@example.com"},
    {"first_name": "Lucas", "last_name": "Silva", "email": "lucas.silva@example.com"},
    {"first_name": "Ava", "last_name": "Johnson", "email": "ava.johnson@example.com"},
    {"first_name": "Ethan", "last_name": "Zhang", "email": "ethan.zhang@example.com"},
    {"first_name": "Isabella", "last_name": "Martinez", "email": "isabella.martinez@example.com"},
    {"first_name": "Mason", "last_name": "Anderson", "email": "mason.anderson@example.com"},
    {"first_name": "Mia", "last_name": "Taylor", "email": "mia.taylor@example.com"},
    {"first_name": "Logan", "last_name": "Lee", "email": "logan.lee@example.com"},
    {"first_name": "Charlotte", "last_name": "Brown", "email": "charlotte.brown@example.com"},
    {"first_name": "Jack", "last_name": "Davis", "email": "jack.davis@example.com"},
    {"first_name": "Amelia", "last_name": "Garcia", "email": "amelia.garcia@example.com"},
    {"first_name": "Aiden", "last_name": "Miller", "email": "aiden.miller@example.com"},
    {"first_name": "Harper", "last_name": "Moore", "email": "harper.moore@example.com"},
    {"first_name": "Elijah", "last_name": "White", "email": "elijah.white@example.com"},
    {"first_name": "Ella", "last_name": "Lopez", "email": "ella.lopez@example.com"},
    {"first_name": "Oliver", "last_name": "Hall", "email": "oliver.hall@example.com"},
    {"first_name": "Aria", "last_name": "Young", "email": "aria.young@example.com"},
    {"first_name": "William", "last_name": "Allen", "email": "william.allen@example.com"},
    {"first_name": "Luna", "last_name": "King", "email": "luna.king@example.com"},
    {"first_name": "Benjamin", "last_name": "Wright", "email": "benjamin.wright@example.com"},
    {"first_name": "Zoe", "last_name": "Scott", "email": "zoe.scott@example.com"},
]


def seed_users(app):
    """Seed sample users into database"""
    with app.app_context():
        print("🌱 Starting user seeding process...")
        print(f"📊 Target: {len(SAMPLE_USERS)} users")

        # Check existing users
        existing_count = User.query.count()
        print(f"📈 Current users in database: {existing_count}")

        created_count = 0
        skipped_count = 0

        for idx, user_data in enumerate(SAMPLE_USERS, 1):
            # Generate username from email
            username = user_data['email'].split('@')[0]

            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == user_data['email']) | (User.username == username)
            ).first()

            if existing_user:
                print(f"⏭️  [{idx:2d}/28] Skipped: {user_data['first_name']} {user_data['last_name']} (already exists)")
                skipped_count += 1
                continue

            # Generate avatar URL for this user
            avatar_url = generate_avatar_url(idx, user_data['first_name'])

            # Create new user
            user = User(
                username=username,
                email=user_data['email'],
                password='Password123',  # Default password for all sample users
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                avatar_url=avatar_url,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                is_verified=True,
                is_active=True
            )

            try:
                db.session.add(user)
                db.session.commit()
                created_count += 1
                print(f"✅ [{idx:2d}/28] Created: {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
            except Exception as e:
                db.session.rollback()
                print(f"❌ [{idx:2d}/28] Failed: {user_data['first_name']} {user_data['last_name']} - {str(e)}")

        # Final summary
        print("\n" + "="*60)
        print("📊 Seeding Summary:")
        print(f"   ✅ Created: {created_count} users")
        print(f"   ⏭️  Skipped: {skipped_count} users (already existed)")
        print(f"   📈 Total users in database: {User.query.count()}")
        print("="*60)

        return created_count


def verify_seeding(app):
    """Verify that users were created successfully"""
    with app.app_context():
        print("\n🔍 Verifying seeded users...")

        total_users = User.query.count()
        print(f"📊 Total users: {total_users}")

        # Show first 5 users
        users = User.query.limit(5).all()
        print("\n📋 Sample users (first 5):")
        for user in users:
            print(f"   {user.id:3d}. {user.first_name} {user.last_name} ({user.email})")

        print(f"\n✅ Verification complete!")


if __name__ == '__main__':
    # Create app with testing configuration
    app = create_app('development')

    print("="*60)
    print("🚀 Sample Users Seeder")
    print("="*60)

    # Seed users
    created = seed_users(app)

    if created > 0:
        # Verify seeding
        verify_seeding(app)

    print("\n✨ Seeding process completed!")
