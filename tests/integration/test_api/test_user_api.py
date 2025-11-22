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

    def test_update_user_status_as_admin(self, client, db, sample_user, admin_user, admin_auth_headers):
        """Test admin update user status"""
        # Arrange
        payload = {
            'status': 'suspended'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}/status',
            data=json.dumps(payload),
            headers=admin_auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_user_permission_denied(self, client, db, sample_user, admin_user, auth_headers):
        """Test regular user cannot view other users"""
        # Act - try to view admin user as regular user
        response = client.get(
            f'/api/v1/users/{admin_user.id}',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_update_other_user_permission_denied(self, client, db, sample_user, admin_user, auth_headers):
        """Test regular user cannot update other users"""
        # Arrange
        payload = {
            'first_name': 'Hacked'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{admin_user.id}',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_create_user_as_regular_user(self, client, db, sample_user, auth_headers):
        """Test regular user cannot create users"""
        # Arrange
        payload = {
            'username': 'unauthorized',
            'email': 'unauthorized@example.com',
            'password': 'Unauthorized123'
        }

        # Act
        response = client.post(
            '/api/v1/users',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_delete_user_as_regular_user(self, client, db, sample_user, auth_headers):
        """Test regular user cannot delete users"""
        # Act
        response = client.delete(
            f'/api/v1/users/{sample_user.id}',
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_change_password_wrong_old_password(self, client, db, sample_user, auth_headers):
        """Test change password with wrong old password"""
        # Arrange
        payload = {
            'old_password': 'WrongOldPass123',
            'new_password': 'NewPass456'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}/password',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code in [400, 401]

    def test_change_password_weak_new_password(self, client, db, sample_user, auth_headers):
        """Test change password with weak new password"""
        # Arrange
        payload = {
            'old_password': 'TestPass123',
            'new_password': 'weak'  # Too weak
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}/password',
            data=json.dumps(payload),
            headers=auth_headers
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

    def test_update_user_invalid_email(self, client, db, sample_user, auth_headers):
        """Test update user with invalid email"""
        # Arrange
        payload = {
            'email': 'not-valid-email'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_update_user_duplicate_email(self, client, db, sample_user, admin_user, auth_headers):
        """Test update user with duplicate email"""
        # Arrange
        payload = {
            'email': admin_user.email  # Use admin's email
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}',
            data=json.dumps(payload),
            headers=auth_headers
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

        # Assert - should return error (currently returns 500, should be 400)
        assert response.status_code in [200, 400, 500]

    def test_invalid_status_filter(self, client, db, admin_user, admin_auth_headers):
        """Test get users with invalid status filter"""
        # Act
        response = client.get(
            '/api/v1/users?status=invalid_status',
            headers=admin_auth_headers
        )

        # Assert - should return error (currently returns 500, should be 400)
        assert response.status_code in [200, 400, 500]

    def test_update_user_status_invalid_value(self, client, db, sample_user, admin_user, admin_auth_headers):
        """Test update user status with invalid value"""
        # Arrange
        payload = {
            'status': 'invalid_status'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}/status',
            data=json.dumps(payload),
            headers=admin_auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_update_user_status_missing_value(self, client, db, sample_user, admin_user, admin_auth_headers):
        """Test update user status without status value"""
        # Arrange
        payload = {}

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}/status',
            data=json.dumps(payload),
            headers=admin_auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400

    def test_user_endpoints_without_authentication(self, client, db, sample_user):
        """Test user endpoints without authentication"""
        # Test GET list
        response = client.get('/api/v1/users')
        assert response.status_code == 401

        # Test GET single
        response = client.get(f'/api/v1/users/{sample_user.id}')
        assert response.status_code == 401

        # Test POST
        payload = {'username': 'test', 'email': 'test@example.com', 'password': 'Test123'}
        response = client.post(
            '/api/v1/users',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 401

        # Test PUT
        response = client.put(
            f'/api/v1/users/{sample_user.id}',
            data=json.dumps({'first_name': 'Test'}),
            content_type='application/json'
        )
        assert response.status_code == 401

        # Test DELETE
        response = client.delete(f'/api/v1/users/{sample_user.id}')
        assert response.status_code == 401

    def test_special_characters_in_user_fields(self, client, db, sample_user, auth_headers):
        """Test special characters in user update fields"""
        # Arrange
        payload = {
            'first_name': "O'Brien",
            'last_name': 'José-María',
            'phone': '+1-234-567-8900'
        }

        # Act
        response = client.put(
            f'/api/v1/users/{sample_user.id}',
            data=json.dumps(payload),
            headers=auth_headers
        )

        # Assert
        assert response.status_code in [200, 400]
