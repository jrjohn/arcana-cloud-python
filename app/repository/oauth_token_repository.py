"""
OAuthToken Repository Interface
Extends BaseRepository with OAuth-token-specific query and revocation methods,
following the arcana-cloud-springboot OAuthTokenRepository pattern.
"""
from abc import abstractmethod
from typing import Optional, List
from datetime import datetime

from app.repository.base_repository import BaseRepository
from app.models.oauth_token import OAuthToken


class OAuthTokenRepository(BaseRepository[OAuthToken, int]):
    """
    OAuth Token Repository interface.

    Extends BaseRepository with token-specific lookup and lifecycle operations.
    Implementations delegate to the underlying OAuthTokenDAO.
    """

    @abstractmethod
    def find_by_access_token(self, access_token: str) -> Optional[OAuthToken]:
        """
        Find a token record by its access token string.

        Args:
            access_token: JWT access token string

        Returns:
            OAuthToken if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_refresh_token(self, refresh_token: str) -> Optional[OAuthToken]:
        """
        Find a token record by its refresh token string.

        Args:
            refresh_token: JWT refresh token string

        Returns:
            OAuthToken if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all_by_user_id(
        self, user_id: int, include_revoked: bool = False
    ) -> List[OAuthToken]:
        """
        Retrieve all tokens belonging to a user.

        Args:
            user_id: Owner user ID
            include_revoked: When False (default) only active tokens are returned

        Returns:
            List of matching OAuthToken records
        """
        pass

    @abstractmethod
    def exists_by_access_token(self, access_token: str) -> bool:
        """
        Check whether an access token exists in the store.

        Args:
            access_token: JWT access token string

        Returns:
            True if the token exists, False otherwise
        """
        pass

    @abstractmethod
    def revoke(self, token_id: int) -> bool:
        """
        Revoke a single token by its ID.

        Args:
            token_id: Primary key of the token to revoke

        Returns:
            True if revoked successfully, False if not found
        """
        pass

    @abstractmethod
    def revoke_all_by_user_id(self, user_id: int) -> int:
        """
        Revoke every active token owned by a user.

        Args:
            user_id: Owner user ID

        Returns:
            Number of tokens revoked
        """
        pass

    @abstractmethod
    def delete_expired(self, before_date: Optional[datetime] = None) -> int:
        """
        Delete tokens that expired before the given date.

        Args:
            before_date: Cutoff datetime (defaults to utcnow())

        Returns:
            Number of tokens deleted
        """
        pass
