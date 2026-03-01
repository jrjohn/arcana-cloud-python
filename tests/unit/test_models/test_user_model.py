"""
User Model Unit Tests
Comprehensive tests for User model
"""
import pytest
from datetime import datetime, timezone

from app.models.user import User, UserRole, UserStatus


class TestUserModel:
    """User Model test class"""

    def test_user_creation(self):
        """Test user creation with basic fields"""
        # Act
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Assert
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash is not None
        assert user.password_hash != 'TestPass123'  # Should be hashed
        assert user.role == UserRole.USER  # Default role
        assert user.status == UserStatus.ACTIVE  # Default status
        assert user.is_verified is False  # Default
        assert user.is_active is True  # Default

    def test_user_creation_with_kwargs(self):
        """Test user creation with additional kwargs"""
        # Act
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='User',
            phone='+1234567890',
            role=UserRole.ADMIN
        )

        # Assert
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.phone == '+1234567890'
        assert user.role == UserRole.ADMIN

    def test_set_password(self):
        """Test password hashing"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='InitialPass123'
        )
        initial_hash = user.password_hash

        # Act
        user.setPassword('NewPass456')

        # Assert
        assert user.password_hash != initial_hash
        assert user.password_hash != 'NewPass456'

    def test_check_password_correct(self):
        """Test password verification with correct password"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Act
        result = user.checkPassword('TestPass123')

        # Assert
        assert result is True

    def test_check_password_incorrect(self):
        """Test password verification with incorrect password"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Act
        result = user.checkPassword('WrongPassword')

        # Assert
        assert result is False

    def test_update_last_login(self):
        """Test updating last login timestamp"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        assert user.last_login_at is None

        # Act
        before_update = datetime.now(timezone.utc)
        user.updateLastLogin()
        after_update = datetime.now(timezone.utc)

        # Assert
        assert user.last_login_at is not None
        assert before_update <= user.last_login_at <= after_update

    def test_to_dict_basic(self):
        """Test converting user to dictionary without sensitive data"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        user.id = 1
        user.first_name = 'Test'
        user.last_name = 'User'

        # Act
        user_dict = user.toDict()

        # Assert
        assert user_dict['id'] == 1
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['first_name'] == 'Test'
        assert user_dict['last_name'] == 'User'
        assert user_dict['role'] == 'user'
        assert user_dict['status'] == 'active'
        assert user_dict['is_verified'] is False
        assert user_dict['is_active'] is True
        assert 'password_hash' not in user_dict

    def test_to_dict_with_sensitive(self):
        """Test converting user to dictionary with sensitive data"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        user.id = 1

        # Act
        user_dict = user.toDict(include_sensitive=True)

        # Assert
        assert 'password_hash' in user_dict
        assert user_dict['password_hash'] is not None

    def test_to_dict_with_timestamps(self):
        """Test dictionary includes properly formatted timestamps"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        user.id = 1
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        user.updateLastLogin()

        # Act
        user_dict = user.toDict()

        # Assert
        assert user_dict['created_at'] is not None
        assert user_dict['updated_at'] is not None
        assert user_dict['last_login_at'] is not None
        # Check ISO format
        assert 'T' in user_dict['created_at']

    def test_to_dict_none_timestamps(self):
        """Test dictionary handles None timestamps properly"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        user.id = 1
        user.created_at = None
        user.updated_at = None
        user.last_login_at = None

        # Act
        user_dict = user.toDict()

        # Assert
        assert user_dict['created_at'] is None
        assert user_dict['updated_at'] is None
        assert user_dict['last_login_at'] is None

    def test_user_repr(self):
        """Test user string representation"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Act
        repr_str = repr(user)

        # Assert
        assert 'testuser' in repr_str
        assert 'test@example.com' in repr_str

    def test_user_role_enum(self):
        """Test user role enumeration"""
        # Assert
        assert UserRole.ADMIN.value == 'admin'
        assert UserRole.USER.value == 'user'
        assert UserRole.GUEST.value == 'guest'

    def test_user_status_enum(self):
        """Test user status enumeration"""
        # Assert
        assert UserStatus.ACTIVE.value == 'active'
        assert UserStatus.INACTIVE.value == 'inactive'
        assert UserStatus.SUSPENDED.value == 'suspended'
        assert UserStatus.DELETED.value == 'deleted'

    def test_user_with_all_roles(self):
        """Test user creation with all role types"""
        # Test each role
        for role in [UserRole.ADMIN, UserRole.USER, UserRole.GUEST]:
            user = User(
                username=f'user_{role.value}',
                email=f'{role.value}@example.com',
                password='TestPass123',
                role=role
            )
            assert user.role == role

    def test_user_with_all_statuses(self):
        """Test user with all status types"""
        # Test each status
        for status in [UserStatus.ACTIVE, UserStatus.INACTIVE,
                      UserStatus.SUSPENDED, UserStatus.DELETED]:
            user = User(
                username='testuser',
                email='test@example.com',
                password='TestPass123'
            )
            user.status = status
            assert user.status == status

    def test_user_optional_fields(self):
        """Test user with all optional fields set"""
        # Act
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123',
            first_name='John',
            last_name='Doe',
            phone='+1234567890',
            avatar_url='https://example.com/avatar.jpg'
        )

        # Assert
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.phone == '+1234567890'
        assert user.avatar_url == 'https://example.com/avatar.jpg'

    def test_user_optional_fields_none(self):
        """Test user with optional fields as None"""
        # Act
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )

        # Assert
        assert user.first_name is None
        assert user.last_name is None
        assert user.phone is None
        assert user.avatar_url is None

    def test_password_not_stored_in_plain_text(self):
        """Test that password is never stored in plain text"""
        # Arrange
        password = 'SuperSecretPass123'
        user = User(
            username='testuser',
            email='test@example.com',
            password=password
        )

        # Assert
        assert user.password_hash != password
        assert password not in user.password_hash
        # Password hash should be significantly different length
        assert len(user.password_hash) > len(password)

    def test_multiple_password_changes(self):
        """Test multiple password changes produce different hashes"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='Password1'
        )
        hash1 = user.password_hash

        # Act
        user.setPassword('Password2')
        hash2 = user.password_hash

        user.setPassword('Password3')
        hash3 = user.password_hash

        # Assert
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3

    def test_user_verification_toggle(self):
        """Test toggling user verification status"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        assert user.is_verified is False

        # Act
        user.is_verified = True

        # Assert
        assert user.is_verified is True

    def test_user_active_toggle(self):
        """Test toggling user active status"""
        # Arrange
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        assert user.is_active is True

        # Act
        user.is_active = False

        # Assert
        assert user.is_active is False
