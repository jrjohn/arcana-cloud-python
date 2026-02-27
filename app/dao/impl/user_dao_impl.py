"""
User DAO Implementation
Delegates all persistence operations to the injected UserRepository,
following the arcana-cloud-springboot UserDaoImpl pattern.
"""
from typing import Optional, List, Tuple

from app.dao.user_dao import UserDao
from app.models.user import User, UserRole, UserStatus
from app.repositories.interfaces.user_repository import UserRepository


class UserDaoImpl(UserDao):
    """
    Concrete User DAO.

    Wraps a UserRepository so that the Service layer is decoupled
    from persistence details.  Constructor injection is used so
    the dependency can be replaced easily (e.g. in tests).
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize with a UserRepository instance.

        Args:
            user_repository: Underlying repository to delegate to
        """
        self._repository = user_repository

    # ------------------------------------------------------------------
    # BaseDao implementation
    # ------------------------------------------------------------------

    def save(self, entity: User) -> User:
        """Create or update a user."""
        if entity.id is None:
            return self._repository.create(entity)
        return self._repository.update(entity)

    def find_by_id(self, id: int) -> Optional[User]:
        """Find a user by primary key."""
        return self._repository.getById(id)

    def find_all(self) -> List[User]:
        """Return all users (un-paginated, page 1 with a large limit)."""
        users, _ = self._repository.getAll(page=1, per_page=100_000)
        return users

    def count(self) -> int:
        """Return total user count."""
        return self._repository.count()

    def delete_by_id(self, id: int) -> bool:
        """Delete a user by primary key."""
        return self._repository.delete(id)

    def exists_by_id(self, id: int) -> bool:
        """Check whether a user with the given ID exists."""
        return self._repository.getById(id) is not None

    # ------------------------------------------------------------------
    # UserDao-specific methods
    # ------------------------------------------------------------------

    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        return self._repository.getByUsername(username)

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        return self._repository.getByEmail(email)

    def exists_by_username(self, username: str) -> bool:
        """Check whether a username is already taken."""
        return self._repository.existsByUsername(username)

    def exists_by_email(self, email: str) -> bool:
        """Check whether an email is already registered."""
        return self._repository.existsByEmail(email)

    def find_all_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
    ) -> Tuple[List[User], int]:
        """Retrieve users with pagination and optional filters."""
        return self._repository.getAll(
            page=page,
            per_page=per_page,
            role=role,
            status=status,
        )

    def update_status(self, user_id: int, status: UserStatus) -> Optional[User]:
        """Update a user's status field."""
        user = self._repository.getById(user_id)
        if user is None:
            return None
        user.status = status
        return self._repository.update(user)
