"""
Auth Controller Unit Tests
Tests for app/controllers/auth_controller.py
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from app.utils.exceptions import APIException

AUTH_URL = '/api/v1/auth'
JSON_CT = {'Content-Type': 'application/json'}
AUTH_HDR = {'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'}

REGISTER_PAYLOAD = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'SecurePass123',
    'first_name': 'Test',
    'last_name': 'User',
}
LOGIN_PAYLOAD = {'username_or_email': 'testuser', 'password': 'SecurePass123'}


@pytest.fixture(scope='module')
def app():
    with patch('app.repositories.impl.user_repository_impl.UserRepositoryImpl'), \
         patch('app.repositories.impl.oauth_token_repository_impl.OAuthTokenRepositoryImpl'), \
         patch('app.extensions.db'), \
         patch('app.services.impl.auth_service_impl.AuthServiceImpl') as MockAuth:
        from app.models.user import User, UserRole
        admin = MagicMock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN
        MockAuth.return_value.validateToken.return_value = admin
        admin.toDict.return_value = {'id': 1, 'email': 'admin@test.com', 'role': 'admin'}
        from app import create_app
        a = create_app('testing')
        a.config['TESTING'] = True
        yield a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_svc():
    return MagicMock()


# ── POST /api/auth/register ───────────────────────────────────────────────────

class TestRegister:
    def test_register_returns_201(self, client, auth_svc, monkeypatch):
        auth_svc.register.return_value = {'id': 1, 'email': 'test@example.com'}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/register', data=json.dumps(REGISTER_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 201

    def test_register_calls_auth_service(self, client, auth_svc, monkeypatch):
        auth_svc.register.return_value = {'id': 1}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        client.post(f'{AUTH_URL}/register', data=json.dumps(REGISTER_PAYLOAD), headers=JSON_CT)
        auth_svc.register.assert_called_once()

    def test_register_api_exception(self, client, auth_svc, monkeypatch):
        auth_svc.register.side_effect = APIException('Email taken', 409, 'DUPLICATE_EMAIL')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/register', data=json.dumps(REGISTER_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 409

    def test_register_generic_exception_returns_500(self, client, auth_svc, monkeypatch):
        auth_svc.register.side_effect = RuntimeError('DB error')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/register', data=json.dumps(REGISTER_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 500


# ── POST /api/auth/login ──────────────────────────────────────────────────────

class TestLogin:
    def test_login_returns_200(self, client, auth_svc, monkeypatch):
        auth_svc.login.return_value = {'access_token': 'tok', 'refresh_token': 'ref'}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/login', data=json.dumps(LOGIN_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 200

    def test_login_calls_auth_service(self, client, auth_svc, monkeypatch):
        auth_svc.login.return_value = {'access_token': 'tok'}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        client.post(f'{AUTH_URL}/login', data=json.dumps(LOGIN_PAYLOAD), headers=JSON_CT)
        auth_svc.login.assert_called_once()

    def test_login_api_exception(self, client, auth_svc, monkeypatch):
        auth_svc.login.side_effect = APIException('Invalid credentials', 401, 'INVALID_CREDENTIALS')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/login', data=json.dumps(LOGIN_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 401

    def test_login_generic_exception_returns_500(self, client, auth_svc, monkeypatch):
        auth_svc.login.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/login', data=json.dumps(LOGIN_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 500


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

class TestLogout:
    def test_logout_returns_200(self, client, auth_svc, monkeypatch):
        auth_svc.logout.return_value = True
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/logout', headers=AUTH_HDR)
        assert res.status_code == 200

    def test_logout_api_exception(self, client, auth_svc, monkeypatch):
        auth_svc.logout.side_effect = APIException('Invalid token', 401, 'INVALID_TOKEN')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/logout', headers=AUTH_HDR)
        assert res.status_code == 401

    def test_logout_generic_exception_returns_500(self, client, auth_svc, monkeypatch):
        auth_svc.logout.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/logout', headers=AUTH_HDR)
        assert res.status_code == 500


# ── POST /api/auth/refresh ────────────────────────────────────────────────────

class TestRefreshToken:
    PAYLOAD = {'refresh_token': 'valid-refresh-token'}

    def test_refresh_returns_200(self, client, auth_svc, monkeypatch):
        auth_svc.refreshToken.return_value = {'access_token': 'new-tok'}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/refresh', data=json.dumps(self.PAYLOAD), headers=JSON_CT)
        assert res.status_code == 200

    def test_refresh_api_exception(self, client, auth_svc, monkeypatch):
        auth_svc.refreshToken.side_effect = APIException('Token expired', 401, 'TOKEN_EXPIRED')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/refresh', data=json.dumps(self.PAYLOAD), headers=JSON_CT)
        assert res.status_code == 401

    def test_refresh_generic_exception_returns_500(self, client, auth_svc, monkeypatch):
        auth_svc.refreshToken.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/refresh', data=json.dumps(self.PAYLOAD), headers=JSON_CT)
        assert res.status_code == 500


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

class TestGetCurrentUser:
    def test_me_returns_200(self, client, auth_svc, monkeypatch):
        auth_svc.getUserProfile.return_value = {'id': 1, 'email': 'admin@test.com'}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.get(f'{AUTH_URL}/me', headers=AUTH_HDR)
        assert res.status_code == 200

    def test_me_no_auth_returns_401(self, client):
        # /me uses g.current_user (set by token_required), not get_auth_service/getUserProfile
        # Test that missing Authorization header → 401 from token_required
        res = client.get(f'{AUTH_URL}/me')
        assert res.status_code == 401

    def test_me_invalid_token_format_returns_401(self, client):
        # Invalid bearer format → 401 from token_required format check
        res = client.get(f'{AUTH_URL}/me', headers={'Authorization': 'NotBearer token'})
        assert res.status_code == 401


# ── GET /api/auth/tokens ──────────────────────────────────────────────────────

class TestGetUserTokens:
    def test_tokens_returns_200(self, client, auth_svc, monkeypatch):
        auth_svc.getUserTokens.return_value = [{'id': 1, 'token': 'tok'}]
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.get(f'{AUTH_URL}/tokens', headers=AUTH_HDR)
        assert res.status_code == 200

    def test_tokens_api_exception(self, client, auth_svc, monkeypatch):
        auth_svc.getUserTokens.side_effect = APIException('Error', 500, 'ERR')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.get(f'{AUTH_URL}/tokens', headers=AUTH_HDR)
        assert res.status_code == 500

    def test_tokens_generic_exception_returns_500(self, client, auth_svc, monkeypatch):
        auth_svc.getUserTokens.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.get(f'{AUTH_URL}/tokens', headers=AUTH_HDR)
        assert res.status_code == 500

    def test_tokens_with_oauth_token_objects_serializes(self, client, auth_svc, monkeypatch):
        # Line 234: else branch → tokens are OAuthToken objects, not dicts
        # Create mock token objects with toDict() method
        mock_token = MagicMock()
        mock_token.toDict.return_value = {'id': 1, 'token': 'tok', 'created_at': '2026-01-01'}
        auth_svc.getUserTokens.return_value = [mock_token]
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.get(f'{AUTH_URL}/tokens', headers=AUTH_HDR)
        assert res.status_code == 200


# ── POST /api/auth/tokens/revoke-all ─────────────────────────────────────────

class TestRevokeAllTokens:
    def test_revoke_all_returns_200(self, client, auth_svc, monkeypatch):
        auth_svc.revokeAllTokens.return_value = {'revoked': 3}
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/tokens/revoke-all', headers=AUTH_HDR)
        assert res.status_code == 200

    def test_revoke_all_api_exception(self, client, auth_svc, monkeypatch):
        auth_svc.revokeAllTokens.side_effect = APIException('Error', 500, 'ERR')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/tokens/revoke-all', headers=AUTH_HDR)
        assert res.status_code == 500

    def test_revoke_all_generic_exception_returns_500(self, client, auth_svc, monkeypatch):
        auth_svc.revokeAllTokens.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.auth_controller.get_auth_service', lambda: auth_svc)
        res = client.post(f'{AUTH_URL}/tokens/revoke-all', headers=AUTH_HDR)
        assert res.status_code == 500
