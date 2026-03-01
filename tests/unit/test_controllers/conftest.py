"""
Controller Unit Test Fixtures
Provides app + auth-bypassed client for controller unit tests.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from flask import g

from app.models.user import User, UserRole


def make_admin_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.role = UserRole.ADMIN
    user.email = 'admin@test.com'
    user.first_name = 'Admin'
    user.last_name = 'User'
    return user


def make_regular_user(user_id=2):
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = UserRole.USER
    user.email = 'user@test.com'
    user.first_name = 'Regular'
    user.last_name = 'User'
    return user


AUTH_HEADER = {'Authorization': 'Bearer test-token-valid', 'Content-Type': 'application/json'}


def make_client(app, mock_user):
    """Create a test client that bypasses auth by patching validateToken."""
    client = app.test_client()

    # We need to patch all auth internals per request via a fixture
    # Return both client and the mock user so tests can configure expectations
    return client


@pytest.fixture(scope='module')
def app_with_mocked_auth():
    """
    Flask app fixture that patches token_required to inject a mock user.
    Uses module scope for performance (app created once per test module).
    """
    with patch('app.decorators.auth_decorators.UserRepositoryImpl') as MockUserRepo, \
         patch('app.decorators.auth_decorators.OAuthTokenRepositoryImpl') as MockTokenRepo, \
         patch('app.decorators.auth_decorators.AuthServiceImpl') as MockAuthService, \
         patch('app.decorators.auth_decorators.db') as mock_db:

        admin_user = make_admin_user()
        MockAuthService.return_value.validateToken.return_value = admin_user
        MockUserRepo.return_value = MagicMock()
        MockTokenRepo.return_value = MagicMock()
        mock_db.session = MagicMock()

        from app import create_app
        flask_app = create_app('testing')
        flask_app.config['TESTING'] = True

        yield flask_app, admin_user, MockAuthService


@pytest.fixture
def admin_client(app_with_mocked_auth):
    """Test client authenticated as admin."""
    flask_app, admin_user, _ = app_with_mocked_auth
    return flask_app.test_client(), admin_user


@pytest.fixture
def auth_headers():
    return {'Authorization': 'Bearer test-token-valid', 'Content-Type': 'application/json'}
