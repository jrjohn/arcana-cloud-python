"""
User Repository Unit Tests
Comprehensive tests for UserRepositoryImpl
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
from app.models.User import User, UserRole, UserStatus
from app.utils.Exceptions import DatabaseError, NotFoundError


class TestUserRepository:
    """User Repository test class"""

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def user_repository(self, mock_session):
        """Create UserRepository instance"""
        return UserRepositoryImpl(mock_session)

    @pytest.fixture
    def sample_user(self):
        """Create sample user"""
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        user.id = 1
        return user

    def test_create_user_success(self, user_repository, mock_session, sample_user):
        """Test successful user creation"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Act
        result = user_repository.create(sample_user)

        # Assert
        assert result == sample_user
        mock_session.add.assert_called_once_with(sample_user)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_user)

    def test_create_user_database_error(self, user_repository, mock_session, sample_user):
        """Test user creation with database error"""
        # Arrange
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            user_repository.create(sample_user)

        assert "Failed to create user" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_create_user_integrity_error(self, user_repository, mock_session, sample_user):
        """Test user creation with integrity error (duplicate)"""
        # Arrange
        mock_session.commit.side_effect = IntegrityError("duplicate key", None, None)

        # Act & Assert
        with pytest.raises(DatabaseError):
            user_repository.create(sample_user)

        mock_session.rollback.assert_called_once()

    def test_get_by_id_success(self, user_repository, mock_session, sample_user):
        """Test get user by ID successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # Act
        result = user_repository.getById(1)

        # Assert
        assert result == sample_user
        mock_session.query.assert_called_once_with(User)

    def test_get_by_id_not_found(self, user_repository, mock_session):
        """Test get user by ID when user doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = user_repository.getById(999)

        # Assert
        assert result is None

    def test_get_by_id_database_error(self, user_repository, mock_session):
        """Test get user by ID with database error"""
        # Arrange
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            user_repository.getById(1)

        assert "Failed to get user by ID" in str(exc_info.value)

    def test_get_by_username_success(self, user_repository, mock_session, sample_user):
        """Test get user by username successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # Act
        result = user_repository.getByUsername('testuser')

        # Assert
        assert result == sample_user

    def test_get_by_username_not_found(self, user_repository, mock_session):
        """Test get user by username when not found"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = user_repository.getByUsername('nonexistent')

        # Assert
        assert result is None

    def test_get_by_email_success(self, user_repository, mock_session, sample_user):
        """Test get user by email successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # Act
        result = user_repository.getByEmail('test@example.com')

        # Assert
        assert result == sample_user

    def test_update_user_success(self, user_repository, mock_session, sample_user):
        """Test update user successfully"""
        # Arrange
        sample_user.first_name = 'Updated'
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Act
        result = user_repository.update(sample_user)

        # Assert
        assert result == sample_user
        assert result.first_name == 'Updated'
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_user)

    def test_update_user_database_error(self, user_repository, mock_session, sample_user):
        """Test update user with database error"""
        # Arrange
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            user_repository.update(sample_user)

        assert "Failed to update user" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_delete_user_success(self, user_repository, mock_session, sample_user):
        """Test delete user successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user
        mock_session.delete.return_value = None
        mock_session.commit.return_value = None

        # Act
        result = user_repository.delete(1)

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_user)
        mock_session.commit.assert_called_once()

    def test_delete_user_not_found(self, user_repository, mock_session):
        """Test delete user when user doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            user_repository.delete(999)

        assert "User with ID 999 not found" in str(exc_info.value)

    def test_delete_user_database_error(self, user_repository, mock_session, sample_user):
        """Test delete user with database error"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            user_repository.delete(1)

        assert "Failed to delete user" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_exists_by_username_true(self, user_repository, mock_session):
        """Test username exists check returns true"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.exists.return_value = True
        mock_query.scalar.return_value = True

        # Act
        result = user_repository.existsByUsername('testuser')

        # Assert
        assert result is True

    def test_exists_by_username_false(self, user_repository, mock_session):
        """Test username exists check returns false"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.exists.return_value = False
        mock_query.scalar.return_value = False

        # Act
        result = user_repository.existsByUsername('nonexistent')

        # Assert
        assert result is False

    def test_exists_by_email_true(self, user_repository, mock_session):
        """Test email exists check returns true"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.exists.return_value = True
        mock_query.scalar.return_value = True

        # Act
        result = user_repository.existsByEmail('test@example.com')

        # Assert
        assert result is True

    def test_exists_by_email_false(self, user_repository, mock_session):
        """Test email exists check returns false"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.exists.return_value = False
        mock_query.scalar.return_value = False

        # Act
        result = user_repository.existsByEmail('nonexistent@example.com')

        # Assert
        assert result is False

    def test_get_all_users_no_filters(self, user_repository, mock_session, sample_user):
        """Test get all users without filters"""
        # Arrange
        users = [sample_user]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = users

        # Act
        result_users, total = user_repository.getAll(page=1, per_page=20)

        # Assert
        assert len(result_users) == 1
        assert result_users[0] == sample_user
        assert total == 1

    def test_get_all_users_with_role_filter(self, user_repository, mock_session, sample_user):
        """Test get all users with role filter"""
        # Arrange
        users = [sample_user]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = users

        # Act
        result_users, total = user_repository.getAll(
            page=1,
            per_page=20,
            role=UserRole.USER
        )

        # Assert
        assert len(result_users) == 1
        assert total == 1

    def test_get_all_users_with_status_filter(self, user_repository, mock_session, sample_user):
        """Test get all users with status filter"""
        # Arrange
        users = [sample_user]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = users

        # Act
        result_users, total = user_repository.getAll(
            page=1,
            per_page=20,
            status=UserStatus.ACTIVE
        )

        # Assert
        assert len(result_users) == 1
        assert total == 1

    def test_get_all_users_pagination(self, user_repository, mock_session, sample_user):
        """Test get all users with pagination"""
        # Arrange
        users = [sample_user]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = users

        # Act
        result_users, total = user_repository.getAll(page=2, per_page=10)

        # Assert
        assert total == 50
        mock_query.offset.assert_called_with(10)  # (page-1) * per_page
        mock_query.limit.assert_called_with(10)

    def test_get_all_users_database_error(self, user_repository, mock_session):
        """Test get all users with database error"""
        # Arrange
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            user_repository.getAll(page=1, per_page=20)

        assert "Failed to get all users" in str(exc_info.value)

    def test_count_users_success(self, user_repository, mock_session):
        """Test count users successfully"""
        # Arrange
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.scalar.return_value = 42

        # Act
        result = user_repository.count()

        # Assert
        assert result == 42

    def test_count_users_database_error(self, user_repository, mock_session):
        """Test count users with database error"""
        # Arrange
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            user_repository.count()

        assert "Failed to count users" in str(exc_info.value)
