"""
OAuth Token Model
OAuth token model
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.Extensions import db


class OAuthToken(db.Model):
    """OAuth Token Model"""
    __tablename__ = 'oauth_tokens'

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # User association
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Token information
    access_token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), unique=True, index=True)
    token_type: Mapped[str] = mapped_column(String(20), default='Bearer', nullable=False)

    # Token scope and permissions
    scope: Mapped[Optional[str]] = mapped_column(String(255))

    # Expiration times
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    refresh_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Token status
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Client information
    client_id: Mapped[Optional[str]] = mapped_column(String(100))
    client_name: Mapped[Optional[str]] = mapped_column(String(100))

    # IP and User Agent
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_tokens")

    def __init__(
        self,
        user_id: int,
        access_token: str,
        expires_in: int = 3600,
        refresh_token: Optional[str] = None,
        refresh_expires_in: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize OAuth Token

        Args:
            user_id: User ID
            access_token: Access token
            expires_in: Access token validity period (seconds)
            refresh_token: Refresh token
            refresh_expires_in: Refresh token validity period (seconds)
            **kwargs: Other fields
        """
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token

        # Set defaults
        if 'token_type' not in kwargs:
            self.token_type = 'Bearer'
        if 'is_revoked' not in kwargs:
            self.is_revoked = False

        # Set expiration times
        self.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        if refresh_token and refresh_expires_in:
            self.refresh_expires_at = datetime.utcnow() + timedelta(seconds=refresh_expires_in)

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def isExpired(self) -> bool:
        """
        Check if access token is expired

        Returns:
            Whether expired
        """
        return datetime.utcnow() >= self.expires_at

    def isRefreshExpired(self) -> bool:
        """
        Check if refresh token is expired

        Returns:
            Whether expired
        """
        if not self.refresh_expires_at:
            return True
        return datetime.utcnow() >= self.refresh_expires_at

    def isValid(self) -> bool:
        """
        Check if token is valid

        Returns:
            Whether valid (not expired and not revoked)
        """
        return not self.isExpired() and not self.is_revoked

    def revoke(self) -> None:
        """Revoke token"""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

    def updateLastUsed(self) -> None:
        """Update last used time"""
        self.last_used_at = datetime.utcnow()

    def toDict(self, include_tokens: bool = False) -> dict:
        """
        Convert to dictionary

        Args:
            include_tokens: Whether to include token values

        Returns:
            Token information dictionary
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'token_type': self.token_type,
            'scope': self.scope,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_revoked': self.is_revoked,
            'client_id': self.client_id,
            'client_name': self.client_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }

        if include_tokens:
            data['access_token'] = self.access_token
            data['refresh_token'] = self.refresh_token
            data['refresh_expires_at'] = self.refresh_expires_at.isoformat() if self.refresh_expires_at else None

        return data

    def __repr__(self) -> str:
        return f'<OAuthToken {self.id} for User {self.user_id}>'
