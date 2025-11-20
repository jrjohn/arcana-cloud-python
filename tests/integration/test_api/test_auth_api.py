"""
Auth API Integration Tests
Authentication API integration tests
"""
import pytest
import json


class TestAuthAPI:
    """Authentication API test class"""

    def test_register_success(self, client, db):
        """Test successful registration"""
        # Arrange
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['username'] == 'newuser'

    def test_register_duplicate_username(self, client, db, sample_user):
        """Test duplicate username registration"""
        # Arrange
        payload = {
            'username': 'testuser',  # Same as sample_user
            'email': 'different@example.com',
            'password': 'NewPass123'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['success'] is False

    def test_login_success(self, client, db, sample_user):
        """Test successful login"""
        # Arrange
        payload = {
            'username_or_email': 'testuser',
            'password': 'TestPass123'
        }

        # Act
        response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['user']['username'] == 'testuser'

    def test_login_invalid_password(self, client, db, sample_user):
        """Test login with invalid password"""
        # Arrange
        payload = {
            'username_or_email': 'testuser',
            'password': 'WrongPassword'
        }

        # Act
        response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False

    def test_get_current_user(self, client, db, sample_user, auth_headers):
        """Test get current user information"""
        # Act
        response = client.get(
            '/api/v1/auth/me',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['username'] == 'testuser'

    def test_get_current_user_without_token(self, client, db):
        """Test get user information without authentication"""
        # Act
        response = client.get('/api/v1/auth/me')

        # Assert
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False

    def test_logout_success(self, client, db, sample_user, auth_headers):
        """Test successful logout"""
        # Act
        response = client.post(
            '/api/v1/auth/logout',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_refresh_token_success(self, client, db, sample_token):
        """Test refresh token"""
        # Arrange
        payload = {
            'refresh_token': sample_token.refresh_token
        }

        # Act
        response = client.post(
            '/api/v1/auth/refresh',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data['data']
