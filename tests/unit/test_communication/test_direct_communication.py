"""
Direct Communication Unit Tests
Tests for app/communication/impl/direct.py
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from app.communication.impl.direct_impl import DirectServiceCommunicationImpl, DirectRepositoryCommunicationImpl
from app.communication.interfaces import CommunicationMode, CommunicationProtocol
from app.models.user import User, UserRole, UserStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(uid=1, username='alice'):
    u = MagicMock(spec=User)
    u.id = uid
    u.username = username
    u.email = f'{username}@example.com'
    u.first_name = 'Alice'
    u.last_name = 'Test'
    u.phone = None
    u.avatar_url = None
    u.role = UserRole.USER
    u.status = UserStatus.ACTIVE
    u.is_verified = False
    u.is_active = True
    u.created_at = None
    u.updated_at = None
    u.last_login_at = None
    # toDict() is called by DirectServiceCommunicationImpl to serialise User objects
    u.toDict.return_value = {
        'id': uid, 'username': username,
        'email': f'{username}@example.com',
        'first_name': 'Alice', 'last_name': 'Test',
        'role': UserRole.USER.value, 'status': UserStatus.ACTIVE.value,
        'is_verified': False, 'is_active': True,
    }
    return u


class TestDirectServiceCommunicationInit:
    def test_mode_is_monolithic(self):
        svc = Mock()
        comm = DirectServiceCommunicationImpl(svc)
        assert comm.get_mode() == CommunicationMode.MONOLITHIC

    def test_protocol_is_direct(self):
        svc = Mock()
        comm = DirectServiceCommunicationImpl(svc)
        assert comm.get_protocol() == CommunicationProtocol.DIRECT

    def test_health_check_true(self):
        svc = Mock()
        comm = DirectServiceCommunicationImpl(svc)
        assert comm.health_check() is True


class TestDirectServiceCommunicationCall:
    """Tests for the generic call() proxy"""

    def test_call_delegates_to_service_method(self):
        svc = Mock()
        svc.someMethod.return_value = 'result'
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.call('someMethod', foo='bar')
        svc.someMethod.assert_called_once_with(foo='bar')
        assert result == 'result'

    def test_call_converts_model_to_dict(self):
        svc = Mock()
        user = _make_user()
        svc.getUser.return_value = user
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.call('getUser', user_id=1)
        assert isinstance(result, dict)
        assert result['username'] == 'alice'


class TestDirectServiceCommunicationGetUsers:
    def test_get_users_delegates(self):
        svc = Mock()
        svc.getUsers.return_value = {
            'items': [],
            'pagination': {'page': 1, 'per_page': 20, 'total': 0}
        }
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.get_users(page=1, per_page=20)
        svc.getUsers.assert_called_once_with(page=1, per_page=20)
        assert 'items' in result

    def test_get_users_passes_filters(self):
        svc = Mock()
        svc.getUsers.return_value = {'items': [], 'pagination': {}}
        comm = DirectServiceCommunicationImpl(svc)
        comm.get_users(page=2, per_page=10, role=UserRole.ADMIN)
        svc.getUsers.assert_called_once_with(page=2, per_page=10, role=UserRole.ADMIN)


class TestDirectServiceCommunicationGetUserById:
    def test_get_user_by_id(self):
        svc = Mock()
        user = _make_user(uid=5)
        svc.getUserById.return_value = user
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.get_user_by_id(5)
        svc.getUserById.assert_called_once_with(5)
        assert isinstance(result, dict)
        assert result['id'] == 5


class TestDirectServiceCommunicationCreateUser:
    def test_create_user(self):
        svc = Mock()
        user = _make_user()
        svc.createUser.return_value = user
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.create_user({
            'username': 'alice', 'email': 'alice@example.com', 'password': 'Pass123!'
        })
        svc.createUser.assert_called_once()
        assert result['username'] == 'alice'


class TestDirectServiceCommunicationUpdateUser:
    def test_update_user(self):
        svc = Mock()
        user = _make_user()
        user.first_name = 'Updated'
        user.toDict.return_value['first_name'] = 'Updated'
        svc.updateUser.return_value = user
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.update_user(1, {'first_name': 'Updated'})
        svc.updateUser.assert_called_once_with(1, first_name='Updated')
        assert result['first_name'] == 'Updated'


class TestDirectServiceCommunicationDeleteUser:
    def test_delete_user(self):
        svc = Mock()
        svc.deleteUser.return_value = None
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.delete_user(1)
        svc.deleteUser.assert_called_once_with(1)
        assert result['success'] is True


class TestDirectServiceCommunicationChangePassword:
    def test_change_password(self):
        svc = Mock()
        svc.changePassword.return_value = None
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.change_password(1, 'old', 'new')
        svc.changePassword.assert_called_once_with(1, 'old', 'new')
        assert result['success'] is True


class TestDirectServiceCommunicationVerifyUser:
    def test_verify_user(self):
        svc = Mock()
        user = _make_user()
        user.is_verified = True
        user.toDict.return_value['is_verified'] = True
        svc.verifyUser.return_value = user
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.verify_user(1)
        svc.verifyUser.assert_called_once_with(1)
        assert result['is_verified'] is True


class TestDirectServiceCommunicationUpdateUserStatus:
    def test_update_user_status(self):
        svc = Mock()
        user = _make_user()
        user.status = UserStatus.INACTIVE
        user.toDict.return_value['status'] = UserStatus.INACTIVE.value
        svc.updateUserStatus.return_value = user
        comm = DirectServiceCommunicationImpl(svc)
        result = comm.update_user_status(1, 'inactive')
        svc.updateUserStatus.assert_called_once_with(1, UserStatus.INACTIVE)
        assert result['status'] == UserStatus.INACTIVE.value


# ---------------------------------------------------------------------------
# DirectRepositoryCommunicationImpl
# ---------------------------------------------------------------------------

class TestDirectRepositoryCommunicationInit:
    def test_mode_is_monolithic(self):
        repo = Mock()
        comm = DirectRepositoryCommunicationImpl(repo)
        assert comm.get_mode() == CommunicationMode.MONOLITHIC

    def test_protocol_is_direct(self):
        repo = Mock()
        comm = DirectRepositoryCommunicationImpl(repo)
        assert comm.get_protocol() == CommunicationProtocol.DIRECT

    def test_health_check_true(self):
        repo = Mock()
        comm = DirectRepositoryCommunicationImpl(repo)
        assert comm.health_check() is True


class TestDirectRepositoryCommunicationCall:
    def test_call_delegates_to_repo_method(self):
        repo = Mock()
        repo.someMethod.return_value = 'value'
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.call('someMethod', x=1)
        repo.someMethod.assert_called_once_with(x=1)
        assert result == 'value'

    def test_call_converts_model_to_dict(self):
        repo = Mock()
        user = _make_user()
        repo.findUser.return_value = user
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.call('findUser', user_id=1)
        assert isinstance(result, dict)


class TestDirectRepositoryCommunicationGetById:
    def test_get_by_id_found(self):
        repo = Mock()
        user = _make_user(uid=3)
        repo.getById.return_value = user
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.get_by_id('User', 3)
        repo.getById.assert_called_once_with(3)
        assert result['id'] == 3

    def test_get_by_id_not_found(self):
        repo = Mock()
        repo.getById.return_value = None
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.get_by_id('User', 999)
        assert result is None


class TestDirectRepositoryCommunicationCreate:
    def test_create_delegates(self):
        repo = Mock()
        user = _make_user()
        repo.create.return_value = user
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.create('User', {'username': 'alice'})
        repo.create.assert_called_once_with(username='alice')
        assert result['username'] == 'alice'


class TestDirectRepositoryCommunicationUpdate:
    def test_update_delegates(self):
        repo = Mock()
        user = _make_user()
        user.first_name = 'Bob'
        user.toDict.return_value['first_name'] = 'Bob'
        repo.update.return_value = user
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.update('User', 1, {'first_name': 'Bob'})
        repo.update.assert_called_once_with(1, first_name='Bob')
        assert result['first_name'] == 'Bob'


class TestDirectRepositoryCommunicationDelete:
    def test_delete_delegates(self):
        repo = Mock()
        repo.delete.return_value = None
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.delete('User', 1)
        repo.delete.assert_called_once_with(1)
        assert result['success'] is True


class TestDirectRepositoryCommunicationQuery:
    def test_query_delegates(self):
        repo = Mock()
        user = _make_user()
        repo.getAll.return_value = ([user], 1)
        comm = DirectRepositoryCommunicationImpl(repo)
        result = comm.query('User', {}, page=1, per_page=20)
        assert result['total'] == 1
        assert result['page'] == 1
        assert isinstance(result['items'], list)
