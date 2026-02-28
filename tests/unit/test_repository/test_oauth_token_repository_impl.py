"""
OAuthToken Repository Impl Unit Tests
Tests for app/repository/impl/oauth_token_repository_impl.py
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from app.repository.impl.oauth_token_repository_impl import OAuthTokenRepositoryImpl
from app.models.oauth_token import OAuthToken


def _make_token(tid=1, uid=1, access_token='acc', refresh_token='ref'):
    """Helper: create a minimal OAuthToken mock."""
    t = Mock(spec=OAuthToken)
    t.id = tid
    t.user_id = uid
    t.access_token = access_token
    t.refresh_token = refresh_token
    t.is_revoked = False
    return t


class TestOAuthTokenRepositoryImplSave:
    """Tests for save()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_save_new_token_calls_create(self, repo, mock_dao):
        token = Mock(spec=OAuthToken)
        token.id = None
        mock_dao.create.return_value = token
        result = repo.save(token)
        mock_dao.create.assert_called_once_with(token)
        assert result is token

    def test_save_existing_token_calls_update(self, repo, mock_dao):
        token = Mock(spec=OAuthToken)
        token.id = 10
        mock_dao.update.return_value = token
        result = repo.save(token)
        mock_dao.update.assert_called_once_with(token)
        assert result is token


class TestOAuthTokenRepositoryImplFindById:
    """Tests for find_by_id()"""

    @pytest.fixture
    def mock_dao(self):
        d = Mock()
        # Simulate 'session' attribute
        d.session = Mock()
        return d

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_find_by_id_with_session(self, repo, mock_dao):
        token = _make_token()
        mock_dao.session.get.return_value = token
        result = repo.find_by_id(1)
        mock_dao.session.get.assert_called_once_with(OAuthToken, 1)
        assert result is token

    def test_find_by_id_no_session(self):
        dao = Mock(spec=[])  # dao without 'session'
        repo = OAuthTokenRepositoryImpl(dao)
        result = repo.find_by_id(1)
        assert result is None

    def test_find_by_id_not_found(self, repo, mock_dao):
        mock_dao.session.get.return_value = None
        result = repo.find_by_id(999)
        assert result is None


class TestOAuthTokenRepositoryImplFindAll:
    """Tests for find_all()"""

    @pytest.fixture
    def mock_dao(self):
        d = Mock()
        d.session = Mock()
        return d

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_find_all_with_session(self, repo, mock_dao):
        tokens = [_make_token(), _make_token(tid=2)]
        mock_dao.session.query.return_value.all.return_value = tokens
        result = repo.find_all()
        assert result == tokens

    def test_find_all_no_session(self):
        dao = Mock(spec=[])
        repo = OAuthTokenRepositoryImpl(dao)
        result = repo.find_all()
        assert result == []


class TestOAuthTokenRepositoryImplCount:
    """Tests for count()"""

    @pytest.fixture
    def mock_dao(self):
        d = Mock()
        d.session = Mock()
        return d

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_count_with_session(self, repo, mock_dao):
        mock_dao.session.query.return_value.scalar.return_value = 5
        result = repo.count()
        assert result == 5

    def test_count_no_session(self):
        dao = Mock(spec=[])
        repo = OAuthTokenRepositoryImpl(dao)
        result = repo.count()
        assert result == 0

    def test_count_none_scalar(self, repo, mock_dao):
        mock_dao.session.query.return_value.scalar.return_value = None
        result = repo.count()
        assert result == 0


class TestOAuthTokenRepositoryImplDeleteById:
    """Tests for delete_by_id()"""

    @pytest.fixture
    def mock_dao(self):
        d = Mock()
        d.session = Mock()
        return d

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_delete_by_id_found(self, repo, mock_dao):
        token = _make_token()
        mock_dao.session.get.return_value = token
        result = repo.delete_by_id(1)
        mock_dao.session.delete.assert_called_once_with(token)
        mock_dao.session.commit.assert_called_once()
        assert result is True

    def test_delete_by_id_not_found(self, repo, mock_dao):
        mock_dao.session.get.return_value = None
        result = repo.delete_by_id(999)
        assert result is False

    def test_delete_by_id_no_session(self):
        dao = Mock(spec=[])
        repo = OAuthTokenRepositoryImpl(dao)
        result = repo.delete_by_id(1)
        assert result is False


class TestOAuthTokenRepositoryImplExistsById:
    """Tests for exists_by_id()"""

    @pytest.fixture
    def mock_dao(self):
        d = Mock()
        d.session = Mock()
        return d

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_exists_by_id_true(self, repo, mock_dao):
        mock_dao.session.get.return_value = _make_token()
        assert repo.exists_by_id(1) is True

    def test_exists_by_id_false(self, repo, mock_dao):
        mock_dao.session.get.return_value = None
        assert repo.exists_by_id(999) is False


class TestOAuthTokenRepositoryImplSpecificMethods:
    """Tests for OAuthToken-specific methods"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return OAuthTokenRepositoryImpl(mock_dao)

    def test_find_by_access_token(self, repo, mock_dao):
        token = _make_token()
        mock_dao.getByAccessToken.return_value = token
        result = repo.find_by_access_token('my-access-token')
        mock_dao.getByAccessToken.assert_called_once_with('my-access-token')
        assert result is token

    def test_find_by_refresh_token(self, repo, mock_dao):
        token = _make_token()
        mock_dao.getByRefreshToken.return_value = token
        result = repo.find_by_refresh_token('my-refresh-token')
        mock_dao.getByRefreshToken.assert_called_once_with('my-refresh-token')
        assert result is token

    def test_find_by_access_token_not_found(self, repo, mock_dao):
        mock_dao.getByAccessToken.return_value = None
        result = repo.find_by_access_token('bad-token')
        assert result is None

    def test_find_all_by_user_id_default(self, repo, mock_dao):
        tokens = [_make_token(), _make_token(tid=2)]
        mock_dao.getByUserId.return_value = tokens
        result = repo.find_all_by_user_id(1)
        mock_dao.getByUserId.assert_called_once_with(1, include_revoked=False)
        assert result == tokens

    def test_find_all_by_user_id_include_revoked(self, repo, mock_dao):
        mock_dao.getByUserId.return_value = []
        repo.find_all_by_user_id(1, include_revoked=True)
        mock_dao.getByUserId.assert_called_once_with(1, include_revoked=True)

    def test_exists_by_access_token_true(self, repo, mock_dao):
        mock_dao.existsByAccessToken.return_value = True
        assert repo.exists_by_access_token('tok') is True

    def test_exists_by_access_token_false(self, repo, mock_dao):
        mock_dao.existsByAccessToken.return_value = False
        assert repo.exists_by_access_token('bad') is False

    def test_revoke(self, repo, mock_dao):
        mock_dao.revoke.return_value = True
        result = repo.revoke(1)
        mock_dao.revoke.assert_called_once_with(1)
        assert result is True

    def test_revoke_not_found(self, repo, mock_dao):
        mock_dao.revoke.return_value = False
        result = repo.revoke(999)
        assert result is False

    def test_revoke_all_by_user_id(self, repo, mock_dao):
        mock_dao.revokeAllByUserId.return_value = 3
        result = repo.revoke_all_by_user_id(1)
        mock_dao.revokeAllByUserId.assert_called_once_with(1)
        assert result == 3

    def test_delete_expired_with_date(self, repo, mock_dao):
        cutoff = datetime(2024, 1, 1)
        mock_dao.deleteExpired.return_value = 5
        result = repo.delete_expired(cutoff)
        mock_dao.deleteExpired.assert_called_once_with(cutoff)
        assert result == 5

    def test_delete_expired_no_date(self, repo, mock_dao):
        mock_dao.deleteExpired.return_value = 2
        result = repo.delete_expired()
        mock_dao.deleteExpired.assert_called_once_with(None)
        assert result == 2
