"""
Auth Service Implementation
Authentication Service implementation
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt

from app.models.user import User, UserStatus
from app.models.oauth_token import OAuthToken
from app.repositories.interfaces.UserRepository import UserRepository
from app.repositories.interfaces.OAuthTokenRepository import OAuthTokenRepository
from app.services.interfaces.AuthService import AuthService
from app.utils.Exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ConflictError
)


class AuthServiceImpl(AuthService):
    """Authentication Service implementation"""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: OAuthTokenRepository
    ):
        """
        Initialize

        Args:
            user_repository: 用戶 Repository
            token_repository: Token Repository
        """
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
        self.access_token_expires = int(os.getenv('ACCESS_TOKEN_EXPIRES', '3600'))
        self.refresh_token_expires = int(os.getenv('REFRESH_TOKEN_EXPIRES', '2592000'))

    def _generate_jwt_token(self, user: User, token_type: str = 'access', expires_in: int = 3600) -> str:
        """
        Generate JWT token

        Args:
            user: User object
            token_type: token 類型（access 或 refresh）
            expires_in: 有效期（秒）

        Returns:
            JWT token
        """
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'token_type': token_type,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }

        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def _verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token

        Args:
            token: JWT token

        Returns:
            Decoded payload

        Raises:
            AuthenticationError: Token invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    def login(
        self,
        username_or_email: str,
        password: str,
        client_id: Optional[str] = None,
        client_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """User login"""
        # 查找用戶（支持Username或Email）
        user = None
        if '@' in username_or_email:
            user = self.user_repository.getByEmail(username_or_email)
        else:
            user = self.user_repository.getByUsername(username_or_email)

        if not user:
            raise AuthenticationError("Invalid username/email or password")

        # 驗證Password
        if not user.checkPassword(password):
            raise AuthenticationError("Invalid username/email or password")

        # Check user狀態
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(f"User account is {user.status.value}")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Generate tokens
        access_token = self._generate_jwt_token(user, 'access', self.access_token_expires)
        refresh_token = self._generate_jwt_token(user, 'refresh', self.refresh_token_expires)

        # 保存 token 到Database
        oauth_token = OAuthToken(
            user_id=user.id,
            access_token=access_token,
            expires_in=self.access_token_expires,
            refresh_token=refresh_token,
            refresh_expires_in=self.refresh_token_expires,
            client_id=client_id,
            client_name=client_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.token_repository.create(oauth_token)

        # Update last login time
        user.updateLastLogin()
        self.user_repository.update(user)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': self.access_token_expires,
            'user': user.toDict()
        }

    def logout(self, access_token: str) -> bool:
        """User logout"""
        token = self.token_repository.getByAccessToken(access_token)
        if not token:
            raise NotFoundError("Token not found", "OAuthToken")

        token.revoke()
        self.token_repository.update(token)
        return True

    def refreshToken(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh token"""
        # 驗證 refresh token
        try:
            payload = self._verify_jwt_token(refresh_token)
            if payload.get('token_type') != 'refresh':
                raise AuthenticationError("Invalid token type")
        except AuthenticationError:
            raise

        # 查找Database中的 token 記錄
        token = self.token_repository.getByRefreshToken(refresh_token)
        if not token:
            raise NotFoundError("Refresh token not found", "OAuthToken")

        # Check token status
        if token.is_revoked:
            raise AuthenticationError("Token has been revoked")

        if token.isRefreshExpired():
            raise AuthenticationError("Refresh token has expired")

        # Get user
        user = self.user_repository.getById(token.user_id)
        if not user:
            raise NotFoundError("User not found", "User")

        # Generate new access token
        new_access_token = self._generate_jwt_token(user, 'access', self.access_token_expires)

        # 更新Database中的 token
        token.access_token = new_access_token
        token.expires_at = datetime.utcnow() + timedelta(seconds=self.access_token_expires)
        self.token_repository.update(token)

        return {
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': self.access_token_expires
        }

    def validateToken(self, access_token: str) -> User:
        """Validate token"""
        # 驗證 JWT
        try:
            payload = self._verify_jwt_token(access_token)
            if payload.get('token_type') != 'access':
                raise AuthenticationError("Invalid token type")
        except AuthenticationError:
            raise

        # 查找Database中的 token 記錄
        token = self.token_repository.getByAccessToken(access_token)
        if not token:
            raise NotFoundError("Token not found", "OAuthToken")

        # Check token status
        if not token.isValid():
            raise AuthenticationError("Token is invalid or expired")

        # Get user
        user = self.user_repository.getById(token.user_id)
        if not user:
            raise NotFoundError("User not found", "User")

        # Check user狀態
        if user.status != UserStatus.ACTIVE or not user.is_active:
            raise AuthenticationError("User account is not active")

        # Update token last used time
        token.updateLastUsed()
        self.token_repository.update(token)

        return user

    def revokeAllTokens(self, user_id: int) -> int:
        """撤銷用戶的所有 token"""
        return self.token_repository.revokeAllByUserId(user_id)

    def getUserTokens(self, user_id: int) -> list[OAuthToken]:
        """Get user的所有有效 token"""
        return self.token_repository.getByUserId(user_id, include_revoked=False)

    def register(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> Dict[str, Any]:
        """User registration"""
        # 使用 UserService 的邏輯Create user（需要注入 UserService）
        # 這裡簡化實現，直接Create user
        from app.services.implementations.UserServiceImpl import UserServiceImpl

        # Check user是否已存在
        if self.user_repository.existsByUsername(username):
            raise ConflictError(f"Username '{username}' already exists")

        if self.user_repository.existsByEmail(email):
            raise ConflictError(f"Email '{email}' already exists")

        # Create user
        user = User(username=username, email=email, password=password, **kwargs)
        user = self.user_repository.create(user)

        # 自動登入並返回 token
        return self.login(username, password)

    def verifyPassword(self, user: User, password: str) -> bool:
        """驗證Password"""
        return user.checkPassword(password)
