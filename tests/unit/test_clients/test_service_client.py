"""
ServiceClient Unit Tests
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import requests

from app.services.clients.service_client import ServiceClient
from app.utils.exceptions import (
    ServiceUnavailableError, ValidationError, NotFoundError,
    ConflictError, AuthenticationError, AuthorizationError
)


@pytest.fixture
def client():
    with patch.dict('os.environ', {'USER_SERVICE_URL': 'http://localhost:5001'}):
        return ServiceClient('user-service', timeout=5)


class TestServiceClientInit:
    def test_init_with_single_url(self):
        with patch.dict('os.environ', {'USER_SERVICE_URL': 'http://localhost:5001'}):
            c = ServiceClient('user-service')
            info = c.get_service_info()
            assert 'user-service' == info['service_name']

    def test_init_with_multiple_urls(self):
        with patch.dict('os.environ', {'USER_SERVICE_URLS': 'http://host1:5001,http://host2:5001'}):
            c = ServiceClient('user-service')
            info = c.get_service_info()
            assert len(info['all_urls']) == 2

    def test_init_default_url(self):
        with patch.dict('os.environ', {}, clear=True):
            c = ServiceClient('user-service')
            assert c.service_name == 'user-service'


class TestServiceClientCall:
    def test_get_success(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'data': {'id': 1}}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get('/api/users/1')
        assert result == {'data': {'id': 1}}

    def test_post_success(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'data': {'id': 2}}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.post('/api/users', data={'username': 'john'})
        assert result['data']['id'] == 2

    def test_put_success(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'data': {'id': 1, 'username': 'updated'}}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.put('/api/users/1', data={'username': 'updated'})
        assert result['data']['username'] == 'updated'

    def test_delete_success(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'success': True}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.delete('/api/users/1')
        assert result['success'] is True

    def test_patch_success(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'data': {'status': 'ACTIVE'}}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.patch('/api/users/1/status', data={'status': 'ACTIVE'})
        assert result['data']['status'] == 'ACTIVE'

    def test_non_json_response(self, client):
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "OK"
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get('/health')
        assert result == {'data': 'OK'}

    def test_connection_error_raises_service_unavailable(self, client):
        with patch.object(client.session, 'request',
                          side_effect=requests.exceptions.ConnectionError("refused")):
            with pytest.raises(ServiceUnavailableError):
                client.get('/api/users')

    def test_timeout_raises_service_unavailable(self, client):
        with patch.object(client.session, 'request',
                          side_effect=requests.exceptions.Timeout("timed out")):
            with pytest.raises(ServiceUnavailableError):
                client.get('/api/users')

    def test_unexpected_error_raises_service_unavailable(self, client):
        with patch.object(client.session, 'request',
                          side_effect=RuntimeError("unexpected")):
            with pytest.raises(ServiceUnavailableError):
                client.get('/api/users')


class TestServiceClientHTTPErrors:
    def _make_http_error(self, status_code: int, body: dict = None):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = body or {'error': f'HTTP {status_code}'}
        http_err = requests.exceptions.HTTPError(response=response)
        return http_err

    def test_400_raises_validation_error(self, client):
        err = self._make_http_error(400, {'error': 'bad input'})
        with patch.object(client.session, 'request', side_effect=err):
            with pytest.raises(ValidationError):
                client.post('/api/users', data={})

    def test_401_raises_authentication_error(self, client):
        err = self._make_http_error(401, {'error': 'unauthorized'})
        with patch.object(client.session, 'request', side_effect=err):
            with pytest.raises(AuthenticationError):
                client.get('/api/users/me')

    def test_403_raises_authorization_error(self, client):
        err = self._make_http_error(403, {'error': 'forbidden'})
        with patch.object(client.session, 'request', side_effect=err):
            with pytest.raises(AuthorizationError):
                client.get('/api/admin')

    def test_404_raises_not_found(self, client):
        err = self._make_http_error(404, {'error': 'not found'})
        with patch.object(client.session, 'request', side_effect=err):
            with pytest.raises(NotFoundError):
                client.get('/api/users/999')

    def test_409_raises_conflict(self, client):
        err = self._make_http_error(409, {'error': 'duplicate'})
        with patch.object(client.session, 'request', side_effect=err):
            with pytest.raises(ConflictError):
                client.post('/api/users', data={'username': 'existing'})

    def test_500_raises_service_unavailable(self, client):
        err = self._make_http_error(500, {'error': 'internal error'})
        with patch.object(client.session, 'request', side_effect=err):
            with pytest.raises(ServiceUnavailableError):
                client.get('/api/users')


class TestServiceClientHealthCheck:
    def test_health_check_healthy(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'healthy'}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            assert client.health_check() is True

    def test_health_check_unhealthy(self, client):
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'degraded'}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, 'request', return_value=mock_response):
            assert client.health_check() is False

    def test_health_check_exception(self, client):
        with patch.object(client.session, 'request',
                          side_effect=requests.exceptions.ConnectionError()):
            assert client.health_check() is False

    def test_get_service_info(self, client):
        info = client.get_service_info()
        assert info['service_name'] == 'user-service'
        assert 'all_urls' in info
        assert 'healthy_urls' in info
        assert 'health_status' in info
