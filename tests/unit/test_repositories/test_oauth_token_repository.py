"""
OAuth Token Repository Unit Tests
Comprehensive tests for OAuthTokenRepositoryImpl
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.impl.oauth_token_repository_impl import OAuthTokenRepositoryImpl
from app.models.oauth_token import OAuthToken
from app.utils.exceptions import DatabaseError, NotFoundError


class TestOAuthTokenRepository:
    """OAuth Token Repository test class"""

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def token_repository(self, mock_session):
        """Create OAuthTokenRepository instance"""
        return OAuthTokenRepositoryImpl(mock_session)

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

    def test_create_token_success(self, token_repository, mock_session, sample_token):
        """Test successful token creation"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Act
        result = token_repository.create(sample_token)

        # Assert
        assert result == sample_token
        mock_session.add.assert_called_once_with(sample_token)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_token)

    def test_create_token_database_error(self, token_repository, mock_session, sample_token):
        """Test token creation with database error"""
        # Arrange
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.create(sample_token)

        assert "Failed to create token" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_get_by_access_token_success(self, token_repository, mock_session, sample_token):
        """Test get token by access token successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_token

        # Act
        result = token_repository.getByAccessToken('test_access_token')

        # Assert
        assert result == sample_token

    def test_get_by_access_token_not_found(self, token_repository, mock_session):
        """Test get token by access token when not found"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = token_repository.getByAccessToken('nonexistent_token')

        # Assert
        assert result is None

    def test_get_by_access_token_database_error(self, token_repository, mock_session):
        """Test get token by access token with database error"""
        # Arrange
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.getByAccessToken('test_token')

        assert "Failed to get token by access token" in str(exc_info.value)

    def test_get_by_refresh_token_success(self, token_repository, mock_session, sample_token):
        """Test get token by refresh token successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_token

        # Act
        result = token_repository.getByRefreshToken('test_refresh_token')

        # Assert
        assert result == sample_token

    def test_get_by_refresh_token_not_found(self, token_repository, mock_session):
        """Test get token by refresh token when not found"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = token_repository.getByRefreshToken('nonexistent_token')

        # Assert
        assert result is None

    def test_get_by_user_id_exclude_revoked(self, token_repository, mock_session, sample_token):
        """Test get tokens by user ID excluding revoked"""
        # Arrange
        tokens = [sample_token]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tokens

        # Act
        result = token_repository.getByUserId(1, include_revoked=False)

        # Assert
        assert len(result) == 1
        assert result[0] == sample_token

    def test_get_by_user_id_include_revoked(self, token_repository, mock_session, sample_token):
        """Test get tokens by user ID including revoked"""
        # Arrange
        tokens = [sample_token]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tokens

        # Act
        result = token_repository.getByUserId(1, include_revoked=True)

        # Assert
        assert len(result) == 1

    def test_get_by_user_id_database_error(self, token_repository, mock_session):
        """Test get tokens by user ID with database error"""
        # Arrange
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.getByUserId(1)

        assert "Failed to get tokens by user ID" in str(exc_info.value)

    def test_update_token_success(self, token_repository, mock_session, sample_token):
        """Test update token successfully"""
        # Arrange
        sample_token.access_token = 'new_access_token'
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Act
        result = token_repository.update(sample_token)

        # Assert
        assert result == sample_token
        assert result.access_token == 'new_access_token'
        mock_session.commit.assert_called_once()

    def test_update_token_database_error(self, token_repository, mock_session, sample_token):
        """Test update token with database error"""
        # Arrange
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.update(sample_token)

        assert "Failed to update token" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_revoke_token_success(self, token_repository, mock_session, sample_token):
        """Test revoke token successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_token
        mock_session.commit.return_value = None

        # Act
        result = token_repository.revoke(1)

        # Assert
        assert result is True
        assert sample_token.is_revoked is True
        mock_session.commit.assert_called_once()

    def test_revoke_token_not_found(self, token_repository, mock_session):
        """Test revoke token when token doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            token_repository.revoke(999)

        assert "Token with ID 999 not found" in str(exc_info.value)

    def test_revoke_token_database_error(self, token_repository, mock_session, sample_token):
        """Test revoke token with database error"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_token
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.revoke(1)

        assert "Failed to revoke token" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_revoke_all_by_user_id_success(self, token_repository, mock_session, sample_token):
        """Test revoke all tokens for user successfully"""
        # Arrange
        token2 = OAuthToken(
            user_id=1,
            access_token='token2',
            refresh_token='refresh2',
            expires_in=3600
        )
        tokens = [sample_token, token2]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tokens
        mock_session.commit.return_value = None

        # Act
        result = token_repository.revokeAllByUserId(1)

        # Assert
        assert result == 2
        assert sample_token.is_revoked is True
        assert token2.is_revoked is True
        mock_session.commit.assert_called_once()

    def test_revoke_all_by_user_id_no_tokens(self, token_repository, mock_session):
        """Test revoke all tokens when user has no tokens"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_session.commit.return_value = None

        # Act
        result = token_repository.revokeAllByUserId(1)

        # Assert
        assert result == 0

    def test_revoke_all_by_user_id_database_error(self, token_repository, mock_session, sample_token):
        """Test revoke all tokens with database error"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_token]
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.revokeAllByUserId(1)

        assert "Failed to revoke all tokens" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_delete_expired_success(self, token_repository, mock_session):
        """Test delete expired tokens successfully"""
        # Arrange
        expired_token1 = OAuthToken(
            user_id=1,
            access_token='expired1',
            expires_in=-3600  # Expired
        )
        expired_token2 = OAuthToken(
            user_id=1,
            access_token='expired2',
            expires_in=-7200  # Expired
        )
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [expired_token1, expired_token2]
        mock_session.commit.return_value = None

        # Act
        result = token_repository.deleteExpired()

        # Assert
        assert result == 2
        assert mock_session.delete.call_count == 2
        mock_session.commit.assert_called_once()

    def test_delete_expired_with_custom_date(self, token_repository, mock_session):
        """Test delete expired tokens with custom before_date"""
        # Arrange
        before_date = datetime.utcnow() - timedelta(days=7)
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_session.commit.return_value = None

        # Act
        result = token_repository.deleteExpired(before_date=before_date)

        # Assert
        assert result == 0

    def test_delete_expired_database_error(self, token_repository, mock_session):
        """Test delete expired tokens with database error"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.deleteExpired()

        assert "Failed to delete expired tokens" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_exists_by_access_token_true(self, token_repository, mock_session):
        """Test access token exists check returns true"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.exists.return_value = True
        mock_query.scalar.return_value = True

        # Act
        result = token_repository.existsByAccessToken('test_token')

        # Assert
        assert result is True

    def test_exists_by_access_token_false(self, token_repository, mock_session):
        """Test access token exists check returns false"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.exists.return_value = False
        mock_query.scalar.return_value = False

        # Act
        result = token_repository.existsByAccessToken('nonexistent_token')

        # Assert
        assert result is False

    def test_exists_by_access_token_database_error(self, token_repository, mock_session):
        """Test access token exists check with database error"""
        # Arrange
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            token_repository.existsByAccessToken('test_token')

        assert "Failed to check access token existence" in str(exc_info.value)
