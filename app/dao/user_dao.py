"""
User DAO - Database access operations for User entities.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, UserStatus


class UserDao:
    """Data Access Object for User database operations."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._session.query(User).filter(User.id == user_id).first()

    def find_by_username(self, username: str) -> Optional[User]:
        return self._session.query(User).filter(User.username == username).first()

    def find_by_email(self, email: str) -> Optional[User]:
        return self._session.query(User).filter(User.email == email).first()

    def find_all(self, role: Optional[UserRole] = None,
                 status: Optional[UserStatus] = None,
                 offset: int = 0, limit: int = 20) -> List[User]:
        q = self._session.query(User)
        if role:
            q = q.filter(User.role == role)
        if status:
            q = q.filter(User.status == status)
        return q.offset(offset).limit(limit).all()

    def count(self, role: Optional[UserRole] = None,
              status: Optional[UserStatus] = None) -> int:
        q = self._session.query(User)
        if role:
            q = q.filter(User.role == role)
        if status:
            q = q.filter(User.status == status)
        return q.count()

    def save(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def delete(self, user: User) -> None:
        self._session.delete(user)
        self._session.flush()
