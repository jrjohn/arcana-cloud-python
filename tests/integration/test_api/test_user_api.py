"""
User API Integration Tests
User API integration tests
"""
import pytest
import json


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

    def test_get_users_as_regular_user(self, client, db, sample_user, auth_headers):
        """Test regular user cannot get user list"""
        # Act
        response = client.get(
            '/api/v1/users?page=1&per_page=20',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_get_user_by_id_self(self, client, db, sample_user, auth_headers):
        """Test get own user information"""
        # Act
        response = client.get(
            f'/api/v1/users/{sample_user.id}',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == sample_user.id

    def test_update_user_self(self, client, db, sample_user, auth_headers):
        """Test update own user information"""
        # Arrange
        payload = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['first_name'] == 'Updated'

    def test_change_password(self, client, db, sample_user, auth_headers):
        """Test change password"""
        # Arrange
        payload = {
            'old_password': 'TestPass123',
            'new_password': 'NewPass456'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}/password',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_create_user_as_admin(self, client, db, admin_user, admin_auth_headers):
        """Test admin create user"""
        # Arrange
        payload = {
            'username': 'createduser',
            'email': 'created@example.com',
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
        assert data['data']['username'] == 'createduser'

    def test_delete_user_as_admin(self, client, db, sample_user, admin_user, admin_auth_headers):
        """Test admin delete user"""
        # Act
        response = client.delete(
            f'/api/v1/users/{sample_user.id}',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_verify_user_as_admin(self, client, db, sample_user, admin_user, admin_auth_headers):
        """Test admin verify user"""
        # Act
        response = client.post(
            f'/api/v1/users/{sample_user.id}/verify',
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['is_verified'] is True
