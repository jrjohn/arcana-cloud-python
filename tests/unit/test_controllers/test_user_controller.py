"""
User Controller Unit Tests
Tests for app/controllers/user_controller.py
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from app.models.user import UserRole
from app.utils.exceptions import APIException

USERS_URL = '/api/v1/users'
AUTH_HEADER = {'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'}

# ── helpers ──────────────────────────────────────────────────────────────────

def make_paginated(items=None, total=3):
    return {
        'items': items or [{'id': 1, 'email': 'a@b.com'}],
        'pagination': {'page': 1, 'per_page': 20, 'total': total},
    }


def api_patch(monkeypatch, service_mock):
    """Patch get_service_communication globally inside the request."""
    monkeypatch.setattr(
        'app.controllers.user_controller.get_service_communication',
        lambda: service_mock,
    )


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def app():
    with patch('app.decorators.auth_decorators.UserRepositoryImpl'), \
         patch('app.decorators.auth_decorators.OAuthTokenRepositoryImpl'), \
         patch('app.decorators.auth_decorators.db'), \
         patch('app.decorators.auth_decorators.AuthServiceImpl') as MockAuth:
        from app.models.user import User
        admin = MagicMock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN
        MockAuth.return_value.validateToken.return_value = admin
        from app import create_app
        a = create_app('testing')
        a.config['TESTING'] = True
        yield a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def svc():
    return MagicMock()


# ── GET /api/v1/users ─────────────────────────────────────────────────────────

class TestGetUsers:
    def test_returns_200_with_users(self, client, svc, monkeypatch):
        svc.get_users.return_value = make_paginated()
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(USERS_URL, headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_calls_service_with_pagination(self, client, svc, monkeypatch):
        svc.get_users.return_value = make_paginated()
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        client.get(f'{USERS_URL}?page=2&per_page=5', headers=AUTH_HEADER)
        svc.get_users.assert_called_once()

    def test_filter_by_valid_role(self, client, svc, monkeypatch):
        svc.get_users.return_value = make_paginated()
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}?role=user', headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_filter_by_invalid_role_returns_400(self, client, svc, monkeypatch):
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}?role=INVALID_ROLE_XYZ', headers=AUTH_HEADER)
        assert res.status_code == 400

    def test_filter_by_valid_status(self, client, svc, monkeypatch):
        svc.get_users.return_value = make_paginated()
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}?status=active', headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_filter_by_invalid_status_returns_400(self, client, svc, monkeypatch):
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}?status=INVALID_STATUS_XYZ', headers=AUTH_HEADER)
        assert res.status_code == 400

    def test_api_exception_returns_correct_status(self, client, svc, monkeypatch):
        svc.get_users.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(USERS_URL, headers=AUTH_HEADER)
        assert res.status_code == 404

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.get_users.side_effect = RuntimeError('DB error')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(USERS_URL, headers=AUTH_HEADER)
        assert res.status_code == 500

    def test_no_auth_header_returns_401(self, client, svc, monkeypatch):
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(USERS_URL)
        assert res.status_code == 401


# ── GET /api/v1/users/<id> ────────────────────────────────────────────────────

class TestGetUser:
    def test_admin_can_get_any_user(self, client, svc, monkeypatch):
        svc.get_user_by_id.return_value = {'id': 5, 'email': 'other@test.com'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}/5', headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_own_user_can_get_own_info(self, client, svc, monkeypatch):
        svc.get_user_by_id.return_value = {'id': 1, 'email': 'admin@test.com'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}/1', headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.get_user_by_id.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}/999', headers=AUTH_HEADER)
        assert res.status_code == 404

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.get_user_by_id.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{USERS_URL}/1', headers=AUTH_HEADER)
        assert res.status_code == 500


# ── POST /api/v1/users ────────────────────────────────────────────────────────

class TestCreateUser:
    PAYLOAD = {
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'Pass123!',
        'first_name': 'New',
        'last_name': 'User',
    }

    def test_create_returns_201(self, client, svc, monkeypatch):
        svc.create_user.return_value = {'id': 99, 'email': 'new@test.com'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.post(USERS_URL, data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 201

    def test_create_calls_service(self, client, svc, monkeypatch):
        svc.create_user.return_value = {'id': 99, 'email': 'new@test.com'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        client.post(USERS_URL, data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        svc.create_user.assert_called_once()

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.create_user.side_effect = APIException('Conflict', 409, 'DUPLICATE')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.post(USERS_URL, data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 409

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.create_user.side_effect = RuntimeError('oops')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.post(USERS_URL, data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 500


# ── PUT /api/v1/users/<id> ────────────────────────────────────────────────────

class TestUpdateUser:
    PAYLOAD = {'first_name': 'Updated', 'last_name': 'Name'}

    def test_admin_can_update_any_user(self, client, svc, monkeypatch):
        svc.update_user.return_value = {'id': 5, 'first_name': 'Updated'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/5', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_update_calls_service(self, client, svc, monkeypatch):
        svc.update_user.return_value = {'id': 1, 'first_name': 'Updated'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        client.put(f'{USERS_URL}/1', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        svc.update_user.assert_called_once()

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.update_user.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/99', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 404

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.update_user.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/1', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 500


# ── DELETE /api/v1/users/<id> ─────────────────────────────────────────────────

class TestDeleteUser:
    def test_delete_returns_200(self, client, svc, monkeypatch):
        svc.delete_user.return_value = None
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.delete(f'{USERS_URL}/5', headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.delete_user.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.delete(f'{USERS_URL}/99', headers=AUTH_HEADER)
        assert res.status_code == 404

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.delete_user.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.delete(f'{USERS_URL}/1', headers=AUTH_HEADER)
        assert res.status_code == 500


# ── PUT /api/v1/users/<id>/password ──────────────────────────────────────────

class TestChangePassword:
    PAYLOAD = {'old_password': 'OldPass123', 'new_password': 'NewPass456'}

    def test_own_password_change_returns_200(self, client, svc, monkeypatch):
        svc.change_password.return_value = None
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/1/password', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_other_user_password_returns_403(self, client, svc, monkeypatch):
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/99/password', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 403

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.change_password.side_effect = APIException('Wrong password', 400, 'INVALID_PASSWORD')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/1/password', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 400

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.change_password.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/1/password', data=json.dumps(self.PAYLOAD), headers=AUTH_HEADER)
        assert res.status_code == 500


# ── POST /api/v1/users/<id>/verify ───────────────────────────────────────────

class TestVerifyUser:
    def test_verify_returns_200(self, client, svc, monkeypatch):
        svc.verify_user.return_value = {'id': 5, 'verified': True}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.post(f'{USERS_URL}/5/verify', headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.verify_user.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.post(f'{USERS_URL}/99/verify', headers=AUTH_HEADER)
        assert res.status_code == 404

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.verify_user.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.post(f'{USERS_URL}/1/verify', headers=AUTH_HEADER)
        assert res.status_code == 500


# ── PUT /api/v1/users/<id>/status ────────────────────────────────────────────

class TestUpdateUserStatus:
    def test_update_status_returns_200(self, client, svc, monkeypatch):
        svc.update_user_status.return_value = {'id': 5, 'status': 'suspended'}
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        payload = json.dumps({'status': 'suspended'})
        res = client.put(f'{USERS_URL}/5/status', data=payload, headers=AUTH_HEADER)
        assert res.status_code == 200

    def test_missing_status_returns_400(self, client, svc, monkeypatch):
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/5/status', data=json.dumps({}), headers=AUTH_HEADER)
        assert res.status_code == 400

    def test_invalid_status_returns_400(self, client, svc, monkeypatch):
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        payload = json.dumps({'status': 'NOT_A_STATUS'})
        res = client.put(f'{USERS_URL}/5/status', data=payload, headers=AUTH_HEADER)
        assert res.status_code == 400

    def test_api_exception_propagated(self, client, svc, monkeypatch):
        svc.update_user_status.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/99/status', data=json.dumps({'status': 'active'}), headers=AUTH_HEADER)
        assert res.status_code == 404

    def test_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.update_user_status.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{USERS_URL}/1/status', data=json.dumps({'status': 'active'}), headers=AUTH_HEADER)
        assert res.status_code == 500
