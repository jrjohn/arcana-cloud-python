"""
User API Integration Tests
User API integration tests
"""
import pytest
import json


def generate_unique_username(base="user"):
    """Generate unique username with UUID"""
    import uuid
    return f"{base}_{uuid.uuid4().hex[:8]}"


def generate_unique_email(base="test"):
    """Generate unique email with UUID"""
    import uuid
    return f"{base}_{uuid.uuid4().hex[:8]}@example.com"


def create_test_user(client, admin_auth_headers, base="testuser"):
    """Helper to create a test user and return user_id, username, password"""
    import uuid
    username = f"{base}_{uuid.uuid4().hex[:8]}"
    email = f"{base}_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123"

    payload = {
        'username': username,
        'email': email,
        'password': password,
        'first_name': 'Test',
        'last_name': 'User'
    }

    response = client.post(
        '/api/v1/users',
        data=json.dumps(payload),
        headers=admin_auth_headers,
        content_type='application/json'
    )

    if response.status_code != 201:
        raise Exception(f"Failed to create test user: {response.status_code} - {response.data}")

    data = json.loads(response.data)
    user_id = data['data']['id']

    return user_id, username, email, password


def get_user_token(client, username, password):
    """Helper to login and get auth headers for a user"""
    response = client.post(
        '/api/v1/auth/login',
        data=json.dumps({'username_or_email': username, 'password': password}),
        content_type='application/json'
    )

    if response.status_code != 200:
        raise Exception(f"Failed to login: {response.status_code} - {response.data}")

    data = json.loads(response.data)
    token = data['data']['access_token']

    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


class TestUserAPI:
    """User API test class"""

    def test_get_users_as_admin(self, client, db, admin_user, admin_auth_headers):
        """Test admin get user list"""
        # Act
        response = client.get(
            '/api/v1/users?page=1&per_page=20',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'items' in data['data']
        assert 'pagination' in data['data']

    def test_get_users_as_regular_user(self, client, db, admin_auth_headers):
        """Test regular user cannot get user list"""
        # Arrange - Create a regular user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'regularuser')
        user_headers = get_user_token(client, username, password)

        # Act
        response = client.get(
            '/api/v1/users?page=1&per_page=20',
            headers=user_headers
        )

        # Assert
        assert response.status_code == 403

    def test_get_user_by_id_self(self, client, db, admin_auth_headers):
        """Test get own user information"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'selfuser')
        user_headers = get_user_token(client, username, password)

        # Act
        response = client.get(
            f'/api/v1/users/{user_id}',
            headers=user_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == user_id

    def test_update_user_self(self, client, db, admin_auth_headers):
        """Test update own user information"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'updateself')
        user_headers = get_user_token(client, username, password)

        payload = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user_id}',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['first_name'] == 'Updated'

    def test_change_password(self, client, db, admin_auth_headers):
        """Test change password"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'changepass')
        user_headers = get_user_token(client, username, password)

        payload = {
            'old_password': password,
            'new_password': 'NewPass456'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user_id}/password',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_create_user_as_admin(self, client, db, admin_user, admin_auth_headers):
        """Test admin create user"""
        # Arrange
        unique_username = generate_unique_username('createduser')
        unique_email = generate_unique_email('created')
        payload = {
            'username': unique_username,
            'email': unique_email,
            'password': 'CreatedPass123',
            'first_name': 'Created',
            'last_name': 'User'
        }

        # Act
        response = client.post(
            '/api/v1/users',
            data=json.dumps(payload),
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['username'] == unique_username

    def test_delete_user_as_admin(self, client, db, admin_user, admin_auth_headers):
        """Test admin delete user"""
        # Arrange - Create a user to delete
        unique_username = generate_unique_username('deletetestuser')
        unique_email = generate_unique_email('deletetest')
        create_payload = {
            'username': unique_username,
            'email': unique_email,
            'password': 'DeleteTest123',
            'first_name': 'Delete',
            'last_name': 'Test'
        }
        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=admin_auth_headers
        )
        assert create_response.status_code == 201
        created_data = json.loads(create_response.data)
        user_id = created_data['data']['id']

        # Act - Delete the user
        response = client.delete(
            f'/api/v1/users/{user_id}',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_verify_user_as_admin(self, client, db, admin_user, admin_auth_headers):
        """Test admin verify user"""
        # Arrange - Create a user to verify
        unique_username = generate_unique_username('verifytest')
        unique_email = generate_unique_email('verify')
        create_payload = {
            'username': unique_username,
            'email': unique_email,
            'password': 'VerifyTest123',
            'first_name': 'Verify',
            'last_name': 'Test'
        }
        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=admin_auth_headers
        )
        assert create_response.status_code == 201
        created_data = json.loads(create_response.data)
        user_id = created_data['data']['id']

        # Act - Verify the user
        response = client.post(
            f'/api/v1/users/{user_id}/verify',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['is_verified'] is True

    def test_update_user_status_as_admin(self, client, db, admin_user, admin_auth_headers):
        """Test admin update user status"""
        # Arrange - Create a user to update status
        unique_username = generate_unique_username('statustest')
        unique_email = generate_unique_email('status')
        create_payload = {
            'username': unique_username,
            'email': unique_email,
            'password': 'StatusTest123',
            'first_name': 'Status',
            'last_name': 'Test'
        }
        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=admin_auth_headers
        )
        assert create_response.status_code == 201
        created_data = json.loads(create_response.data)
        user_id = created_data['data']['id']

        # Act - Update the user status
        payload = {
            'status': 'suspended'
        }
        response = client.put(
            f'/api/v1/users/{user_id}/status',
            data=json.dumps(payload),
            headers=admin_auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_user_permission_denied(self, client, db, admin_user, admin_auth_headers):
        """Test regular user cannot view other users"""
        # Arrange - Create a regular user and another target user
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'viewinguser')
        user_headers = get_user_token(client, username, password)

        # Create another user to try to view
        target_id, _, _, _ = create_test_user(client, admin_auth_headers, 'targetuser')

        # Act - try to view target user as regular user
        response = client.get(
            f'/api/v1/users/{target_id}',
            headers=user_headers
        )

        # Assert
        assert response.status_code == 403

    def test_update_other_user_permission_denied(self, client, db, admin_auth_headers):
        """Test regular user cannot update other users"""
        # Arrange - Create a regular user and another target user
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'updatinguser')
        user_headers = get_user_token(client, username, password)

        # Create another user to try to update
        target_id, _, _, _ = create_test_user(client, admin_auth_headers, 'updatetarget')

        payload = {
            'first_name': 'Hacked'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{target_id}',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code == 403

    def test_create_user_as_regular_user(self, client, db, admin_auth_headers):
        """Test regular user cannot create users"""
        # Arrange - Create a regular user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'creatinguser')
        user_headers = get_user_token(client, username, password)

        payload = {
            'username': generate_unique_username('unauthorized'),
            'email': generate_unique_email('unauthorized'),
            'password': 'Unauthorized123'
        }

        # Act
        response = client.post(
            '/api/v1/users',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code == 403

    def test_delete_user_as_regular_user(self, client, db, admin_auth_headers):
        """Test regular user cannot delete users"""
        # Arrange - Create a regular user and another target user
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'deletinguser')
        user_headers = get_user_token(client, username, password)

        # Create another user to try to delete
        target_id, _, _, _ = create_test_user(client, admin_auth_headers, 'deletetarget')

        # Act
        response = client.delete(
            f'/api/v1/users/{target_id}',
            headers=user_headers
        )

        # Assert
        assert response.status_code == 403

    def test_change_password_wrong_old_password(self, client, db, admin_auth_headers):
        """Test change password with wrong old password"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'wrongpass')
        user_headers = get_user_token(client, username, password)

        payload = {
            'old_password': 'WrongOldPass123',
            'new_password': 'NewPass456'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user_id}/password',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code in [400, 401]

    def test_change_password_weak_new_password(self, client, db, admin_auth_headers):
        """Test change password with weak new password"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'weakpass')
        user_headers = get_user_token(client, username, password)

        payload = {
            'old_password': password,
            'new_password': 'weak'  # Too weak
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user_id}/password',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code == 400

    def test_get_users_with_filters(self, client, db, admin_user, admin_auth_headers):
        """Test get users with role and status filters"""
        # Act
        response = client.get(
            '/api/v1/users?page=1&per_page=20&role=user&status=active',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_update_user_invalid_email(self, client, db, admin_auth_headers):
        """Test update user with invalid email"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'invalidemail')
        user_headers = get_user_token(client, username, password)

        payload = {
            'email': 'not-valid-email'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user_id}',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code == 400

    def test_update_user_duplicate_email(self, client, db, admin_auth_headers):
        """Test update user with duplicate email"""
        # Arrange - Create two users
        user1_id, user1_username, user1_email, user1_password = create_test_user(client, admin_auth_headers, 'dupuser1')
        user1_headers = get_user_token(client, user1_username, user1_password)

        user2_id, user2_username, user2_email, user2_password = create_test_user(client, admin_auth_headers, 'dupuser2')

        # Try to update user1 to have user2's email
        payload = {
            'email': user2_email
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user1_id}',
            data=json.dumps(payload),
            headers=user1_headers
        )

        # Assert
        assert response.status_code in [400, 409]


class TestUserAPIEdgeCases:
    """User API edge cases and boundary tests"""

    def test_get_nonexistent_user(self, client, db, admin_user, admin_auth_headers):
        """Test get non-existent user"""
        # Act
        response = client.get(
            '/api/v1/users/99999',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_nonexistent_user(self, client, db, admin_user, admin_auth_headers):
        """Test update non-existent user"""
        # Arrange
        payload = {
            'first_name': 'Does',
            'last_name': 'NotExist'
        }

        # Act
        response = client.put(
            '/api/v1/users/99999',
            data=json.dumps(payload),
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_delete_nonexistent_user(self, client, db, admin_user, admin_auth_headers):
        """Test delete non-existent user"""
        # Act
        response = client.delete(
            '/api/v1/users/99999',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_verify_nonexistent_user(self, client, db, admin_user, admin_auth_headers):
        """Test verify non-existent user"""
        # Act
        response = client.post(
            '/api/v1/users/99999/verify',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_pagination_boundary_values(self, client, db, admin_user, admin_auth_headers):
        """Test pagination with boundary values"""
        # Test page 0
        response = client.get(
            '/api/v1/users?page=0&per_page=10',
            headers=admin_auth_headers
        )
        assert response.status_code in [200, 400]

        # Test negative page
        response = client.get(
            '/api/v1/users?page=-1&per_page=10',
            headers=admin_auth_headers
        )
        assert response.status_code in [200, 400]

        # Test very large per_page (exceeds max_per_page of 100)
        response = client.get(
            '/api/v1/users?page=1&per_page=10000',
            headers=admin_auth_headers
        )
        assert response.status_code == 400  # Should be rejected

    def test_invalid_role_filter(self, client, db, admin_user, admin_auth_headers):
        """Test get users with invalid role filter"""
        # Act
        response = client.get(
            '/api/v1/users?role=invalid_role',
            headers=admin_auth_headers
        )

        # Assert - should return 400 error with valid roles
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_ROLE' in str(data.get('error', {}))

    def test_invalid_status_filter(self, client, db, admin_user, admin_auth_headers):
        """Test get users with invalid status filter"""
        # Act
        response = client.get(
            '/api/v1/users?status=invalid_status',
            headers=admin_auth_headers
        )

        # Assert - should return 400 error with valid statuses
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_STATUS' in str(data.get('error', {}))

    def test_update_user_status_invalid_value(self, client, db, admin_user, admin_auth_headers):
        """Test update user status with invalid value"""
        # Arrange - Create a user to test with
        unique_username = generate_unique_username('invalidstatustest')
        unique_email = generate_unique_email('invalidstatus')
        create_payload = {
            'username': unique_username,
            'email': unique_email,
            'password': 'InvalidStatus123',
            'first_name': 'Invalid',
            'last_name': 'Status'
        }
        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=admin_auth_headers
        )
        assert create_response.status_code == 201
        created_data = json.loads(create_response.data)
        user_id = created_data['data']['id']

        # Act - Try to set invalid status
        payload = {
            'status': 'invalid_status'
        }
        response = client.put(
            f'/api/v1/users/{user_id}/status',
            data=json.dumps(payload),
            headers=admin_auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_update_user_status_missing_value(self, client, db, admin_user, admin_auth_headers):
        """Test update user status without status value"""
        # Arrange - Create a user to test with
        unique_username = generate_unique_username('missingstatustest')
        unique_email = generate_unique_email('missingstatus')
        create_payload = {
            'username': unique_username,
            'email': unique_email,
            'password': 'MissingStatus123',
            'first_name': 'Missing',
            'last_name': 'Status'
        }
        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=admin_auth_headers
        )
        assert create_response.status_code == 201
        created_data = json.loads(create_response.data)
        user_id = created_data['data']['id']

        # Act - Try to update status without value
        payload = {}
        response = client.put(
            f'/api/v1/users/{user_id}/status',
            data=json.dumps(payload),
            headers=admin_auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_user_endpoints_without_authentication(self, client, db, admin_auth_headers):
        """Test user endpoints without authentication"""
        # Create a test user to use in tests (but don't use its token)
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'noauthtest')

        # Test GET list
        response = client.get('/api/v1/users')
        assert response.status_code == 401

        # Test GET single
        response = client.get(f'/api/v1/users/{user_id}')
        assert response.status_code == 401

        # Test POST
        payload = {
            'username': generate_unique_username('test'),
            'email': generate_unique_email('test'),
            'password': 'Test123'
        }
        response = client.post(
            '/api/v1/users',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 401

        # Test PUT
        response = client.put(
            f'/api/v1/users/{user_id}',
            data=json.dumps({'first_name': 'Test'}),
            content_type='application/json'
        )
        assert response.status_code == 401

        # Test DELETE
        response = client.delete(f'/api/v1/users/{user_id}')
        assert response.status_code == 401

    def test_special_characters_in_user_fields(self, client, db, admin_auth_headers):
        """Test special characters in user update fields"""
        # Arrange - Create a user and get their token
        user_id, username, email, password = create_test_user(client, admin_auth_headers, 'specialchars')
        user_headers = get_user_token(client, username, password)

        payload = {
            'first_name': "O'Brien",
            'last_name': 'José-María',
            'phone': '+1-234-567-8900'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{user_id}',
            data=json.dumps(payload),
            headers=user_headers
        )

        # Assert
        assert response.status_code in [200, 400]
