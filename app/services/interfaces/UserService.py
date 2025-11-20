"""
User Service Interface
User Service interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.models.user import User, UserRole, UserStatus


class UserService(ABC):
    """User Service interface"""

    @abstractmethod
    def createUser(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> User:
        """
        Create user

        Args:
            username: Username
            email: Email
            password: Password
            **kwargs: Other fields

        Returns:
            Created user

        Raises:
            ConflictError: Username或Email已存在
            ValidationError: Validation failed
        """
        pass

    @abstractmethod
    def getUserById(self, user_id: int) -> User:
        """
        根據 ID Get user

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            NotFoundError: User not found
        """
        pass

    @abstractmethod
    def getUserByUsername(self, username: str) -> User:
        """
        根據UsernameGet user

        Args:
            username: Username

        Returns:
            User object

        Raises:
            NotFoundError: User not found
        """
        pass

    @abstractmethod
    def getUserByEmail(self, email: str) -> User:
        """
        根據EmailGet user

        Args:
            email: Email

        Returns:
            User object

        Raises:
            NotFoundError: User not found
        """
        pass

    @abstractmethod
    def updateUser(self, user_id: int, **kwargs) -> User:
        """
        Update user信息

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated user

        Raises:
            NotFoundError: User not found
            ValidationError: Validation failed
        """
        pass

    @abstractmethod
    def deleteUser(self, user_id: int) -> bool:
        """
        Delete user

        Args:
            user_id: User ID

        Returns:
            Whether deletion successful

        Raises:
            NotFoundError: User not found
        """
        pass

    @abstractmethod
    def changePassword(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改Password

        Args:
            user_id: User ID
            old_password: 舊Password
            new_password: 新Password

        Returns:
            Whether modification successful

        Raises:
            NotFoundError: User not found
            AuthenticationError: 舊Password錯誤
            ValidationError: 新PasswordValidation failed
        """
        pass

    @abstractmethod
    def verifyUser(self, user_id: int) -> User:
        """
        Verify user

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            NotFoundError: User not found
        """
        pass

    @abstractmethod
    def updateUserStatus(self, user_id: int, status: UserStatus) -> User:
        """
        Update user狀態

        Args:
            user_id: User ID
            status: New status

        Returns:
            User object

        Raises:
            NotFoundError: User not found
        """
        pass

    @abstractmethod
    def getUsers(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> Dict[str, Any]:
        """
        Get user列表（分頁）

        Args:
            page: Page number
            per_page: Items per page
            role: Role filter
            status: Status filter

        Returns:
            包含User list和分頁信息的字典
        """
        pass
