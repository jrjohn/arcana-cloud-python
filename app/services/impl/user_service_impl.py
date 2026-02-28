"""
User Service Implementation
User Service implementation
"""
import re
from typing import Optional, List, Dict, Any

from app.models.user import User, UserRole, UserStatus
from app.repository.user_repository import UserRepository
from app.services.interfaces.user_service import UserService
from app.utils.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError
)


class UserServiceImpl(UserService):
    """User Service implementation"""

    def __init__(self, user_repository: UserRepository):
        """
        Initialize

        Args:
            user_repository: UserRepository abstraction (decouples Service from DAO)
        """
        self.user_dao = user_repository

    def _validate_email(self, email: str) -> None:
        """驗證Email格式"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError("Invalid email format")

    def _validate_password(self, password: str) -> None:
        """驗證Password強度"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit")

    def _validate_username(self, username: str) -> None:
        """Verify user名格式"""
        if len(username) < 3 or len(username) > 80:
            raise ValidationError("Username must be between 3 and 80 characters")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscores and hyphens")

    def createUser(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> User:
        """Create user"""
        # Validate input
        self._validate_username(username)
        self._validate_email(email)
        self._validate_password(password)

        # Check if username and email already exist
        if self.user_dao.exists_by_username(username):
            raise ConflictError(f"Username '{username}' already exists")

        if self.user_dao.exists_by_email(email):
            raise ConflictError(f"Email '{email}' already exists")

        # Create user
        user = User(username=username, email=email, password=password, **kwargs)
        return self.user_dao.save(user)

    def getUserById(self, user_id: int) -> User:
        """根據 ID Get user"""
        user = self.user_dao.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found", "User")
        return user

    def getUserByUsername(self, username: str) -> User:
        """根據UsernameGet user"""
        user = self.user_dao.find_by_username(username)
        if not user:
            raise NotFoundError(f"User with username '{username}' not found", "User")
        return user

    def getUserByEmail(self, email: str) -> User:
        """根據EmailGet user"""
        user = self.user_dao.find_by_email(email)
        if not user:
            raise NotFoundError(f"User with email '{email}' not found", "User")
        return user

    def updateUser(self, user_id: int, **kwargs) -> User:
        """Update user信息"""
        user = self.getUserById(user_id)

        # Validate fields to update
        if 'email' in kwargs:
            self._validate_email(kwargs['email'])
            if kwargs['email'] != user.email and self.user_dao.exists_by_email(kwargs['email']):
                raise ConflictError(f"Email '{kwargs['email']}' already exists")

        if 'username' in kwargs:
            self._validate_username(kwargs['username'])
            if kwargs['username'] != user.username and self.user_dao.exists_by_username(kwargs['username']):
                raise ConflictError(f"Username '{kwargs['username']}' already exists")

        # 不允許直接更新Password
        if 'password' in kwargs or 'password_hash' in kwargs:
            raise ValidationError("Use changePassword method to update password")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return self.user_dao.save(user)

    def deleteUser(self, user_id: int) -> bool:
        """Delete user"""
        # Check if user exists first - this will raise NotFoundError if not
        self.getUserById(user_id)
        return self.user_dao.delete_by_id(user_id)

    def changePassword(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改Password"""
        user = self.getUserById(user_id)

        # 驗證舊Password
        if not user.checkPassword(old_password):
            raise AuthenticationError("Old password is incorrect")

        # 驗證新Password
        self._validate_password(new_password)

        # 更新Password
        user.setPassword(new_password)
        self.user_dao.save(user)
        return True

    def verifyUser(self, user_id: int) -> User:
        """Verify user"""
        user = self.getUserById(user_id)
        user.is_verified = True
        return self.user_dao.save(user)

    def updateUserStatus(self, user_id: int, status: UserStatus) -> User:
        """Update user狀態"""
        updated = self.user_dao.update_status(user_id, status)
        if not updated:
            raise NotFoundError(f"User with ID {user_id} not found", "User")
        return updated

    def getUsers(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> Dict[str, Any]:
        """Get user列表（分頁）"""
        users, total = self.user_dao.find_all_paginated(
            page=page,
            per_page=per_page,
            role=role,
            status=status,
        )

        return {
            'items': [user.toDict() for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
