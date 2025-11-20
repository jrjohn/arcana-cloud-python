"""
OAuth Token Model Unit Tests
Comprehensive tests for OAuthToken model
"""
import pytest
from datetime import datetime, timedelta

from app.models.OAuthToken import OAuthToken


class TestOAuthTokenModel:
    """OAuth Token Model test class"""

    def test_token_creation_basic(self):
        """Test token creation with basic fields"""
        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )

        # Assert
        assert token.user_id == 1
        assert token.access_token == 'test_access_token'
        assert token.refresh_token is None
        assert token.token_type == 'Bearer'  # Default
        assert token.is_revoked is False  # Default
        assert token.expires_at is not None

    def test_token_creation_with_refresh(self):
        """Test token creation with refresh token"""
        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=2592000
        )

        # Assert
        assert token.refresh_token == 'test_refresh_token'
        assert token.refresh_expires_at is not None

    def test_token_creation_with_client_info(self):
        """Test token creation with client information"""
        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            client_id='web-app',
            client_name='Web Application',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        # Assert
        assert token.client_id == 'web-app'
        assert token.client_name == 'Web Application'
        assert token.ip_address == '192.168.1.1'
        assert token.user_agent == 'Mozilla/5.0'

    def test_token_creation_with_scope(self):
        """Test token creation with scope"""
        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            scope='read write delete'
        )

        # Assert
        assert token.scope == 'read write delete'

    def test_token_expiration_calculation(self):
        """Test that expiration time is calculated correctly"""
        # Arrange
        before = datetime.utcnow()

        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600  # 1 hour
        )

        # Assert
        after = datetime.utcnow()
        expected_expiry = before + timedelta(seconds=3600)

        # Allow 1 second tolerance for test execution time
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 1

    def test_refresh_token_expiration_calculation(self):
        """Test that refresh token expiration is calculated correctly"""
        # Arrange
        before = datetime.utcnow()

        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=2592000  # 30 days
        )

        # Assert
        after = datetime.utcnow()
        expected_expiry = before + timedelta(seconds=2592000)

        # Allow 1 second tolerance
        assert abs((token.refresh_expires_at - expected_expiry).total_seconds()) < 1

    def test_is_expired_not_expired(self):
        """Test token is not expired when valid"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600  # Expires in 1 hour
        )

        # Act
        result = token.isExpired()

        # Assert
        assert result is False

    def test_is_expired_expired(self):
        """Test token is expired"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=-3600  # Expired 1 hour ago
        )

        # Act
        result = token.isExpired()

        # Assert
        assert result is True

    def test_is_expired_just_expired(self):
        """Test token that just expired"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=0  # Expires now
        )

        # Act - wait a tiny bit to ensure it's expired
        import time
        time.sleep(0.01)
        result = token.isExpired()

        # Assert
        assert result is True

    def test_is_refresh_expired_not_expired(self):
        """Test refresh token is not expired"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=2592000  # 30 days
        )

        # Act
        result = token.isRefreshExpired()

        # Assert
        assert result is False

    def test_is_refresh_expired_expired(self):
        """Test refresh token is expired"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=-86400  # Expired 1 day ago
        )

        # Act
        result = token.isRefreshExpired()

        # Assert
        assert result is True

    def test_is_refresh_expired_no_refresh_token(self):
        """Test refresh expiration when no refresh token"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )

        # Act
        result = token.isRefreshExpired()

        # Assert
        assert result is True  # Should return True if no refresh token

    def test_is_valid_valid_token(self):
        """Test valid token returns True"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )

        # Act
        result = token.isValid()

        # Assert
        assert result is True

    def test_is_valid_expired_token(self):
        """Test expired token returns False"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=-3600  # Expired
        )

        # Act
        result = token.isValid()

        # Assert
        assert result is False

    def test_is_valid_revoked_token(self):
        """Test revoked token returns False"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )
        token.revoke()

        # Act
        result = token.isValid()

        # Assert
        assert result is False

    def test_revoke_token(self):
        """Test revoking a token"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )
        assert token.is_revoked is False
        assert token.revoked_at is None

        # Act
        before_revoke = datetime.utcnow()
        token.revoke()
        after_revoke = datetime.utcnow()

        # Assert
        assert token.is_revoked is True
        assert token.revoked_at is not None
        assert before_revoke <= token.revoked_at <= after_revoke

    def test_update_last_used(self):
        """Test updating last used timestamp"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )
        assert token.last_used_at is None

        # Act
        before_update = datetime.utcnow()
        token.updateLastUsed()
        after_update = datetime.utcnow()

        # Assert
        assert token.last_used_at is not None
        assert before_update <= token.last_used_at <= after_update

    def test_to_dict_without_tokens(self):
        """Test converting token to dictionary without token values"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=2592000
        )
        token.id = 1
        token.client_id = 'web-app'

        # Act
        token_dict = token.toDict()

        # Assert
        assert token_dict['id'] == 1
        assert token_dict['user_id'] == 1
        assert token_dict['token_type'] == 'Bearer'
        assert token_dict['client_id'] == 'web-app'
        assert token_dict['is_revoked'] is False
        assert 'access_token' not in token_dict
        assert 'refresh_token' not in token_dict

    def test_to_dict_with_tokens(self):
        """Test converting token to dictionary with token values"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=2592000
        )
        token.id = 1

        # Act
        token_dict = token.toDict(include_tokens=True)

        # Assert
        assert 'access_token' in token_dict
        assert 'refresh_token' in token_dict
        assert token_dict['access_token'] == 'test_access_token'
        assert token_dict['refresh_token'] == 'test_refresh_token'
        assert 'refresh_expires_at' in token_dict

    def test_to_dict_timestamps(self):
        """Test dictionary includes properly formatted timestamps"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )
        token.id = 1
        token.created_at = datetime.utcnow()
        token.updateLastUsed()

        # Act
        token_dict = token.toDict()

        # Assert
        assert token_dict['expires_at'] is not None
        assert token_dict['created_at'] is not None
        assert token_dict['last_used_at'] is not None
        # Check ISO format
        assert 'T' in token_dict['expires_at']

    def test_to_dict_none_timestamps(self):
        """Test dictionary handles None timestamps"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )
        token.id = 1
        token.created_at = None
        token.last_used_at = None

        # Act
        token_dict = token.toDict()

        # Assert
        assert token_dict['created_at'] is None
        assert token_dict['last_used_at'] is None

    def test_token_repr(self):
        """Test token string representation"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )
        token.id = 1

        # Act
        repr_str = repr(token)

        # Assert
        assert '1' in repr_str
        assert 'User 1' in repr_str or 'user_id=1' in repr_str.lower()

    def test_token_with_all_optional_fields(self):
        """Test token with all optional fields set"""
        # Act
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600,
            refresh_token='test_refresh_token',
            refresh_expires_in=2592000,
            token_type='Bearer',
            scope='read write',
            client_id='web-app',
            client_name='Web Application',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        # Assert
        assert token.token_type == 'Bearer'
        assert token.scope == 'read write'
        assert token.client_id == 'web-app'
        assert token.client_name == 'Web Application'
        assert token.ip_address == '192.168.1.1'
        assert token.user_agent == 'Mozilla/5.0'

    def test_multiple_revocations(self):
        """Test that multiple revocations update the timestamp"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )

        # Act
        token.revoke()
        first_revoked_at = token.revoked_at

        import time
        time.sleep(0.01)

        token.revoke()
        second_revoked_at = token.revoked_at

        # Assert
        assert token.is_revoked is True
        assert second_revoked_at >= first_revoked_at

    def test_multiple_last_used_updates(self):
        """Test that multiple last_used updates change the timestamp"""
        # Arrange
        token = OAuthToken(
            user_id=1,
            access_token='test_access_token',
            expires_in=3600
        )

        # Act
        token.updateLastUsed()
        first_used_at = token.last_used_at

        import time
        time.sleep(0.01)

        token.updateLastUsed()
        second_used_at = token.last_used_at

        # Assert
        assert second_used_at >= first_used_at
