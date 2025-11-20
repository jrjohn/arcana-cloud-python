"""
User Repository Implementation
User Repository implementation
"""
from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus
from app.repositories.interfaces.UserRepository import UserRepository
from app.utils.Exceptions import DatabaseError, NotFoundError


class UserRepositoryImpl(UserRepository):
    """User Repository implementation"""

    def __init__(self, session: Session):
        """
        Initialize

        Args:
            session: Database session
        """
        self.session = session

    def create(self, user: User) -> User:
        """Create user"""
        try:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to create user: {str(e)}")

    def getById(self, user_id: int) -> Optional[User]:
        """根據 ID Get user"""
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get user by ID: {str(e)}")

    def getByUsername(self, username: str) -> Optional[User]:
        """根據UsernameGet user"""
        try:
            return self.session.query(User).filter(User.username == username).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get user by username: {str(e)}")

    def getByEmail(self, email: str) -> Optional[User]:
        """根據EmailGet user"""
        try:
            return self.session.query(User).filter(User.email == email).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get user by email: {str(e)}")

    def update(self, user: User) -> User:
        """Update user"""
        try:
            self.session.commit()
            self.session.refresh(user)
            return user
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to update user: {str(e)}")

    def delete(self, user_id: int) -> bool:
        """Delete user"""
        try:
            user = self.getById(user_id)
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found", "User")

            self.session.delete(user)
            self.session.commit()
            return True
        except NotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete user: {str(e)}")

    def existsByUsername(self, username: str) -> bool:
        """Check user名Whether exists"""
        try:
            return self.session.query(
                self.session.query(User).filter(User.username == username).exists()
            ).scalar()
        except Exception as e:
            raise DatabaseError(f"Failed to check username existence: {str(e)}")

    def existsByEmail(self, email: str) -> bool:
        """Check if email exists"""
        try:
            return self.session.query(
                self.session.query(User).filter(User.email == email).exists()
            ).scalar()
        except Exception as e:
            raise DatabaseError(f"Failed to check email existence: {str(e)}")

    def getAll(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> tuple[List[User], int]:
        """Get all users (paginated)"""
        try:
            query = self.session.query(User)

            # Apply filter conditions
            if role:
                query = query.filter(User.role == role)
            if status:
                query = query.filter(User.status == status)

            # 獲取Total count
            total = query.count()

            # Apply pagination
            offset = (page - 1) * per_page
            users = query.offset(offset).limit(per_page).all()

            return users, total
        except Exception as e:
            raise DatabaseError(f"Failed to get all users: {str(e)}")

    def count(self) -> int:
        """Get userTotal count"""
        try:
            return self.session.query(func.count(User.id)).scalar()
        except Exception as e:
            raise DatabaseError(f"Failed to count users: {str(e)}")
