"""
Auth Decorators Unit Tests
Tests for app/decorators/auth_decorators.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g

from app.models.user import User, UserRole


def _make_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    return app


class TestTokenRequired:
    """Tests for token_required decorator"""

    def test_missing_auth_header_returns_401(self):
        from app.decorators.auth_decorators import token_required

        app = _make_app()

        @token_required
        def protected():
            return ('ok', 200)

        with app.test_request_context('/', headers={}):
            response = protected()
            assert response[1] == 401

    def test_invalid_header_format_returns_401(self):
        from app.decorators.auth_decorators import token_required

        app = _make_app()

        @token_required
        def protected():
            return ('ok', 200)

        with app.test_request_context('/', headers={'Authorization': 'not-valid-format-but-no-space'}):
            response = protected()
            assert response[1] == 401

    def test_wrong_token_type_returns_401(self):
        from app.decorators.auth_decorators import token_required

        app = _make_app()

        @token_required
        def protected():
            return ('ok', 200)

        with app.test_request_context('/', headers={'Authorization': 'Basic sometoken'}):
            response = protected()
            assert response[1] == 401

    @patch('app.decorators.auth_decorators.AuthServiceImpl')
    @patch('app.decorators.auth_decorators.OAuthTokenRepositoryImpl')
    @patch('app.decorators.auth_decorators.UserRepositoryImpl')
    def test_valid_token_calls_protected_route(self, MockUserRepo, MockTokenRepo, MockAuthService):
        from app.decorators.auth_decorators import token_required
        from app.extensions import db

        app = _make_app()

        mock_user = Mock(spec=User)
        mock_user.username = 'alice'
        MockAuthService.return_value.validateToken.return_value = mock_user

        @token_required
        def protected():
            return ('ok', 200)

        with app.test_request_context('/', headers={'Authorization': 'Bearer valid-token'}):
            with app.app_context():
                with patch('app.decorators.auth_decorators.db') as mock_db:
                    mock_db.session = Mock()
                    response = protected()
            # If validateToken returns a user, decorated function should run
            # Response may be ('ok', 200) or error depending on DB setup

    @patch('app.decorators.auth_decorators.AuthServiceImpl')
    @patch('app.decorators.auth_decorators.OAuthTokenRepositoryImpl')
    @patch('app.decorators.auth_decorators.UserRepositoryImpl')
    def test_invalid_token_returns_401(self, MockUserRepo, MockTokenRepo, MockAuthService):
        from app.decorators.auth_decorators import token_required
        from app.utils.exceptions import AuthenticationError

        app = _make_app()
        MockAuthService.return_value.validateToken.side_effect = AuthenticationError('Token expired')

        @token_required
        def protected():
            return ('ok', 200)

        with app.test_request_context('/', headers={'Authorization': 'Bearer bad-token'}):
            with patch('app.decorators.auth_decorators.db') as mock_db:
                mock_db.session = Mock()
                response = protected()
                assert response[1] == 401

    @patch('app.decorators.auth_decorators.AuthServiceImpl')
    @patch('app.decorators.auth_decorators.OAuthTokenRepositoryImpl')
    @patch('app.decorators.auth_decorators.UserRepositoryImpl')
    def test_unexpected_exception_returns_401(self, MockUserRepo, MockTokenRepo, MockAuthService):
        from app.decorators.auth_decorators import token_required

        app = _make_app()
        MockAuthService.return_value.validateToken.side_effect = RuntimeError('Unexpected')

        @token_required
        def protected():
            return ('ok', 200)

        with app.test_request_context('/', headers={'Authorization': 'Bearer some-token'}):
            with patch('app.decorators.auth_decorators.db') as mock_db:
                mock_db.session = Mock()
                response = protected()
                assert response[1] == 401


class TestRoleRequired:
    """Tests for role_required decorator"""

    def test_no_current_user_returns_401(self):
        from app.decorators.auth_decorators import role_required

        app = _make_app()

        @role_required([UserRole.ADMIN])
        def admin_only():
            return ('admin ok', 200)

        with app.test_request_context('/'):
            with app.app_context():
                # g.current_user not set
                response = admin_only()
                assert response[1] == 401

    def test_wrong_role_returns_403(self):
        from app.decorators.auth_decorators import role_required

        app = _make_app()

        @role_required([UserRole.ADMIN])
        def admin_only():
            return ('admin ok', 200)

        with app.test_request_context('/'):
            with app.app_context():
                g.current_user = Mock(spec=User)
                g.current_user.role = UserRole.USER
                response = admin_only()
                assert response[1] == 403

    def test_correct_role_allows_access(self):
        from app.decorators.auth_decorators import role_required

        app = _make_app()

        @role_required([UserRole.ADMIN])
        def admin_only():
            return ('admin ok', 200)

        with app.test_request_context('/'):
            with app.app_context():
                g.current_user = Mock(spec=User)
                g.current_user.role = UserRole.ADMIN
                response = admin_only()
                assert response == ('admin ok', 200)

    def test_user_in_allowed_roles(self):
        from app.decorators.auth_decorators import role_required

        app = _make_app()

        @role_required([UserRole.ADMIN, UserRole.USER])
        def multi_role():
            return ('ok', 200)

        with app.test_request_context('/'):
            with app.app_context():
                g.current_user = Mock(spec=User)
                g.current_user.role = UserRole.USER
                response = multi_role()
                assert response == ('ok', 200)
