#!/usr/bin/env python3
"""
Simple API test script to verify Monolithic mode with DI
"""
import requests
import json
import time

BASE_URL = "http://localhost:5555"

def test_health():
    """Test health endpoints"""
    print("=" * 60)
    print("Testing Health Endpoints")
    print("=" * 60)

    # Health check
    response = requests.get(f"{BASE_URL}/health")
    print(f"\n✓ GET /health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    # Readiness check
    response = requests.get(f"{BASE_URL}/ready")
    print(f"\n✓ GET /ready")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")


def test_auth_flow():
    """Test complete authentication flow"""
    print("\n" + "=" * 60)
    print("Testing Authentication Flow")
    print("=" * 60)

    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    email = f"testuser_{timestamp}@example.com"
    password = "SecurePass123"

    # 1. Register
    print(f"\n1. Registering user: {username}")
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "User"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=register_data
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code != 201:
        print("  ✗ Registration failed!")
        return None

    print("  ✓ Registration successful")

    # 2. Login
    print(f"\n2. Logging in: {username}")
    login_data = {
        "username_or_email": username,
        "password": password
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=login_data
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code != 200:
        print("  ✗ Login failed!")
        return None

    print("  ✓ Login successful")

    # Extract tokens
    token_data = response.json()['data']
    access_token = token_data['access_token']
    user_id = token_data['user']['id']

    # 3. Get current user
    print(f"\n3. Getting current user info")
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers=headers
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code != 200:
        print("  ✗ Get user info failed!")
        return None

    print("  ✓ Get user info successful")

    return {
        "access_token": access_token,
        "user_id": user_id,
        "username": username
    }


def test_public_users():
    """Test public user endpoints (no auth required)"""
    print("\n" + "=" * 60)
    print("Testing Public User Endpoints")
    print("=" * 60)

    # List users
    print(f"\n1. Listing public users")
    response = requests.get(f"{BASE_URL}/api/public/users?page=1&per_page=5")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("  ✓ List users successful")
        users = response.json()['data']['items']
        if users:
            user_id = users[0]['id']

            # Get specific user
            print(f"\n2. Getting user details (ID: {user_id})")
            response = requests.get(f"{BASE_URL}/api/public/users/{user_id}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {json.dumps(response.json(), indent=2)}")

            if response.status_code == 200:
                print("  ✓ Get user details successful")
    else:
        print("  ✗ List users failed!")


def test_user_management(auth_data):
    """Test user management endpoints (requires auth)"""
    if not auth_data:
        print("\nSkipping user management tests (no auth data)")
        return

    print("\n" + "=" * 60)
    print("Testing User Management Endpoints")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
    user_id = auth_data['user_id']

    # 1. Get user by ID
    print(f"\n1. Getting user by ID: {user_id}")
    response = requests.get(
        f"{BASE_URL}/api/v1/users/{user_id}",
        headers=headers
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("  ✓ Get user successful")
    else:
        print("  ✗ Get user failed!")

    # 2. Update user
    print(f"\n2. Updating user: {user_id}")
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "phone": "+1234567890"
    }

    response = requests.put(
        f"{BASE_URL}/api/v1/users/{user_id}",
        headers=headers,
        json=update_data
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("  ✓ Update user successful")
    else:
        print("  ✗ Update user failed!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MONOLITHIC MODE API TESTING")
    print("Testing Dependency Injection Implementation")
    print("=" * 60)

    try:
        # Test health
        test_health()

        # Test public endpoints
        test_public_users()

        # Test auth flow
        auth_data = test_auth_flow()

        # Test user management
        test_user_management(auth_data)

        print("\n" + "=" * 60)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to Flask application")
        print("  Make sure the app is running on http://localhost:5555")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
