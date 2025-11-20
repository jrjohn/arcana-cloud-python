"""
User Repository Interface
User Repository interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.models.user import User, UserRole, UserStatus


class UserRepository(ABC):
    """User Repository interface"""

    @abstractmethod
    def create(self, user: User) -> User:
        """
        Create user

        Args:
            user: User object

        Returns:
            Created user
        """
        pass

    @abstractmethod
    def getById(self, user_id: int) -> Optional[User]:
        """
        根據 ID Get user

        Args:
            user_id: User ID

        Returns:
            User object或 None
        """
        pass

    @abstractmethod
    def getByUsername(self, username: str) -> Optional[User]:
        """
        根據UsernameGet user

        Args:
            username: Username

        Returns:
            User object或 None
        """
        pass

    @abstractmethod
    def getByEmail(self, email: str) -> Optional[User]:
        """
        根據EmailGet user

        Args:
            email: Email

        Returns:
            User object或 None
        """
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """
        Update user

        Args:
            user: User object

        Returns:
            Updated user
        """
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """
        Delete user

        Args:
            user_id: User ID

        Returns:
            Whether deletion successful
        """
        pass

    @abstractmethod
    def existsByUsername(self, username: str) -> bool:
        """
        Check user名Whether exists

        Args:
            username: Username

        Returns:
            Whether exists
        """
        pass

    @abstractmethod
    def existsByEmail(self, email: str) -> bool:
        """
        Check if email exists

        Args:
            email: Email

        Returns:
            Whether exists
        """
        pass

    @abstractmethod
    def getAll(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> tuple[List[User], int]:
        """
        Get all users (paginated)

        Args:
            page: Page number
            per_page: Items per page
            role: Role filter
            status: Status filter

        Returns:
            (User list, Total count)
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get userTotal count

        Returns:
            Total count
        """
        pass
