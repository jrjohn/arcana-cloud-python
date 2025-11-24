"""
HTTP Auth Service Client
Implements AuthService interface but communicates via HTTP to Service Layer
For use in Microservices mode
"""
import os
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.services.interfaces.AuthService import AuthService
from app.models.user import User, UserRole, UserStatus
from app.models.oauth_token import OAuthToken
from app.utils.Exceptions import APIException, AuthenticationError, NotFoundError


class HTTPAuthServiceClient(AuthService):
    """
    HTTP-based Auth Service Client
    Implements AuthService interface but makes HTTP requests to Service Layer
    """

    def __init__(self, service_url: str = None):
        """
        Initialize HTTP Auth Service Client

        Args:
            service_url: Base URL of service layer (e.g., http://localhost:5001)
        """
        self.service_url = service_url or os.getenv('SERVICE_URL', 'http://localhost:5001')

        # Setup HTTP session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Make HTTP request to service layer"""
        url = f"{self.service_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            result = response.json()

            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                error_code = result.get('error_code', 'UNKNOWN_ERROR')

                if response.status_code == 404:
                    raise NotFoundError(error_msg)
                elif response.status_code == 401:
                    raise AuthenticationError(error_msg)
                else:
                    raise APIException(error_msg, error_code=error_code, status_code=response.status_code)

            return result.get('data')

        except requests.exceptions.RequestException as e:
            raise APIException(f"HTTP Service Error: {str(e)}")

    def _deserialize_user(self, data: dict) -> Optional[User]:
        """Convert dict to User object"""
        if data is None:
            return None

        # Create User with a dummy password (will be overridden)
        user = User(
            username=data['username'],
            email=data['email'],
            password='DUMMY_PASSWORD_NOT_USED'
        )

        # Set attributes from service data
        user.id = data.get('id')
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.role = UserRole[data['role']] if data.get('role') else UserRole.USER
        user.status = UserStatus[data['status']] if data.get('status') else UserStatus.ACTIVE
        user.is_verified = data.get('is_verified', False)

        # Set password_hash if provided (needed for password verification)
        if data.get('password_hash'):
            user.password_hash = data['password_hash']

        # Set optional datetime fields
        from datetime import datetime
        if data.get('created_at'):
            user.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            user.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('last_login_at'):
            user.last_login_at = datetime.fromisoformat(data['last_login_at'])

        return user

    def _deserialize_token(self, data: dict) -> Optional[OAuthToken]:
        """Convert dict to OAuthToken object"""
        if data is None:
            return None

        token = OAuthToken(
            user_id=data['user_id'],
            access_token=data['access_token'],
            refresh_token=data.get('refresh_token'),
            token_type=data.get('token_type', 'Bearer')
        )

        token.id = data.get('id')
        token.client_id = data.get('client_id')
        token.client_name = data.get('client_name')
        token.ip_address = data.get('ip_address')
        token.user_agent = data.get('user_agent')

        # Set datetime fields
        from datetime import datetime
        if data.get('expires_at'):
            token.expires_at = datetime.fromisoformat(data['expires_at'])
        if data.get('refresh_expires_at'):
            token.refresh_expires_at = datetime.fromisoformat(data['refresh_expires_at'])
        if data.get('created_at'):
            token.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('last_used_at'):
            token.last_used_at = datetime.fromisoformat(data['last_used_at'])

        return token

    def register(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        User registration via HTTP Service Layer
        """
        data = {
            'username': username,
            'email': email,
            'password': password,
            **kwargs
        }

        result = self._make_request('POST', '/internal/auth/register', data=data)
        return result

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
        User login via HTTP Service Layer
        """
        data = {
            'username_or_email': username_or_email,
            'password': password,
            'client_id': client_id,
            'client_name': client_name,
            'ip_address': ip_address,
            'user_agent': user_agent
        }

        result = self._make_request('POST', '/internal/auth/login', data=data)
        return result

    def logout(self, access_token: str) -> bool:
        """
        User logout via HTTP Service Layer
        """
        data = {'access_token': access_token}
        result = self._make_request('POST', '/internal/auth/logout', data=data)
        return result.get('logged_out', False)

    def refreshToken(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh token via HTTP Service Layer
        """
        data = {'refresh_token': refresh_token}
        result = self._make_request('POST', '/internal/auth/refresh', data=data)
        return result

    def validateToken(self, access_token: str) -> User:
        """
        Validate token via HTTP Service Layer
        """
        data = {'access_token': access_token}
        result = self._make_request('POST', '/internal/auth/validate', data=data)
        return self._deserialize_user(result)

    def getUserTokens(self, user_id: int) -> list:
        """
        Get user tokens via HTTP Service Layer
        Returns list of token dicts (not OAuthToken objects) since they're already serialized from service layer
        """
        result = self._make_request('GET', f'/internal/auth/tokens/{user_id}')
        # Return tokens as dicts - they're already serialized by service layer
        # Creating OAuthToken objects is problematic without proper DB session binding
        return result.get('tokens', [])

    def revokeAllTokens(self, user_id: int) -> int:
        """
        Revoke all user tokens via HTTP Service Layer
        """
        result = self._make_request('POST', f'/internal/auth/tokens/revoke-all/{user_id}')
        return result.get('revoked_count', 0)

    def verifyPassword(self, user: User, password: str) -> bool:
        """
        Verify password via HTTP Service Layer
        """
        data = {
            'user_id': user.id,
            'password': password
        }
        result = self._make_request('POST', '/internal/auth/verify-password', data=data)
        return result.get('is_valid', False)
