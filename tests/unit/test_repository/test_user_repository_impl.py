"""
User Repository Impl Unit Tests
Tests for app/repository/impl/user_repository_impl.py (Repository wrapper layer)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from app.repository.impl.user_repository_impl import UserRepositoryImpl
from app.models.user import User, UserRole, UserStatus


class TestUserRepositoryImplSave:
    """Tests for the save() method"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    @pytest.fixture
    def new_user(self):
        u = User(username='new', email='new@example.com', password='Pass123!')
        u.id = None
        return u

    @pytest.fixture
    def existing_user(self):
        u = User(username='existing', email='existing@example.com', password='Pass123!')
        u.id = 42
        return u

    def test_save_new_user_calls_create(self, repo, mock_dao, new_user):
        """save() on a user with id=None delegates to dao.create"""
        mock_dao.create.return_value = new_user
        result = repo.save(new_user)
        mock_dao.create.assert_called_once_with(new_user)
        mock_dao.update.assert_not_called()
        assert result is new_user

    def test_save_existing_user_calls_update(self, repo, mock_dao, existing_user):
        """save() on a user with id set delegates to dao.update"""
        mock_dao.update.return_value = existing_user
        result = repo.save(existing_user)
        mock_dao.update.assert_called_once_with(existing_user)
        mock_dao.create.assert_not_called()
        assert result is existing_user


class TestUserRepositoryImplFindById:
    """Tests for find_by_id()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_find_by_id_found(self, repo, mock_dao):
        user = User(username='u', email='u@e.com', password='Pass123!')
        user.id = 5
        mock_dao.getById.return_value = user
        result = repo.find_by_id(5)
        mock_dao.getById.assert_called_once_with(5)
        assert result is user

    def test_find_by_id_not_found(self, repo, mock_dao):
        mock_dao.getById.return_value = None
        result = repo.find_by_id(999)
        assert result is None


class TestUserRepositoryImplFindAll:
    """Tests for find_all()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_find_all_returns_list(self, repo, mock_dao):
        users = [Mock(spec=User), Mock(spec=User)]
        mock_dao.getAll.return_value = (users, 2)
        result = repo.find_all()
        mock_dao.getAll.assert_called_once_with(page=1, per_page=100_000)
        assert result == users

    def test_find_all_empty(self, repo, mock_dao):
        mock_dao.getAll.return_value = ([], 0)
        result = repo.find_all()
        assert result == []


class TestUserRepositoryImplCount:
    """Tests for count()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_count_delegates_to_dao(self, repo, mock_dao):
        mock_dao.count.return_value = 7
        result = repo.count()
        mock_dao.count.assert_called_once()
        assert result == 7


class TestUserRepositoryImplDeleteById:
    """Tests for delete_by_id()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_delete_by_id_success(self, repo, mock_dao):
        mock_dao.delete.return_value = True
        result = repo.delete_by_id(1)
        mock_dao.delete.assert_called_once_with(1)
        assert result is True

    def test_delete_by_id_not_found(self, repo, mock_dao):
        mock_dao.delete.return_value = False
        result = repo.delete_by_id(999)
        assert result is False


class TestUserRepositoryImplExistsById:
    """Tests for exists_by_id()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_exists_by_id_true(self, repo, mock_dao):
        mock_dao.getById.return_value = Mock(spec=User)
        assert repo.exists_by_id(1) is True

    def test_exists_by_id_false(self, repo, mock_dao):
        mock_dao.getById.return_value = None
        assert repo.exists_by_id(999) is False


class TestUserRepositoryImplFindByUsername:
    """Tests for find_by_username()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_find_by_username_found(self, repo, mock_dao):
        user = Mock(spec=User)
        mock_dao.getByUsername.return_value = user
        result = repo.find_by_username('alice')
        mock_dao.getByUsername.assert_called_once_with('alice')
        assert result is user

    def test_find_by_username_not_found(self, repo, mock_dao):
        mock_dao.getByUsername.return_value = None
        result = repo.find_by_username('ghost')
        assert result is None


class TestUserRepositoryImplFindByEmail:
    """Tests for find_by_email()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_find_by_email_found(self, repo, mock_dao):
        user = Mock(spec=User)
        mock_dao.getByEmail.return_value = user
        result = repo.find_by_email('alice@example.com')
        mock_dao.getByEmail.assert_called_once_with('alice@example.com')
        assert result is user

    def test_find_by_email_not_found(self, repo, mock_dao):
        mock_dao.getByEmail.return_value = None
        result = repo.find_by_email('ghost@example.com')
        assert result is None


class TestUserRepositoryImplExistsByUsername:
    """Tests for exists_by_username()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_exists_by_username_true(self, repo, mock_dao):
        mock_dao.existsByUsername.return_value = True
        assert repo.exists_by_username('alice') is True

    def test_exists_by_username_false(self, repo, mock_dao):
        mock_dao.existsByUsername.return_value = False
        assert repo.exists_by_username('nobody') is False


class TestUserRepositoryImplExistsByEmail:
    """Tests for exists_by_email()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_exists_by_email_true(self, repo, mock_dao):
        mock_dao.existsByEmail.return_value = True
        assert repo.exists_by_email('alice@example.com') is True

    def test_exists_by_email_false(self, repo, mock_dao):
        mock_dao.existsByEmail.return_value = False
        assert repo.exists_by_email('ghost@example.com') is False


class TestUserRepositoryImplFindAllPaginated:
    """Tests for find_all_paginated()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_find_all_paginated_defaults(self, repo, mock_dao):
        users = [Mock(spec=User)]
        mock_dao.getAll.return_value = (users, 1)
        items, total = repo.find_all_paginated()
        mock_dao.getAll.assert_called_once_with(page=1, per_page=20, role=None, status=None)
        assert items == users
        assert total == 1

    def test_find_all_paginated_with_filters(self, repo, mock_dao):
        mock_dao.getAll.return_value = ([], 0)
        repo.find_all_paginated(page=2, per_page=10, role=UserRole.ADMIN, status=UserStatus.ACTIVE)
        mock_dao.getAll.assert_called_once_with(
            page=2, per_page=10, role=UserRole.ADMIN, status=UserStatus.ACTIVE
        )


class TestUserRepositoryImplUpdateStatus:
    """Tests for update_status()"""

    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return UserRepositoryImpl(mock_dao)

    def test_update_status_success(self, repo, mock_dao):
        user = Mock(spec=User)
        user.status = UserStatus.ACTIVE
        mock_dao.getById.return_value = user
        updated_user = Mock(spec=User)
        mock_dao.update.return_value = updated_user

        result = repo.update_status(1, UserStatus.INACTIVE)
        assert user.status == UserStatus.INACTIVE
        mock_dao.update.assert_called_once_with(user)
        assert result is updated_user

    def test_update_status_user_not_found(self, repo, mock_dao):
        mock_dao.getById.return_value = None
        result = repo.update_status(999, UserStatus.INACTIVE)
        assert result is None
        mock_dao.update.assert_not_called()
