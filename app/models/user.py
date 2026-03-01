"""
User Model
User data model
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import enum

from app.extensions import db


class UserRole(enum.Enum):
    """User Role Enumeration"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(enum.Enum):
    """User Status Enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(db.Model):
    """User Model"""
    __tablename__ = 'users'

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Basic information
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Personal information
    first_name: Mapped[Optional[str]] = mapped_column(String(50))
    last_name: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))

    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        nullable=False
    )

    # Status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    oauth_tokens: Mapped[List["OAuthToken"]] = relationship(
        "OAuthToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __init__(self, username: str, email: str, password: str, **kwargs):
        """
        Initialize user

        Args:
            username: Username
            email: Email address
            password: Password (plain text)
            **kwargs: Other fields
        """
        self.username = username
        self.email = email
        self.setPassword(password)

        # Set defaults for enums if not provided
        if 'role' not in kwargs:
            self.role = UserRole.USER
        if 'status' not in kwargs:
            self.status = UserStatus.ACTIVE
        if 'is_verified' not in kwargs:
            self.is_verified = False
        if 'is_active' not in kwargs:
            self.is_active = True

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def setPassword(self, password: str) -> None:
        """
        Set password (encrypted storage)

        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)

    def checkPassword(self, password: str) -> bool:
        """
        Verify password

        Args:
            password: Password to verify

        Returns:
            Whether the password is correct
        """
        return check_password_hash(self.password_hash, password)

    def updateLastLogin(self) -> None:
        """Update last login time"""
        self.last_login_at = datetime.now(timezone.utc)

    def toDict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary

        Args:
            include_sensitive: Whether to include sensitive information

        Returns:
            User information dictionary
        """
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'role': self.role.value,
            'status': self.status.value,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }

        if include_sensitive:
            data['password_hash'] = self.password_hash

        return data

    def toPublicDict(self) -> dict:
        """
        Convert to public API dictionary (simplified format)

        Returns:
            Public API user information dictionary
        """
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'avatar': self.avatar_url
        }

    def __repr__(self) -> str:
        return f'<User {self.username} ({self.email})>'
