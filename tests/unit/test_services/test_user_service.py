"""
User Service Unit Tests
User service unit tests
"""
import pytest
from unittest.mock import Mock, MagicMock

from app.services.implementations.user_service_impl import UserServiceImpl
from app.models.user import User, UserRole, UserStatus
from app.utils.exceptions import ValidationError, ConflictError, NotFoundError, AuthenticationError


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

    # ------------------------------------------------------------------ #
    # createUser                                                           #
    # ------------------------------------------------------------------ #

    def test_create_user_success(self, user_service, mock_user_repository):
        """Test successful user creation"""
        # Arrange — service calls exists_by_username / exists_by_email / save
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.exists_by_email.return_value = False

        mock_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        mock_user.id = 1
        mock_user_repository.save.return_value = mock_user

        # Act
        result = user_service.createUser(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Assert
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
        mock_user_repository.save.assert_called_once()

    def test_create_user_duplicate_username(self, user_service, mock_user_repository):
        """Test duplicate username creation failure"""
        # Arrange
        mock_user_repository.exists_by_username.return_value = True

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='test@example.com',
                password='TestPass123'
            )

        assert 'already exists' in str(exc_info.value)

    def test_create_user_duplicate_email(self, user_service, mock_user_repository):
        """Test duplicate email creation failure"""
        # Arrange
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.exists_by_email.return_value = True

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

    def test_create_user_invalid_username_too_short(self, user_service, mock_user_repository):
        """Test username too short"""
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='ab',
                email='test@example.com',
                password='TestPass123'
            )

        assert 'username' in str(exc_info.value).lower()

    def test_create_user_invalid_username_special_chars(self, user_service, mock_user_repository):
        """Test username with invalid special characters"""
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='test user!',
                email='test@example.com',
                password='TestPass123'
            )

        assert 'username' in str(exc_info.value).lower()

    def test_create_user_password_no_uppercase(self, user_service, mock_user_repository):
        """Test password without uppercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )

        assert 'password' in str(exc_info.value).lower()

    def test_create_user_password_no_lowercase(self, user_service, mock_user_repository):
        """Test password without lowercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='test@example.com',
                password='TESTPASS123'
            )

        assert 'password' in str(exc_info.value).lower()

    def test_create_user_password_no_digit(self, user_service, mock_user_repository):
        """Test password without digit"""
        with pytest.raises(ValidationError) as exc_info:
            user_service.createUser(
                username='testuser',
                email='test@example.com',
                password='TestPassword'
            )

        assert 'password' in str(exc_info.value).lower()

    # ------------------------------------------------------------------ #
    # getUserById                                                          #
    # ------------------------------------------------------------------ #

    def test_get_user_by_id_success(self, user_service, mock_user_repository):
        """Test get user by ID"""
        # Arrange — service calls find_by_id
        mock_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        mock_user.id = 1
        mock_user_repository.find_by_id.return_value = mock_user

        # Act
        result = user_service.getUserById(1)

        # Assert
        assert result.id == 1
        assert result.username == 'testuser'
        mock_user_repository.find_by_id.assert_called_once_with(1)

    def test_get_user_by_id_not_found(self, user_service, mock_user_repository):
        """Test user not found"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.getUserById(999)

    # ------------------------------------------------------------------ #
    # getUserByUsername                                                    #
    # ------------------------------------------------------------------ #

    def test_get_user_by_username_success(self, user_service, mock_user_repository, sample_user):
        """Test get user by username"""
        # Arrange — service calls find_by_username
        mock_user_repository.find_by_username.return_value = sample_user

        # Act
        result = user_service.getUserByUsername('testuser')

        # Assert
        assert result.username == 'testuser'
        mock_user_repository.find_by_username.assert_called_once_with('testuser')

    def test_get_user_by_username_not_found(self, user_service, mock_user_repository):
        """Test get user by username when user not found"""
        # Arrange
        mock_user_repository.find_by_username.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.getUserByUsername('unknown')

    # ------------------------------------------------------------------ #
    # getUserByEmail                                                       #
    # ------------------------------------------------------------------ #

    def test_get_user_by_email_success(self, user_service, mock_user_repository, sample_user):
        """Test get user by email"""
        # Arrange — service calls find_by_email
        mock_user_repository.find_by_email.return_value = sample_user

        # Act
        result = user_service.getUserByEmail('test@example.com')

        # Assert
        assert result.email == 'test@example.com'
        mock_user_repository.find_by_email.assert_called_once_with('test@example.com')

    def test_get_user_by_email_not_found(self, user_service, mock_user_repository):
        """Test get user by email when user not found"""
        # Arrange
        mock_user_repository.find_by_email.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.getUserByEmail('nobody@example.com')

    # ------------------------------------------------------------------ #
    # updateUser                                                           #
    # ------------------------------------------------------------------ #

    def test_update_user_success(self, user_service, mock_user_repository, sample_user):
        """Test update user basic info"""
        # Arrange — getUserById calls find_by_id; save stores result
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.save.return_value = sample_user

        # Act
        result = user_service.updateUser(
            1,
            first_name='John',
            last_name='Doe'
        )

        # Assert
        assert result.first_name == 'John'
        assert result.last_name == 'Doe'
        mock_user_repository.save.assert_called_once()

    def test_update_user_change_email_success(self, user_service, mock_user_repository, sample_user):
        """Test update user email when new email is available"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.save.return_value = sample_user

        # Act
        result = user_service.updateUser(1, email='new@example.com')

        # Assert
        mock_user_repository.exists_by_email.assert_called_once_with('new@example.com')
        mock_user_repository.save.assert_called_once()

    def test_update_user_change_email_conflict(self, user_service, mock_user_repository, sample_user):
        """Test update user email when new email already taken"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.exists_by_email.return_value = True

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            user_service.updateUser(1, email='taken@example.com')

        assert 'already exists' in str(exc_info.value)

    def test_update_user_change_email_same_email(self, user_service, mock_user_repository, sample_user):
        """Test update user email with the same email (no conflict check)"""
        # Arrange — setting same email should skip exists check
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.save.return_value = sample_user

        # Act
        result = user_service.updateUser(1, email='test@example.com')

        # Assert — exists_by_email should NOT be called when email is unchanged
        mock_user_repository.exists_by_email.assert_not_called()

    def test_update_user_change_username_success(self, user_service, mock_user_repository, sample_user):
        """Test update user username when new username is available"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.save.return_value = sample_user

        # Act
        result = user_service.updateUser(1, username='newname')

        # Assert
        mock_user_repository.exists_by_username.assert_called_once_with('newname')

    def test_update_user_change_username_conflict(self, user_service, mock_user_repository, sample_user):
        """Test update user username when new username already taken"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.exists_by_username.return_value = True

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            user_service.updateUser(1, username='takenname')

        assert 'already exists' in str(exc_info.value)

    def test_update_user_password_not_allowed(self, user_service, mock_user_repository, sample_user):
        """Test that direct password update is rejected"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            user_service.updateUser(1, password='NewPass123')

        assert 'changePassword' in str(exc_info.value)

    def test_update_user_password_hash_not_allowed(self, user_service, mock_user_repository, sample_user):
        """Test that direct password_hash update is rejected"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValidationError):
            user_service.updateUser(1, password_hash='somehash')

    def test_update_user_not_found(self, user_service, mock_user_repository):
        """Test update user when user not found"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.updateUser(999, first_name='Ghost')

    # ------------------------------------------------------------------ #
    # changePassword                                                       #
    # ------------------------------------------------------------------ #

    def test_change_password_success(self, user_service, mock_user_repository, sample_user):
        """Test change password"""
        # Arrange — service calls find_by_id then save
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.save.return_value = sample_user

        # Act
        result = user_service.changePassword(
            1,
            'TestPass123',
            'NewPass456'
        )

        # Assert
        assert result is True
        mock_user_repository.save.assert_called_once()

    def test_change_password_wrong_old_password(self, user_service, mock_user_repository, sample_user):
        """Test change password with wrong old password"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            user_service.changePassword(1, 'WrongOldPass', 'NewPass456')

        assert 'incorrect' in str(exc_info.value).lower()

    def test_change_password_weak_new_password(self, user_service, mock_user_repository, sample_user):
        """Test change password with weak new password"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            user_service.changePassword(1, 'TestPass123', 'weak')

        assert 'password' in str(exc_info.value).lower()

    def test_change_password_user_not_found(self, user_service, mock_user_repository):
        """Test change password when user not found"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.changePassword(999, 'TestPass123', 'NewPass456')

    # ------------------------------------------------------------------ #
    # deleteUser                                                           #
    # ------------------------------------------------------------------ #

    def test_delete_user_success(self, user_service, mock_user_repository, sample_user):
        """Test delete user"""
        # Arrange — deleteUser first calls getUserById (find_by_id) then delete_by_id
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.delete_by_id.return_value = True

        # Act
        result = user_service.deleteUser(1)

        # Assert
        assert result is True
        mock_user_repository.find_by_id.assert_called_once_with(1)
        mock_user_repository.delete_by_id.assert_called_once_with(1)

    def test_delete_user_not_found(self, user_service, mock_user_repository):
        """Test delete user when user not found raises NotFoundError"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.deleteUser(999)

    # ------------------------------------------------------------------ #
    # verifyUser                                                           #
    # ------------------------------------------------------------------ #

    def test_verify_user_success(self, user_service, mock_user_repository, sample_user):
        """Test verify user sets is_verified=True"""
        # Arrange
        sample_user.is_verified = False
        mock_user_repository.find_by_id.return_value = sample_user
        mock_user_repository.save.return_value = sample_user

        # Act
        result = user_service.verifyUser(1)

        # Assert
        assert result.is_verified is True
        mock_user_repository.save.assert_called_once()

    def test_verify_user_not_found(self, user_service, mock_user_repository):
        """Test verify user when user not found"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.verifyUser(999)

    # ------------------------------------------------------------------ #
    # updateUserStatus                                                     #
    # ------------------------------------------------------------------ #

    def test_update_user_status_success(self, user_service, mock_user_repository, sample_user):
        """Test update user status"""
        # Arrange — service calls update_status
        sample_user.status = UserStatus.SUSPENDED
        mock_user_repository.update_status.return_value = sample_user

        # Act
        result = user_service.updateUserStatus(1, UserStatus.SUSPENDED)

        # Assert
        assert result.status == UserStatus.SUSPENDED
        mock_user_repository.update_status.assert_called_once_with(1, UserStatus.SUSPENDED)

    def test_update_user_status_not_found(self, user_service, mock_user_repository):
        """Test update user status when user not found"""
        # Arrange — update_status returns None when user not found
        mock_user_repository.update_status.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.updateUserStatus(999, UserStatus.ACTIVE)

    # ------------------------------------------------------------------ #
    # getUsers (paginated)                                                 #
    # ------------------------------------------------------------------ #

    def test_get_users_success(self, user_service, mock_user_repository, sample_user):
        """Test get users with default pagination"""
        # Arrange — service calls find_all_paginated
        mock_user_repository.find_all_paginated.return_value = ([sample_user], 1)

        # Act
        result = user_service.getUsers()

        # Assert
        assert 'items' in result
        assert 'pagination' in result
        assert len(result['items']) == 1
        assert result['pagination']['page'] == 1
        assert result['pagination']['per_page'] == 20
        assert result['pagination']['total'] == 1
        mock_user_repository.find_all_paginated.assert_called_once_with(
            page=1,
            per_page=20,
            role=None,
            status=None,
        )

    def test_get_users_with_filters(self, user_service, mock_user_repository, sample_user):
        """Test get users with role and status filters"""
        # Arrange
        mock_user_repository.find_all_paginated.return_value = ([sample_user], 1)

        # Act
        result = user_service.getUsers(
            page=2,
            per_page=10,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )

        # Assert
        assert result['pagination']['page'] == 2
        assert result['pagination']['per_page'] == 10
        mock_user_repository.find_all_paginated.assert_called_once_with(
            page=2,
            per_page=10,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )

    def test_get_users_empty(self, user_service, mock_user_repository):
        """Test get users returns empty list"""
        # Arrange
        mock_user_repository.find_all_paginated.return_value = ([], 0)

        # Act
        result = user_service.getUsers()

        # Assert
        assert result['items'] == []
        assert result['pagination']['total'] == 0
        assert result['pagination']['pages'] == 0

    def test_get_users_pagination_pages_calculation(self, user_service, mock_user_repository, sample_user):
        """Test page count calculation with ceiling division"""
        # Arrange — 25 users, 10 per page → 3 pages
        users = [sample_user] * 25
        mock_user_repository.find_all_paginated.return_value = (users[:10], 25)

        # Act
        result = user_service.getUsers(page=1, per_page=10)

        # Assert
        assert result['pagination']['pages'] == 3
