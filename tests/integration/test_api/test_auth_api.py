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

    def test_get_user_tokens(self, client, db, sample_user, auth_headers):
        """Test get all user tokens"""
        # Act
        response = client.get(
            '/api/v1/auth/tokens',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'tokens' in data['data']
        assert isinstance(data['data']['tokens'], list)

    def test_revoke_all_tokens(self, client, db, sample_user, auth_headers):
        """Test revoke all user tokens"""
        # Act
        response = client.post(
            '/api/v1/auth/tokens/revoke-all',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'revoked_count' in data['data']

    def test_register_missing_required_fields(self, client, db):
        """Test registration with missing required fields"""
        # Arrange
        payload = {
            'username': 'incomplete'
            # Missing email and password
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_register_weak_password(self, client, db):
        """Test registration with weak password"""
        # Arrange
        payload = {
            'username': 'weakpass',
            'email': 'weak@example.com',
            'password': 'weak'  # Too short, no uppercase, no digits
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_register_invalid_email(self, client, db):
        """Test registration with invalid email"""
        # Arrange
        payload = {
            'username': 'invalidemail',
            'email': 'not-an-email',
            'password': 'ValidPass123'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_login_with_email(self, client, db, sample_user):
        """Test login using email instead of username"""
        # Arrange
        payload = {
            'username_or_email': sample_user.email,
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

    def test_login_nonexistent_user(self, client, db):
        """Test login with non-existent user"""
        # Arrange
        payload = {
            'username_or_email': 'doesnotexist',
            'password': 'AnyPass123'
        }

        # Act
        response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 401

    def test_refresh_token_invalid(self, client, db):
        """Test refresh with invalid token"""
        # Arrange
        payload = {
            'refresh_token': 'invalid_refresh_token'
        }

        # Act
        response = client.post(
            '/api/v1/auth/refresh',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code in [401, 400]

    def test_refresh_token_missing(self, client, db):
        """Test refresh without token"""
        # Arrange
        payload = {}

        # Act
        response = client.post(
            '/api/v1/auth/refresh',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_protected_endpoint_invalid_token(self, client, db):
        """Test protected endpoint with invalid token"""
        # Arrange
        headers = {
            'Authorization': 'Bearer invalid_token_here'
        }

        # Act
        response = client.get(
            '/api/v1/auth/me',
            headers=headers
        )

        # Assert
        assert response.status_code == 401

    def test_protected_endpoint_malformed_header(self, client, db):
        """Test protected endpoint with malformed auth header"""
        # Arrange
        headers = {
            'Authorization': 'invalid_format'
        }

        # Act
        response = client.get(
            '/api/v1/auth/me',
            headers=headers
        )

        # Assert
        assert response.status_code == 401

    def test_logout_without_token(self, client, db):
        """Test logout without token"""
        # Act
        response = client.post('/api/v1/auth/logout')

        # Assert
        assert response.status_code == 401


class TestAuthAPIEdgeCases:
    """Auth API edge cases and security tests"""

    def test_sql_injection_in_login(self, client, db):
        """Test SQL injection attempt in login"""
        # Arrange
        payload = {
            'username_or_email': "admin' OR '1'='1",
            'password': "password' OR '1'='1"
        }

        # Act
        response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 401  # Should fail, not succeed

    def test_xss_in_registration(self, client, db):
        """Test XSS attempt in registration"""
        # Arrange
        payload = {
            'username': '<script>alert("XSS")</script>',
            'email': 'xss@example.com',
            'password': 'XssTest123',
            'first_name': '<script>alert("XSS")</script>',
            'last_name': 'Test'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert - should either sanitize or reject
        assert response.status_code in [201, 400]

    def test_multiple_rapid_login_attempts(self, client, db, sample_user):
        """Test multiple rapid login attempts (rate limiting check)"""
        # Arrange
        payload = {
            'username_or_email': 'testuser',
            'password': 'WrongPassword'
        }

        # Act - make 5 rapid failed attempts
        responses = []
        for _ in range(5):
            response = client.post(
                '/api/v1/auth/login',
                data=json.dumps(payload),
                content_type='application/json'
            )
            responses.append(response)

        # Assert - all should fail (rate limiting may or may not be implemented)
        for response in responses:
            assert response.status_code in [401, 429]  # 429 = Too Many Requests

    def test_very_long_username(self, client, db):
        """Test registration with very long username"""
        # Arrange
        payload = {
            'username': 'a' * 1000,
            'email': 'longusername@example.com',
            'password': 'LongUser123'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400  # Should validate length

    def test_unicode_in_credentials(self, client, db):
        """Test unicode characters in credentials"""
        # Arrange
        payload = {
            'username': '用户名',
            'email': 'unicode@example.com',
            'password': 'Unicode123密码'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert - should handle unicode appropriately
        assert response.status_code in [201, 400]

    def test_null_byte_in_password(self, client, db):
        """Test null byte in password"""
        # Arrange
        payload = {
            'username': 'nullbyte',
            'email': 'null@example.com',
            'password': 'Pass\x00word123'
        }

        # Act
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Assert - should handle safely
        assert response.status_code in [201, 400]

    def test_case_sensitivity_in_login(self, client, db, sample_user):
        """Test case sensitivity in username/email login"""
        # Test uppercase username
        payload = {
            'username_or_email': 'TESTUSER',
            'password': 'TestPass123'
        }

        response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Behavior depends on implementation (case-sensitive or not)
        assert response.status_code in [200, 401]
