"""
Complete User Workflow Integration Tests
End-to-end tests for complete user workflows
"""
import pytest
import json


class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to logout"""

    def test_complete_registration_and_login_flow(self, client, db):
        """
        Test complete workflow: Register -> Login -> Get Profile -> Logout
        """
        # Step 1: Register a new user
        register_payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        register_response = client.post(
            '/api/v1/auth/register',
            data=json.dumps(register_payload),
            content_type='application/json'
        )

        assert register_response.status_code == 201
        register_data = json.loads(register_response.data)
        assert register_data['success'] is True
        assert 'access_token' in register_data['data']

        initial_access_token = register_data['data']['access_token']

        # Step 2: Login with the new user
        login_payload = {
            'username_or_email': 'newuser',
            'password': 'NewPass123'
        }

        login_response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(login_payload),
            content_type='application/json'
        )

        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        assert login_data['success'] is True
        access_token = login_data['data']['access_token']

        # Step 3: Get current user profile
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        profile_response = client.get(
            '/api/v1/auth/me',
            headers=headers
        )

        assert profile_response.status_code == 200
        profile_data = json.loads(profile_response.data)
        assert profile_data['data']['username'] == 'newuser'
        assert profile_data['data']['email'] == 'newuser@example.com'

        # Step 4: Logout
        logout_response = client.post(
            '/api/v1/auth/logout',
            headers=headers
        )

        assert logout_response.status_code == 200

        # Step 5: Verify token is invalidated
        profile_response_after_logout = client.get(
            '/api/v1/auth/me',
            headers=headers
        )

        # Token should be revoked
        assert profile_response_after_logout.status_code == 401

    def test_user_profile_update_flow(self, client, db, sample_user, auth_headers):
        """
        Test workflow: Login -> Update Profile -> Verify Updates
        """
        # Step 1: Get current profile
        profile_response = client.get(
            '/api/v1/auth/me',
            headers=auth_headers
        )

        assert profile_response.status_code == 200
        original_profile = json.loads(profile_response.data)

        # Step 2: Update profile
        update_payload = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+1234567890'
        }

        update_response = client.put(
            f'/api/v1/users/{sample_user.id}',
            data=json.dumps(update_payload),
            headers=auth_headers
        )

        assert update_response.status_code == 200
        update_data = json.loads(update_response.data)
        assert update_data['data']['first_name'] == 'Updated'
        assert update_data['data']['last_name'] == 'Name'

        # Step 3: Verify updates by getting profile again
        verify_response = client.get(
            '/api/v1/auth/me',
            headers=auth_headers
        )

        assert verify_response.status_code == 200
        verify_data = json.loads(verify_response.data)
        assert verify_data['data']['first_name'] == 'Updated'
        assert verify_data['data']['last_name'] == 'Name'

    def test_password_change_and_reauth_flow(self, client, db, sample_user, auth_headers):
        """
        Test workflow: Change Password -> Logout -> Login with New Password
        """
        # Step 1: Change password
        change_password_payload = {
            'old_password': 'TestPass123',
            'new_password': 'NewPass456'
        }

        change_response = client.put(
            f'/api/v1/users/{sample_user.id}/password',
            data=json.dumps(change_password_payload),
            headers=auth_headers
        )

        assert change_response.status_code == 200

        # Step 2: Logout
        logout_response = client.post(
            '/api/v1/auth/logout',
            headers=auth_headers
        )

        assert logout_response.status_code == 200

        # Step 3: Try to login with old password (should fail)
        old_password_login = {
            'username_or_email': 'testuser',
            'password': 'TestPass123'
        }

        old_login_response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(old_password_login),
            content_type='application/json'
        )

        assert old_login_response.status_code == 401

        # Step 4: Login with new password (should succeed)
        new_password_login = {
            'username_or_email': 'testuser',
            'password': 'NewPass456'
        }

        new_login_response = client.post(
            '/api/v1/auth/login',
            data=json.dumps(new_password_login),
            content_type='application/json'
        )

        assert new_login_response.status_code == 200

    def test_token_refresh_flow(self, client, db, sample_token):
        """
        Test workflow: Login -> Use Token -> Refresh Token -> Use New Token
        """
        # Step 1: Use original token
        headers = {
            'Authorization': f'Bearer {sample_token.access_token}',
            'Content-Type': 'application/json'
        }

        profile_response = client.get(
            '/api/v1/auth/me',
            headers=headers
        )

        assert profile_response.status_code == 200

        # Step 2: Refresh token
        refresh_payload = {
            'refresh_token': sample_token.refresh_token
        }

        refresh_response = client.post(
            '/api/v1/auth/refresh',
            data=json.dumps(refresh_payload),
            content_type='application/json'
        )

        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        new_access_token = refresh_data['data']['access_token']

        # Step 3: Use new token
        new_headers = {
            'Authorization': f'Bearer {new_access_token}',
            'Content-Type': 'application/json'
        }

        new_profile_response = client.get(
            '/api/v1/auth/me',
            headers=new_headers
        )

        assert new_profile_response.status_code == 200

    def test_admin_user_management_flow(self, client, db, admin_user, admin_auth_headers):
        """
        Test workflow: Admin creates user -> Verifies user -> Updates user -> Deletes user
        """
        # Step 1: Admin creates a new user
        create_payload = {
            'username': 'manageduser',
            'email': 'managed@example.com',
            'password': 'ManagedPass123',
            'first_name': 'Managed',
            'last_name': 'User'
        }

        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=admin_auth_headers
        )

        assert create_response.status_code == 201
        create_data = json.loads(create_response.data)
        user_id = create_data['data']['id']

        # Step 2: Admin verifies the user
        verify_response = client.post(
            f'/api/v1/users/{user_id}/verify',
            headers=admin_auth_headers
        )

        assert verify_response.status_code == 200
        verify_data = json.loads(verify_response.data)
        assert verify_data['data']['is_verified'] is True

        # Step 3: Admin gets user list to verify creation
        list_response = client.get(
            '/api/v1/users?page=1&per_page=20',
            headers=admin_auth_headers
        )

        assert list_response.status_code == 200
        list_data = json.loads(list_response.data)
        assert any(user['username'] == 'manageduser' for user in list_data['data']['items'])

        # Step 4: Admin deletes the user
        delete_response = client.delete(
            f'/api/v1/users/{user_id}',
            headers=admin_auth_headers
        )

        assert delete_response.status_code == 200

    def test_unauthorized_access_attempts(self, client, db, sample_user, auth_headers):
        """
        Test workflow: Regular user attempts admin operations (should fail)
        """
        # Step 1: Regular user tries to get all users (admin only)
        list_response = client.get(
            '/api/v1/users?page=1&per_page=20',
            headers=auth_headers
        )

        assert list_response.status_code == 403

        # Step 2: Regular user tries to create another user (admin only)
        create_payload = {
            'username': 'unauthorizeduser',
            'email': 'unauth@example.com',
            'password': 'UnauthPass123'
        }

        create_response = client.post(
            '/api/v1/users',
            data=json.dumps(create_payload),
            headers=auth_headers
        )

        assert create_response.status_code == 403

    def test_validation_error_flow(self, client, db):
        """
        Test workflow: Attempt registration with invalid data
        """
        # Invalid email
        invalid_email_payload = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'TestPass123'
        }

        response1 = client.post(
            '/api/v1/auth/register',
            data=json.dumps(invalid_email_payload),
            content_type='application/json'
        )

        assert response1.status_code == 400

        # Weak password
        weak_password_payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak'
        }

        response2 = client.post(
            '/api/v1/auth/register',
            data=json.dumps(weak_password_payload),
            content_type='application/json'
        )

        assert response2.status_code == 400

    def test_duplicate_registration_flow(self, client, db, sample_user):
        """
        Test workflow: Attempt to register with existing username/email
        """
        # Try to register with existing username
        duplicate_username_payload = {
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'TestPass123'
        }

        response1 = client.post(
            '/api/v1/auth/register',
            data=json.dumps(duplicate_username_payload),
            content_type='application/json'
        )

        assert response1.status_code == 409

        # Try to register with existing email
        duplicate_email_payload = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Already exists
            'password': 'TestPass123'
        }

        response2 = client.post(
            '/api/v1/auth/register',
            data=json.dumps(duplicate_email_payload),
            content_type='application/json'
        )

        assert response2.status_code == 409

    def test_multiple_sessions_flow(self, client, db):
        """
        Test workflow: Same user logs in multiple times (multiple sessions)
        """
        # Register user
        register_payload = {
            'username': 'multiuser',
            'email': 'multi@example.com',
            'password': 'MultiPass123'
        }

        client.post(
            '/api/v1/auth/register',
            data=json.dumps(register_payload),
            content_type='application/json'
        )

        # Login multiple times
        login_payload = {
            'username_or_email': 'multiuser',
            'password': 'MultiPass123'
        }

        response1 = client.post(
            '/api/v1/auth/login',
            data=json.dumps(login_payload),
            content_type='application/json'
        )

        response2 = client.post(
            '/api/v1/auth/login',
            data=json.dumps(login_payload),
            content_type='application/json'
        )

        response3 = client.post(
            '/api/v1/auth/login',
            data=json.dumps(login_payload),
            content_type='application/json'
        )

        # All logins should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # Each should have a different token
        token1 = json.loads(response1.data)['data']['access_token']
        token2 = json.loads(response2.data)['data']['access_token']
        token3 = json.loads(response3.data)['data']['access_token']

        assert token1 != token2
        assert token2 != token3
        assert token1 != token3

    def test_login_with_email_and_username(self, client, db, sample_user):
        """
        Test workflow: Login with both email and username should work
        """
        # Login with username
        username_login = {
            'username_or_email': 'testuser',
            'password': 'TestPass123'
        }

        response1 = client.post(
            '/api/v1/auth/login',
            data=json.dumps(username_login),
            content_type='application/json'
        )

        assert response1.status_code == 200

        # Login with email
        email_login = {
            'username_or_email': 'test@example.com',
            'password': 'TestPass123'
        }

        response2 = client.post(
            '/api/v1/auth/login',
            data=json.dumps(email_login),
            content_type='application/json'
        )

        assert response2.status_code == 200
