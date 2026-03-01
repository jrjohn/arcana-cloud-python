"""
UserServiceAdapter Unit Tests
Tests for MonolithicUserService, LayeredUserService, and get_user_service factory
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.models.user import User, UserRole, UserStatus


class TestGetUserServiceFactory:
    """Tests for the get_user_service factory function"""

    def test_returns_monolithic_service_by_default(self):
        with patch.dict('os.environ', {'DEPLOYMENT_LAYER': 'monolithic'}):
            with patch('app.services.adapters.user_service_adapter.db') as mock_db, \
                 patch('app.services.adapters.user_service_adapter.UserRepositoryImpl') as mock_repo_cls, \
                 patch('app.services.adapters.user_service_adapter.UserServiceImpl') as mock_svc_cls:

                from app.services.adapters.user_service_adapter import (
                    get_user_service, MonolithicUserService
                )
                mock_repo_cls.return_value = Mock()
                mock_svc_cls.return_value = Mock()

                svc = get_user_service()
                assert isinstance(svc, MonolithicUserService)

    def test_returns_layered_service_for_controller_layer(self):
        with patch.dict('os.environ', {'DEPLOYMENT_LAYER': 'controller'}):
            with patch('app.services.adapters.user_service_adapter.ServiceClient') as mock_client_cls:
                mock_client_cls.return_value = Mock()

                from app.services.adapters.user_service_adapter import (
                    get_user_service, LayeredUserService
                )
                svc = get_user_service()
                assert isinstance(svc, LayeredUserService)

    def test_returns_monolithic_for_service_layer(self):
        with patch.dict('os.environ', {'DEPLOYMENT_LAYER': 'service'}):
            with patch('app.services.adapters.user_service_adapter.db') as mock_db, \
                 patch('app.services.adapters.user_service_adapter.UserRepositoryImpl') as mock_repo_cls, \
                 patch('app.services.adapters.user_service_adapter.UserServiceImpl') as mock_svc_cls:

                from app.services.adapters.user_service_adapter import (
                    get_user_service, MonolithicUserService
                )
                mock_repo_cls.return_value = Mock()
                mock_svc_cls.return_value = Mock()

                svc = get_user_service()
                assert isinstance(svc, MonolithicUserService)


class TestMonolithicUserService:
    """Tests for MonolithicUserService delegation"""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def monolithic_svc(self, mock_service):
        with patch('app.services.adapters.user_service_adapter.db'), \
             patch('app.services.adapters.user_service_adapter.UserRepositoryImpl'), \
             patch('app.services.adapters.user_service_adapter.UserServiceImpl',
                   return_value=mock_service):
            from app.services.adapters.user_service_adapter import MonolithicUserService
            svc = MonolithicUserService()
            svc.service = mock_service
            return svc

    def test_get_users_delegates_to_service(self, monolithic_svc, mock_service):
        expected = {'users': [], 'total': 0}
        mock_service.getUsers.return_value = expected

        result = monolithic_svc.getUsers(page=1, per_page=10)
        assert result == expected
        mock_service.getUsers.assert_called_once_with(
            page=1, per_page=10, role=None, status=None
        )

    def test_get_user_by_id_delegates(self, monolithic_svc, mock_service):
        user = User(username='john', email='j@test.com', password='hash')
        user.id = 1
        mock_service.getUserById.return_value = user

        result = monolithic_svc.getUserById(1)
        assert result is user
        mock_service.getUserById.assert_called_once_with(1)

    def test_create_user_delegates(self, monolithic_svc, mock_service):
        user = User(username='john', email='j@test.com', password='hash')
        mock_service.createUser.return_value = user

        result = monolithic_svc.createUser('john', 'j@test.com', 'Password1')
        assert result is user
        mock_service.createUser.assert_called_once()

    def test_update_user_delegates(self, monolithic_svc, mock_service):
        user = User(username='updated', email='u@test.com', password='hash')
        mock_service.updateUser.return_value = user

        result = monolithic_svc.updateUser(1, first_name='Updated')
        assert result is user
        mock_service.updateUser.assert_called_once_with(1, first_name='Updated')

    def test_delete_user_delegates(self, monolithic_svc, mock_service):
        mock_service.deleteUser.return_value = None

        monolithic_svc.deleteUser(1)
        mock_service.deleteUser.assert_called_once_with(1)

    def test_change_password_delegates(self, monolithic_svc, mock_service):
        mock_service.changePassword.return_value = None

        monolithic_svc.changePassword(1, 'OldPass1', 'NewPass1')
        mock_service.changePassword.assert_called_once_with(1, 'OldPass1', 'NewPass1')

    def test_verify_user_delegates(self, monolithic_svc, mock_service):
        user = User(username='john', email='j@test.com', password='hash')
        user.is_verified = True
        mock_service.verifyUser.return_value = user

        result = monolithic_svc.verifyUser(1)
        assert result.is_verified is True

    def test_update_user_status_delegates(self, monolithic_svc, mock_service):
        user = User(username='john', email='j@test.com', password='hash')
        user.status = UserStatus.ACTIVE
        mock_service.updateUserStatus.return_value = user

        result = monolithic_svc.updateUserStatus(1, UserStatus.ACTIVE)
        assert result.status == UserStatus.ACTIVE


class TestLayeredUserService:
    """Tests for LayeredUserService HTTP delegation"""

    @pytest.fixture
    def mock_client(self):
        return Mock()

    @pytest.fixture
    def layered_svc(self, mock_client):
        with patch('app.services.adapters.user_service_adapter.ServiceClient',
                   return_value=mock_client):
            from app.services.adapters.user_service_adapter import LayeredUserService
            svc = LayeredUserService()
            svc.client = mock_client
            return svc

    def test_get_users_calls_http_client(self, layered_svc, mock_client):
        mock_client.get.return_value = {'success': True, 'data': {'users': [], 'pagination': {'total': 0}}}

        result = layered_svc.getUsers(page=1, per_page=10)
        assert 'users' in result
        mock_client.get.assert_called_once()

    def test_get_user_by_id_calls_http_client(self, layered_svc, mock_client):
        mock_client.get.return_value = {
            'success': True,
            'data': {
                'id': 1, 'username': 'john', 'email': 'j@test.com',
                'role': 'USER', 'status': 'ACTIVE',
                'password_hash': 'hash', 'is_verified': True,
                'first_name': None, 'last_name': None,
                'created_at': None, 'updated_at': None, 'last_login_at': None
            }
        }

        result = layered_svc.getUserById(1)
        assert result is not None
        mock_client.get.assert_called_once()
