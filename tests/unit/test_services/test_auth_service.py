"""
Auth Service Unit Tests
Comprehensive tests for AuthServiceImpl
"""
import pytest
import jwt
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.implementations.AuthServiceImpl import AuthServiceImpl
from app.models.user import User, UserRole, UserStatus
from app.models.oauth_token import OAuthToken
from app.utils.Exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ConflictError
)


class TestAuthService:
    """Auth Service test class"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock UserRepository"""
        return Mock()

    @pytest.fixture
    def mock_token_repository(self):
        """Mock OAuthTokenRepository"""
        return Mock()

    @pytest.fixture
    def auth_service(self, mock_user_repository, mock_token_repository):
        """Create AuthService instance"""
        return AuthServiceImpl(mock_user_repository, mock_token_repository)

    @pytest.fixture
    def sample_user(self):
        """Create sample user"""
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        user.id = 1
        user.status = UserStatus.ACTIVE
        user.is_active = True
        return user

    @pytest.fixture
    def sample_token(self):
        """Create sample token"""
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            expires_in=3600,
            refresh_expires_in=2592000
        )
        token.id = 1
        return token

    def test_login_with_username_success(self, auth_service, mock_user_repository,
                                        mock_token_repository, sample_user):
        """Test successful login with username"""
        # Arrange
        mock_user_repository.getByUsername.return_value = sample_user
        mock_token_repository.create.return_value = None
        mock_user_repository.update.return_value = sample_user

        # Act
        result = auth_service.login(
            username_or_email='testuser',
            password='TestPass123'
        )

        # Assert
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'user' in result
        assert result['token_type'] == 'Bearer'
        assert result['user']['username'] == 'testuser'
        mock_user_repository.getByUsername.assert_called_once_with('testuser')
        mock_token_repository.create.assert_called_once()
        mock_user_repository.update.assert_called_once()

    def test_login_with_email_success(self, auth_service, mock_user_repository,
                                      mock_token_repository, sample_user):
        """Test successful login with email"""
        # Arrange
        mock_user_repository.getByEmail.return_value = sample_user
        mock_token_repository.create.return_value = None
        mock_user_repository.update.return_value = sample_user

        # Act
        result = auth_service.login(
            username_or_email='test@example.com',
            password='TestPass123'
        )

        # Assert
        assert 'access_token' in result
        assert 'refresh_token' in result
        mock_user_repository.getByEmail.assert_called_once_with('test@example.com')

    def test_login_user_not_found(self, auth_service, mock_user_repository):
        """Test login with non-existent user"""
        # Arrange
        mock_user_repository.getByUsername.return_value = None

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.login(
                username_or_email='nonexistent',
                password='TestPass123'
            )

        assert "Invalid username/email or password" in str(exc_info.value)

    def test_login_invalid_password(self, auth_service, mock_user_repository, sample_user):
        """Test login with invalid password"""
        # Arrange
        mock_user_repository.getByUsername.return_value = sample_user

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.login(
                username_or_email='testuser',
                password='WrongPassword'
            )

        assert "Invalid username/email or password" in str(exc_info.value)

    def test_login_inactive_user(self, auth_service, mock_user_repository, sample_user):
        """Test login with inactive user"""
        # Arrange
        sample_user.status = UserStatus.INACTIVE
        mock_user_repository.getByUsername.return_value = sample_user

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.login(
                username_or_email='testuser',
                password='TestPass123'
            )

        assert "inactive" in str(exc_info.value).lower()

    def test_login_suspended_user(self, auth_service, mock_user_repository, sample_user):
        """Test login with suspended user"""
        # Arrange
        sample_user.status = UserStatus.SUSPENDED
        mock_user_repository.getByUsername.return_value = sample_user

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.login(
                username_or_email='testuser',
                password='TestPass123'
            )

        assert "suspended" in str(exc_info.value).lower()

    def test_login_deactivated_user(self, auth_service, mock_user_repository, sample_user):
        """Test login with deactivated user"""
        # Arrange
        sample_user.is_active = False
        mock_user_repository.getByUsername.return_value = sample_user

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.login(
                username_or_email='testuser',
                password='TestPass123'
            )

        assert "inactive" in str(exc_info.value).lower()

    def test_login_with_client_info(self, auth_service, mock_user_repository,
                                    mock_token_repository, sample_user):
        """Test login with client information"""
        # Arrange
        mock_user_repository.getByUsername.return_value = sample_user
        mock_token_repository.create.return_value = None
        mock_user_repository.update.return_value = sample_user

        # Act
        result = auth_service.login(
            username_or_email='testuser',
            password='TestPass123',
            client_id='web-app',
            client_name='Web Application',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        # Assert
        assert result is not None
        # Verify token was created with client info
        call_args = mock_token_repository.create.call_args[0][0]
        assert call_args.client_id == 'web-app'
        assert call_args.ip_address == '192.168.1.1'

    def test_logout_success(self, auth_service, mock_token_repository, sample_token):
        """Test successful logout"""
        # Arrange
        mock_token_repository.getByAccessToken.return_value = sample_token
        mock_token_repository.update.return_value = sample_token

        # Act
        result = auth_service.logout('test_access_token')

        # Assert
        assert result is True
        assert sample_token.is_revoked is True
        mock_token_repository.update.assert_called_once()

    def test_logout_token_not_found(self, auth_service, mock_token_repository):
        """Test logout with non-existent token"""
        # Arrange
        mock_token_repository.getByAccessToken.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            auth_service.logout('nonexistent_token')

        assert "Token not found" in str(exc_info.value)

    def test_refresh_token_success(self, auth_service, mock_user_repository,
                                   mock_token_repository, sample_user, sample_token):
        """Test successful token refresh"""
        # Arrange
        mock_token_repository.getByRefreshToken.return_value = sample_token
        mock_user_repository.getById.return_value = sample_user
        mock_token_repository.update.return_value = sample_token

        # Act
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'refresh'
            }
            result = auth_service.refreshToken('test_refresh_token')

        # Assert
        assert 'access_token' in result
        assert result['token_type'] == 'Bearer'
        mock_token_repository.update.assert_called_once()

    def test_refresh_token_invalid_type(self, auth_service):
        """Test refresh token with invalid token type"""
        # Arrange & Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'access'  # Wrong type
            }
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.refreshToken('invalid_token')

            assert "Invalid token type" in str(exc_info.value)

    def test_refresh_token_not_found_in_db(self, auth_service, mock_token_repository):
        """Test refresh token not found in database"""
        # Arrange
        mock_token_repository.getByRefreshToken.return_value = None

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'refresh'
            }
            with pytest.raises(NotFoundError) as exc_info:
                auth_service.refreshToken('test_token')

            assert "Refresh token not found" in str(exc_info.value)

    def test_refresh_token_revoked(self, auth_service, mock_token_repository, sample_token):
        """Test refresh with revoked token"""
        # Arrange
        sample_token.is_revoked = True
        mock_token_repository.getByRefreshToken.return_value = sample_token

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'refresh'
            }
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.refreshToken('test_token')

            assert "revoked" in str(exc_info.value).lower()

    def test_refresh_token_expired(self, auth_service, mock_token_repository, sample_token):
        """Test refresh with expired token"""
        # Arrange
        sample_token.refresh_expires_at = datetime.utcnow() - timedelta(days=1)
        mock_token_repository.getByRefreshToken.return_value = sample_token

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'refresh'
            }
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.refreshToken('test_token')

            assert "expired" in str(exc_info.value).lower()

    def test_validate_token_success(self, auth_service, mock_user_repository,
                                    mock_token_repository, sample_user, sample_token):
        """Test successful token validation"""
        # Arrange
        mock_token_repository.getByAccessToken.return_value = sample_token
        mock_user_repository.getById.return_value = sample_user
        mock_token_repository.update.return_value = sample_token

        # Act
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'access'
            }
            result = auth_service.validateToken('test_access_token')

        # Assert
        assert result == sample_user
        assert sample_token.last_used_at is not None
        mock_token_repository.update.assert_called_once()

    def test_validate_token_invalid_type(self, auth_service):
        """Test validate token with invalid token type"""
        # Arrange & Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'refresh'  # Wrong type
            }
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.validateToken('invalid_token')

            assert "Invalid token type" in str(exc_info.value)

    def test_validate_token_not_found(self, auth_service, mock_token_repository):
        """Test validate token not found in database"""
        # Arrange
        mock_token_repository.getByAccessToken.return_value = None

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'access'
            }
            with pytest.raises(NotFoundError) as exc_info:
                auth_service.validateToken('test_token')

            assert "Token not found" in str(exc_info.value)

    def test_validate_token_expired(self, auth_service, mock_token_repository, sample_token):
        """Test validate expired token"""
        # Arrange
        sample_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        mock_token_repository.getByAccessToken.return_value = sample_token

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'access'
            }
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.validateToken('test_token')

            assert "invalid or expired" in str(exc_info.value).lower()

    def test_validate_token_user_not_found(self, auth_service, mock_user_repository,
                                          mock_token_repository, sample_token):
        """Test validate token when user doesn't exist"""
        # Arrange
        mock_token_repository.getByAccessToken.return_value = sample_token
        mock_user_repository.getById.return_value = None

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'access'
            }
            with pytest.raises(NotFoundError) as exc_info:
                auth_service.validateToken('test_token')

            assert "User not found" in str(exc_info.value)

    def test_validate_token_inactive_user(self, auth_service, mock_user_repository,
                                         mock_token_repository, sample_user, sample_token):
        """Test validate token with inactive user"""
        # Arrange
        sample_user.is_active = False
        mock_token_repository.getByAccessToken.return_value = sample_token
        mock_user_repository.getById.return_value = sample_user

        # Act & Assert
        with patch.object(auth_service, '_verify_jwt_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 1,
                'token_type': 'access'
            }
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.validateToken('test_token')

            assert "not active" in str(exc_info.value).lower()

    def test_revoke_all_tokens_success(self, auth_service, mock_token_repository):
        """Test revoke all user tokens"""
        # Arrange
        mock_token_repository.revokeAllByUserId.return_value = 3

        # Act
        result = auth_service.revokeAllTokens(1)

        # Assert
        assert result == 3
        mock_token_repository.revokeAllByUserId.assert_called_once_with(1)

    def test_get_user_tokens_success(self, auth_service, mock_token_repository, sample_token):
        """Test get user tokens"""
        # Arrange
        mock_token_repository.getByUserId.return_value = [sample_token]

        # Act
        result = auth_service.getUserTokens(1)

        # Assert
        assert len(result) == 1
        assert result[0] == sample_token
        mock_token_repository.getByUserId.assert_called_once_with(1, include_revoked=False)

    def test_register_success(self, auth_service, mock_user_repository,
                              mock_token_repository, sample_user):
        """Test successful user registration"""
        # Arrange
        mock_user_repository.existsByUsername.return_value = False
        mock_user_repository.existsByEmail.return_value = False
        mock_user_repository.create.return_value = sample_user
        mock_user_repository.getByUsername.return_value = sample_user
        mock_token_repository.create.return_value = None
        mock_user_repository.update.return_value = sample_user

        # Act
        result = auth_service.register(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Assert
        assert 'access_token' in result
        assert 'user' in result
        mock_user_repository.create.assert_called_once()

    def test_register_duplicate_username(self, auth_service, mock_user_repository):
        """Test registration with duplicate username"""
        # Arrange
        mock_user_repository.existsByUsername.return_value = True

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            auth_service.register(
                username='testuser',
                email='test@example.com',
                password='TestPass123'
            )

        assert "already exists" in str(exc_info.value)

    def test_register_duplicate_email(self, auth_service, mock_user_repository):
        """Test registration with duplicate email"""
        # Arrange
        mock_user_repository.existsByUsername.return_value = False
        mock_user_repository.existsByEmail.return_value = True

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            auth_service.register(
                username='testuser',
                email='test@example.com',
                password='TestPass123'
            )

        assert "already exists" in str(exc_info.value)

    def test_verify_password_success(self, auth_service, sample_user):
        """Test successful password verification"""
        # Act
        result = auth_service.verifyPassword(sample_user, 'TestPass123')

        # Assert
        assert result is True

    def test_verify_password_failure(self, auth_service, sample_user):
        """Test failed password verification"""
        # Act
        result = auth_service.verifyPassword(sample_user, 'WrongPassword')

        # Assert
        assert result is False

    def test_generate_jwt_token(self, auth_service, sample_user):
        """Test JWT token generation"""
        # Act
        token = auth_service._generate_jwt_token(sample_user, 'access', 3600)

        # Assert
        assert token is not None
        assert isinstance(token, str)

        # Verify token content
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=['HS256'])
        assert decoded['user_id'] == sample_user.id
        assert decoded['username'] == sample_user.username
        assert decoded['token_type'] == 'access'

    def test_verify_jwt_token_success(self, auth_service, sample_user):
        """Test successful JWT token verification"""
        # Arrange
        token = auth_service._generate_jwt_token(sample_user, 'access', 3600)

        # Act
        payload = auth_service._verify_jwt_token(token)

        # Assert
        assert payload['user_id'] == sample_user.id
        assert payload['token_type'] == 'access'

    def test_verify_jwt_token_expired(self, auth_service, sample_user):
        """Test JWT token verification with expired token"""
        # Arrange
        token = auth_service._generate_jwt_token(sample_user, 'access', -1)

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service._verify_jwt_token(token)

        assert "expired" in str(exc_info.value).lower()

    def test_verify_jwt_token_invalid(self, auth_service):
        """Test JWT token verification with invalid token"""
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service._verify_jwt_token('invalid_token')

        assert "Invalid token" in str(exc_info.value)
