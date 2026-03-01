"""
Public User Controller Unit Tests
Tests for app/controllers/public_user_controller.py
No auth required - these are public endpoints.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from app.utils.exceptions import APIException

PUB_URL = '/api/public/users'
JSON_CT = {'Content-Type': 'application/json'}

CREATE_PAYLOAD = {
    'email': 'pub@example.com',
    'first_name': 'Public',
    'last_name': 'User',
}
UPDATE_PAYLOAD = {'first_name': 'Updated', 'last_name': 'Name', 'email': 'pub2@example.com'}


@pytest.fixture(scope='module')
def app():
    from app import create_app
    a = create_app('testing')
    a.config['TESTING'] = True
    return a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def svc():
    return MagicMock()


# ── GET /api/public/users ─────────────────────────────────────────────────────

class TestListUsers:
    def test_list_returns_200(self, client, svc, monkeypatch):
        svc.get_users.return_value = {
            'items': [{'id': 1, 'email': 'a@b.com'}],
            'pagination': {'page': 1, 'per_page': 20, 'total': 1},
        }
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(PUB_URL)
        assert res.status_code == 200

    def test_list_with_pagination(self, client, svc, monkeypatch):
        svc.get_users.return_value = {
            'items': [],
            'pagination': {'page': 2, 'per_page': 5, 'total': 0},
        }
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{PUB_URL}?page=2&per_page=5')
        assert res.status_code == 200

    def test_list_api_exception(self, client, svc, monkeypatch):
        svc.get_users.side_effect = APIException('Service unavailable', 503, 'SERVICE_ERROR')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(PUB_URL)
        assert res.status_code == 500  # list_users catches all Exception as 500

    def test_list_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.get_users.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(PUB_URL)
        assert res.status_code == 500


# ── GET /api/public/users/<id> ────────────────────────────────────────────────

class TestGetUser:
    def test_get_returns_200(self, client, svc, monkeypatch):
        svc.get_user_by_id.return_value = {'id': 1, 'email': 'a@b.com'}
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{PUB_URL}/1')
        assert res.status_code == 200

    def test_get_not_found(self, client, svc, monkeypatch):
        svc.get_user_by_id.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{PUB_URL}/999')
        assert res.status_code == 500  # get_user catches Exception generically

    def test_get_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.get_user_by_id.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.get(f'{PUB_URL}/1')
        assert res.status_code == 500


# ── POST /api/public/users ────────────────────────────────────────────────────

class TestCreateUser:
    def test_create_returns_201(self, client, svc, monkeypatch):
        svc.create_user.return_value = {'id': 99, 'email': 'pub@example.com'}
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.post(PUB_URL, data=json.dumps(CREATE_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 201

    def test_create_calls_service(self, client, svc, monkeypatch):
        svc.create_user.return_value = {'id': 99}
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        client.post(PUB_URL, data=json.dumps(CREATE_PAYLOAD), headers=JSON_CT)
        svc.create_user.assert_called_once()

    def test_create_api_exception(self, client, svc, monkeypatch):
        svc.create_user.side_effect = APIException('Email exists', 409, 'CONFLICT')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.post(PUB_URL, data=json.dumps(CREATE_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 409

    def test_create_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.create_user.side_effect = RuntimeError('DB error')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.post(PUB_URL, data=json.dumps(CREATE_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 500


# ── PUT /api/public/users/<id> ────────────────────────────────────────────────

class TestUpdateUser:
    def test_update_returns_200(self, client, svc, monkeypatch):
        svc.update_user.return_value = {'id': 1, 'first_name': 'Updated'}
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{PUB_URL}/1', data=json.dumps(UPDATE_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 200

    def test_update_api_exception(self, client, svc, monkeypatch):
        svc.update_user.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{PUB_URL}/99', data=json.dumps(UPDATE_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 404

    def test_update_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.update_user.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.put(f'{PUB_URL}/1', data=json.dumps(UPDATE_PAYLOAD), headers=JSON_CT)
        assert res.status_code == 500


# ── DELETE /api/public/users/<id> ─────────────────────────────────────────────

class TestDeleteUser:
    def test_delete_returns_200(self, client, svc, monkeypatch):
        svc.delete_user.return_value = None
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.delete(f'{PUB_URL}/1')
        assert res.status_code == 204  # delete returns 204 NO CONTENT

    def test_delete_api_exception(self, client, svc, monkeypatch):
        svc.delete_user.side_effect = APIException('Not found', 404, 'NOT_FOUND')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.delete(f'{PUB_URL}/99')
        assert res.status_code == 404

    def test_delete_generic_exception_returns_500(self, client, svc, monkeypatch):
        svc.delete_user.side_effect = RuntimeError('fail')
        monkeypatch.setattr('app.controllers.public_user_controller.get_service_communication', lambda: svc)
        res = client.delete(f'{PUB_URL}/1')
        assert res.status_code == 500
