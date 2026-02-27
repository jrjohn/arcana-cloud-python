"""
User Repository Implementation
Delegates all persistence operations to the injected UserDAO,
following the arcana-cloud-springboot UserRepositoryImpl pattern.
"""
from typing import Optional, List, Tuple

from app.repository.user_repository import UserRepository
from app.models.user import User, UserRole, UserStatus
# Import the underlying SQLAlchemy-based DAO (true DAO layer)
from app.repositories.interfaces.user_repository import UserRepository as UserDAO


class UserRepositoryImpl(UserRepository):
    """
    Concrete User Repository.

    Wraps a UserDAO so that the Service layer is decoupled
    from persistence details.  Constructor injection is used so
    the dependency can be replaced easily (e.g. in tests).
    """

    def __init__(self, user_dao: UserDAO):
        """
        Initialize with a UserDAO instance.

        Args:
            user_dao: Underlying DAO to delegate to
        """
        self._dao = user_dao

    # ------------------------------------------------------------------
    # BaseRepository implementation
    # ------------------------------------------------------------------

    def save(self, entity: User) -> User:
        """Create or update a user."""
        if entity.id is None:
            return self._dao.create(entity)
        return self._dao.update(entity)

    def find_by_id(self, id: int) -> Optional[User]:
        """Find a user by primary key."""
        return self._dao.getById(id)

    def find_all(self) -> List[User]:
        """Return all users (un-paginated, page 1 with a large limit)."""
        users, _ = self._dao.getAll(page=1, per_page=100_000)
        return users

    def count(self) -> int:
        """Return total user count."""
        return self._dao.count()

    def delete_by_id(self, id: int) -> bool:
        """Delete a user by primary key."""
        return self._dao.delete(id)

    def exists_by_id(self, id: int) -> bool:
        """Check whether a user with the given ID exists."""
        return self._dao.getById(id) is not None

    # ------------------------------------------------------------------
    # UserRepository-specific methods
    # ------------------------------------------------------------------

    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        return self._dao.getByUsername(username)

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        return self._dao.getByEmail(email)

    def exists_by_username(self, username: str) -> bool:
        """Check whether a username is already taken."""
        return self._dao.existsByUsername(username)

    def exists_by_email(self, email: str) -> bool:
        """Check whether an email is already registered."""
        return self._dao.existsByEmail(email)

    def find_all_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
    ) -> Tuple[List[User], int]:
        """Retrieve users with pagination and optional filters."""
        return self._dao.getAll(
            page=page,
            per_page=per_page,
            role=role,
            status=status,
        )

    def update_status(self, user_id: int, status: UserStatus) -> Optional[User]:
        """Update a user's status field."""
        user = self._dao.getById(user_id)
        if user is None:
            return None
        user.status = status
        return self._dao.update(user)
