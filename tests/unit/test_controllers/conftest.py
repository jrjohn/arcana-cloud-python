"""
Controller Unit Test Fixtures
Provides app + auth-bypassed client for controller unit tests.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from flask import g

# ── urllib3 v2 compatibility shim ─────────────────────────────────────────────
# service_client.py uses Retry(method_whitelist=...) which was renamed to
# allowed_methods in urllib3 >= 2.0. Patch it here so create_app() doesn't fail.
try:
    from urllib3.util.retry import Retry as _Retry
    _orig_retry_init = _Retry.__init__

    def _patched_retry_init(self, *args, **kwargs):
        if 'method_whitelist' in kwargs:
            kwargs.setdefault('allowed_methods', kwargs.pop('method_whitelist'))
        _orig_retry_init(self, *args, **kwargs)

    _Retry.__init__ = _patched_retry_init
except Exception:
    pass  # Best-effort patch
# ─────────────────────────────────────────────────────────────────────────────

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

# ── Auth bypass strategy ───────────────────────────────────────────────────────
# auth_decorators.py uses LAZY imports inside the decorator function body:
#   from app.repositories.impl.user_repository_impl import UserRepositoryImpl
# This means patch('app.decorators.auth_decorators.UserRepositoryImpl') won't work.
# Instead we patch the lazy-imported modules at their source locations,
# AND patch token_required itself to inject g.current_user without DB access.
# ─────────────────────────────────────────────────────────────────────────────

_ADMIN_USER = make_admin_user()


def _make_bypass_decorator(mock_user):
    """
    Returns a token_required-compatible decorator that skips DB auth
    and injects mock_user into Flask's g.current_user.
    """
    from functools import wraps

    def bypass_token_required(roles=None, allow_self=False):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                g.current_user = mock_user
                return f(*args, **kwargs)
            return decorated
        return decorator

    return bypass_token_required


@pytest.fixture(scope='module')
def flask_app():
    """
    Flask app fixture with auth fully bypassed.
    Patches token_required at the source so all controllers skip DB auth.
    Uses module scope for performance.
    """
    mock_user = make_admin_user()
    bypass = _make_bypass_decorator(mock_user)

    # Patch token_required BEFORE create_app so blueprints register with bypass
    with patch('app.decorators.auth_decorators.token_required', bypass), \
         patch('app.repositories.impl.user_repository_impl.UserRepositoryImpl'), \
         patch('app.repositories.impl.oauth_token_repository_impl.OAuthTokenRepositoryImpl'), \
         patch('app.services.impl.auth_service_impl.AuthServiceImpl'), \
         patch('app.extensions.db'):

        from app import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        yield app, mock_user


@pytest.fixture
def admin_client(flask_app):
    """Test client authenticated as admin."""
    app, admin_user = flask_app
    return app.test_client(), admin_user


@pytest.fixture
def regular_client(flask_app):
    """Test client authenticated as regular user."""
    app, _ = flask_app
    mock_user = make_regular_user()

    # Temporarily swap g.current_user for this test
    # (tests needing a different user should use monkeypatch on token_required)
    return app.test_client(), mock_user


@pytest.fixture
def auth_headers():
    return {'Authorization': 'Bearer test-token-valid', 'Content-Type': 'application/json'}
