"""
User DAO Interface
Extends BaseDao with User-specific query methods,
following the arcana-cloud-springboot UserDao pattern.
"""
from abc import abstractmethod
from typing import Optional, List, Tuple

from app.dao.base_dao import BaseDao
from app.models.user import User, UserRole, UserStatus


class UserDao(BaseDao[User, int]):
    """
    User DAO interface.

    Extends BaseDao with user-specific lookup and query operations.
    Implementations delegate to the underlying UserRepository.
    """

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by username.

        Args:
            username: Username to search for

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email address.

        Args:
            email: Email address to search for

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """
        Check whether a user with the given username exists.

        Args:
            username: Username to check

        Returns:
            True if username is taken, False otherwise
        """
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """
        Check whether a user with the given email exists.

        Args:
            email: Email address to check

        Returns:
            True if email is taken, False otherwise
        """
        pass

    @abstractmethod
    def find_all_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
    ) -> Tuple[List[User], int]:
        """
        Retrieve users with pagination and optional filters.

        Args:
            page: 1-based page number
            per_page: Page size
            role: Filter by user role (optional)
            status: Filter by user status (optional)

        Returns:
            Tuple of (user list, total count)
        """
        pass

    @abstractmethod
    def update_status(self, user_id: int, status: UserStatus) -> Optional[User]:
        """
        Update the status of a user identified by user_id.

        Args:
            user_id: ID of the user to update
            status: New status value

        Returns:
            Updated User if found, None otherwise
        """
        pass
