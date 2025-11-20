"""
Auth Service Interface
Authentication Service interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.models.User import User
from app.models.OAuthToken import OAuthToken


class AuthService(ABC):
    """Authentication Service interface"""

    @abstractmethod
    def login(
        self,
        username_or_email: str,
        password: str,
        client_id: Optional[str] = None,
        client_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        User login

        Args:
            username_or_email: Username或Email
            password: Password
            client_id: Client ID
            client_name: Client name
            ip_address: IP address
            user_agent: User Agent

        Returns:
            Dictionary containing token information

        Raises:
            AuthenticationError: Authentication failed
            ValidationError: Validation failed
        """
        pass

    @abstractmethod
    def logout(self, access_token: str) -> bool:
        """
        User logout（撤銷 token）

        Args:
            access_token: Access token

        Returns:
            是否登出成功

        Raises:
            NotFoundError: Token not found
        """
        pass

    @abstractmethod
    def refreshToken(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            Dictionary containing new token information

        Raises:
            AuthenticationError: Refresh failed
            NotFoundError: Token not found
        """
        pass

    @abstractmethod
    def validateToken(self, access_token: str) -> User:
        """
        Validate token

        Args:
            access_token: Access token

        Returns:
            User object

        Raises:
            AuthenticationError: Token invalid or expired
            NotFoundError: Token 或User not found
        """
        pass

    @abstractmethod
    def revokeAllTokens(self, user_id: int) -> int:
        """
        撤銷用戶的所有 token

        Args:
            user_id: User ID

        Returns:
            撤銷的 token 數量
        """
        pass

    @abstractmethod
    def getUserTokens(self, user_id: int) -> list[OAuthToken]:
        """
        Get user的所有有效 token

        Args:
            user_id: User ID

        Returns:
            Token list
        """
        pass

    @abstractmethod
    def register(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        User registration

        Args:
            username: Username
            email: Email
            password: Password
            **kwargs: Other fields

        Returns:
            Dictionary containing user information and token

        Raises:
            ConflictError: Username或Email已存在
            ValidationError: Validation failed
        """
        pass

    @abstractmethod
    def verifyPassword(self, user: User, password: str) -> bool:
        """
        驗證Password

        Args:
            user: User object
            password: 待驗證的Password

        Returns:
            Password是否正確
        """
        pass
