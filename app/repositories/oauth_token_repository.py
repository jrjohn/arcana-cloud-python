"""
OAuth Token Repository Interface
OAuth Token Repository interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from app.models.oauth_token import OAuthToken


class OAuthTokenRepository(ABC):
    """OAuth Token Repository interface"""

    @abstractmethod
    def create(self, token: OAuthToken) -> OAuthToken:
        """
        Create token

        Args:
            token: Token object

        Returns:
            Created token
        """
        pass

    @abstractmethod
    def getByAccessToken(self, access_token: str) -> Optional[OAuthToken]:
        """
        Get by access token

        Args:
            access_token: Access token

        Returns:
            Token object或 None
        """
        pass

    @abstractmethod
    def getByRefreshToken(self, refresh_token: str) -> Optional[OAuthToken]:
        """
        Get by refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            Token object或 None
        """
        pass

    @abstractmethod
    def getByUserId(self, user_id: int, include_revoked: bool = False) -> List[OAuthToken]:
        """
        Get all tokens by user ID

        Args:
            user_id: User ID
            include_revoked: Whether to include revoked tokens

        Returns:
            Token list
        """
        pass

    @abstractmethod
    def update(self, token: OAuthToken) -> OAuthToken:
        """
        Update token

        Args:
            token: Token object

        Returns:
            Updated token
        """
        pass

    @abstractmethod
    def revoke(self, token_id: int) -> bool:
        """
        Revoke token

        Args:
            token_id: Token ID

        Returns:
            Whether revocation successful
        """
        pass

    @abstractmethod
    def revokeAllByUserId(self, user_id: int) -> int:
        """
        Revoke all tokens for user

        Args:
            user_id: User ID

        Returns:
            Number of revoked tokens
        """
        pass

    @abstractmethod
    def deleteExpired(self, before_date: Optional[datetime] = None) -> int:
        """
        Delete expired tokens

        Args:
            before_date: Delete tokens expired before this date, defaults to current time

        Returns:
            Number of deleted tokens
        """
        pass

    @abstractmethod
    def existsByAccessToken(self, access_token: str) -> bool:
        """
        Check if access token exists

        Args:
            access_token: Access token

        Returns:
            Whether exists
        """
        pass
