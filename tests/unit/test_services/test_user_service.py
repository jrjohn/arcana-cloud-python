"""
User Service Unit Tests
User service unit tests
"""
import pytest
from unittest.mock import Mock, MagicMock

from app.services.implementations.user_service_impl import UserServiceImpl
from app.models.user import User, UserRole, UserStatus
from app.utils.exceptions import ValidationError, ConflictError, NotFoundError


class TestUserService:
    """User service test class"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock UserRepository"""
        return Mock()

    @pytest.fixture
    def user_service(self, mock_user_repository):
        """Create UserService instance"""
        return UserServiceImpl(mock_user_repository)

    def test_create_user_success(self, user_service, mock_user_repository):
        """Test successful user creation"""
        # Arrange
        mock_user_repository.existsByUsername.return_value = False
        mock_user_repository.existsByEmail.return_value = False

        mock_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        mock_user.id = 1
        mock_user_repository.create.return_value = mock_user

        # Act
        result = user_service.createUser(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Assert
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
        mock_user_repository.create.assert_called_once()

    def test_create_user_duplicate_username(self, user_service, mock_user_repository):
        """Test duplicate username creation failure"""
        # Arrange
        mock_user_repository.existsByUsername.return_value = True

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='test@example.com',
                password='TestPass123'
            )

        assert 'already exists' in str(exc_info.value)

    def test_create_user_invalid_email(self, user_service, mock_user_repository):
        """Test invalid email format"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='invalid-email',
                password='TestPass123'
            )

        assert 'email' in str(exc_info.value).lower()

    def test_create_user_weak_password(self, user_service, mock_user_repository):
        """Test weak password"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='test@example.com',
                password='weak'
            )

        assert 'password' in str(exc_info.value).lower()

    def test_get_user_by_id_success(self, user_service, mock_user_repository):
        """Test get user by ID"""
        # Arrange
        mock_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        mock_user.id = 1
        mock_user_repository.getById.return_value = mock_user

        # Act
        result = user_service.getUserById(1)

        # Assert
        assert result.id == 1
        assert result.username == 'testuser'

    def test_get_user_by_id_not_found(self, user_service, mock_user_repository):
        """Test user not found"""
        # Arrange
        mock_user_repository.getById.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.getUserById(999)

    def test_update_user_success(self, user_service, mock_user_repository):
        """Test update user"""
        # Arrange
        mock_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        mock_user.id = 1
        mock_user_repository.getById.return_value = mock_user
        mock_user_repository.update.return_value = mock_user

        # Act
        result = user_service.updateUser(
            1,
            first_name='John',
            last_name='Doe'
        )

        # Assert
        assert result.first_name == 'John'
        assert result.last_name == 'Doe'

    def test_change_password_success(self, user_service, mock_user_repository):
        """Test change password"""
        # Arrange
        mock_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        mock_user.id = 1
        mock_user_repository.getById.return_value = mock_user
        mock_user_repository.update.return_value = mock_user

        # Act
        result = user_service.changePassword(
            1,
            'TestPass123',
            'NewPass456'
        )

        # Assert
        assert result is True

    def test_delete_user_success(self, user_service, mock_user_repository):
        """Test delete user"""
        # Arrange
        mock_user_repository.delete.return_value = True

        # Act
        result = user_service.deleteUser(1)

        # Assert
        assert result is True
