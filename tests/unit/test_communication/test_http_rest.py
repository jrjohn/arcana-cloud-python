"""
HTTP/REST Communication Unit Tests
Tests for app/communication/impl/http_rest.py
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import requests

from app.communication.impl.http_rest_impl import HTTPServiceCommunicationImpl, HTTPRepositoryCommunicationImpl
from app.communication.interfaces import DeploymentMode, CommunicationMode, CommunicationProtocol
from app.utils.exceptions import (
    APIException, NotFoundError, ConflictError,
    ValidationError, AuthenticationError, AuthorizationError
)


def _make_http_error(status_code, body=None):
    """Helper: build a requests.HTTPError with a mock response."""
    mock_response = Mock()
    mock_response.status_code = status_code
    if body is not None:
        mock_response.json.return_value = body
    else:
        mock_response.json.side_effect = ValueError("no json")
    err = requests.exceptions.HTTPError(response=mock_response)
    err.response = mock_response
    return err


# ── HTTPServiceCommunicationImpl ──────────────────────────────────────────────────

class TestHTTPServiceCommunicationInit:

    def test_layered_mode_sets_layered_http_mode(self):
        comm = HTTPServiceCommunicationImpl(['http://svc:5001'], DeploymentMode.LAYERED)
        assert comm.get_mode() == CommunicationMode.LAYERED_HTTP

    def test_microservices_mode_sets_microservices_http_mode(self):
        comm = HTTPServiceCommunicationImpl(['http://svc:5001'], DeploymentMode.MICROSERVICES)
        assert comm.get_mode() == CommunicationMode.MICROSERVICES_HTTP

    def test_protocol_is_http(self):
        comm = HTTPServiceCommunicationImpl(['http://svc:5001'], DeploymentMode.LAYERED)
        assert comm.get_protocol() == CommunicationProtocol.HTTP

    def test_round_robin_url_rotation(self):
        comm = HTTPServiceCommunicationImpl(['http://a:5001', 'http://b:5001'], DeploymentMode.LAYERED)
        url1 = comm._get_next_url()
        url2 = comm._get_next_url()
        url3 = comm._get_next_url()
        assert url1 == 'http://a:5001'
        assert url2 == 'http://b:5001'
        assert url3 == 'http://a:5001'  # wraps back


class TestHTTPServiceCommunicationMakeRequest:

    @pytest.fixture
    def comm(self):
        with patch('requests.Session'):
            svc = HTTPServiceCommunicationImpl(['http://svc:5001'], DeploymentMode.LAYERED)
            svc.session = Mock()
            return svc

    def test_successful_request_returns_json(self, comm):
        mock_resp = Mock()
        mock_resp.json.return_value = {'data': 'ok'}
        comm.session.request.return_value = mock_resp
        result = comm._make_request('GET', '/internal/users')
        assert result == {'data': 'ok'}

    def test_404_raises_not_found(self, comm):
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(404, {'error': 'Not found', 'error_code': 'NOT_FOUND'})
        with pytest.raises(NotFoundError):
            comm._make_request('GET', '/internal/users/999')

    def test_409_raises_conflict(self, comm):
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(409, {'error': 'Conflict'})
        with pytest.raises(ConflictError):
            comm._make_request('POST', '/internal/users')

    def test_400_raises_validation_error(self, comm):
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(400, {'error': 'Bad request'})
        with pytest.raises(ValidationError):
            comm._make_request('POST', '/internal/users')

    def test_401_raises_authentication_error(self, comm):
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(401)
        with pytest.raises(AuthenticationError):
            comm._make_request('GET', '/internal/me')

    def test_403_raises_authorization_error(self, comm):
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(403)
        with pytest.raises(AuthorizationError):
            comm._make_request('DELETE', '/internal/admin')

    def test_500_raises_api_exception(self, comm):
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(500, {'error': 'Server error', 'error_code': 'INTERNAL'})
        with pytest.raises(APIException):
            comm._make_request('GET', '/internal/users')

    def test_500_no_json_body_raises_api_exception(self, comm):
        """HTTP error with non-JSON body → still raises APIException"""
        comm.session.request.return_value.raise_for_status.side_effect = \
            _make_http_error(500)
        with pytest.raises(APIException):
            comm._make_request('GET', '/internal/users')

    def test_connection_error_raises_api_exception(self, comm):
        comm.session.request.side_effect = requests.exceptions.ConnectionError("refused")
        with pytest.raises(APIException):
            comm._make_request('GET', '/internal/users')

    def test_timeout_raises_api_exception(self, comm):
        comm.session.request.side_effect = requests.exceptions.Timeout("timed out")
        with pytest.raises(APIException):
            comm._make_request('GET', '/internal/users')


class TestHTTPServiceCommunicationMethods:

    @pytest.fixture
    def comm(self):
        with patch('requests.Session'):
            svc = HTTPServiceCommunicationImpl(['http://svc:5001'], DeploymentMode.LAYERED)
            svc.session = Mock()
            return svc

    def _ok(self, data):
        resp = Mock()
        resp.json.return_value = data
        return resp

    def test_call_posts_to_internal_endpoint(self, comm):
        comm.session.request.return_value = self._ok({'result': 'ok'})
        result = comm.call('getUsers', page=1)
        comm.session.request.assert_called_once()
        call_kwargs = comm.session.request.call_args
        assert '/internal/getUsers' in call_kwargs[1].get('url', call_kwargs[0][1] if len(call_kwargs[0]) > 1 else '')

    def test_health_check_returns_true_on_200(self, comm):
        mock_resp = Mock()
        mock_resp.status_code = 200
        comm.session.get.return_value = mock_resp
        assert comm.health_check() is True

    def test_health_check_returns_false_on_error(self, comm):
        comm.session.get.side_effect = Exception("refused")
        assert comm.health_check() is False

    def test_get_users_returns_data(self, comm):
        comm.session.request.return_value = self._ok({'data': {'users': [], 'total': 0}})
        result = comm.get_users(page=1, per_page=10)
        assert 'users' in result

    def test_get_users_with_enum_filter(self, comm):
        from app.models.user import UserRole
        comm.session.request.return_value = self._ok({'data': {'users': []}})
        comm.get_users(role=UserRole.ADMIN)
        comm.session.request.assert_called_once()

    def test_get_user_by_id(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 1, 'username': 'john'}})
        result = comm.get_user_by_id(1)
        assert result['id'] == 1

    def test_create_user(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 2}})
        result = comm.create_user({'username': 'new', 'email': 'n@t.com', 'password': 'p'})
        assert result['id'] == 2

    def test_update_user(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 1, 'first_name': 'Updated'}})
        result = comm.update_user(1, {'first_name': 'Updated'})
        assert result['first_name'] == 'Updated'

    def test_delete_user(self, comm):
        comm.session.request.return_value = self._ok({'success': True})
        result = comm.delete_user(1)
        assert result is not None

    def test_change_password(self, comm):
        comm.session.request.return_value = self._ok({'success': True})
        result = comm.change_password(1, 'old', 'new')
        assert result is not None

    def test_verify_user(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 1, 'is_verified': True}})
        result = comm.verify_user(1)
        assert result['is_verified'] is True

    def test_update_user_status(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 1, 'status': 'active'}})
        result = comm.update_user_status(1, 'active')
        assert result['status'] == 'active'


# ── HTTPRepositoryCommunicationImpl ───────────────────────────────────────────────

class TestHTTPRepositoryCommunicationImpl:

    @pytest.fixture
    def comm(self):
        with patch('requests.Session'):
            repo = HTTPRepositoryCommunicationImpl(['http://repo:5002'], DeploymentMode.MICROSERVICES)
            repo.session = Mock()
            return repo

    def _ok(self, data):
        resp = Mock()
        resp.json.return_value = data
        return resp

    def test_init_microservices_sets_mode(self, comm):
        assert comm.get_mode() == CommunicationMode.MICROSERVICES_HTTP

    def test_init_layered_sets_layered_mode(self):
        with patch('requests.Session'):
            repo = HTTPRepositoryCommunicationImpl(['http://repo:5002'], DeploymentMode.LAYERED)
            assert repo.get_mode() == CommunicationMode.LAYERED_HTTP

    def test_get_by_id(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 1}})
        result = comm.get_by_id('user', 1)
        assert result['data']['id'] == 1

    def test_create(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 2}})
        result = comm.create('user', {'username': 'new', 'email': 'n@t.com'})
        assert result['data']['id'] == 2

    def test_update(self, comm):
        comm.session.request.return_value = self._ok({'data': {'id': 1}})
        result = comm.update('user', 1, {'first_name': 'X'})
        assert result is not None

    def test_delete(self, comm):
        comm.session.request.return_value = self._ok({'success': True})
        result = comm.delete('user', 1)
        assert result is not None

    def test_query(self, comm):
        comm.session.request.return_value = self._ok({'data': {'items': [], 'total': 0}})
        result = comm.query('user', {'role': 'admin'}, page=1, per_page=10)
        assert result is not None

    def test_call_posts_to_repository_endpoint(self, comm):
        comm.session.request.return_value = self._ok({'result': 'ok'})
        comm.call('getUserById', user_id=1)
        comm.session.request.assert_called_once()

    def test_health_check_returns_true_on_200(self, comm):
        mock_resp = Mock()
        mock_resp.status_code = 200
        comm.session.get.return_value = mock_resp
        assert comm.health_check() is True

    def test_health_check_returns_false_on_exception(self, comm):
        comm.session.get.side_effect = Exception("down")
        assert comm.health_check() is False

    def test_make_request_raises_api_exception_on_error(self, comm):
        comm.session.request.side_effect = Exception("connection refused")
        with pytest.raises(APIException):
            comm._make_request('GET', '/repository/user/1')
