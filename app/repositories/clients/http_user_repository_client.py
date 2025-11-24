"""
HTTP User Repository Client
Implements UserRepository interface but communicates via HTTP to Repository Layer
For use in Microservices mode
"""
import os
from typing import Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.repositories.interfaces.user_repository import UserRepository
from app.models.user import User, UserRole, UserStatus
from app.utils.exceptions import DatabaseError, NotFoundError


class HTTPUserRepositoryClient(UserRepository):
    """
    HTTP-based User Repository Client
    Implements UserRepository interface but makes HTTP requests to Repository Layer
    """

    def __init__(self, repository_url: str = None):
        """
        Initialize HTTP Repository Client

        Args:
            repository_url: Base URL of repository layer (e.g., http://localhost:5002)
        """
        self.repository_url = repository_url or os.getenv('REPOSITORY_URL', 'http://localhost:5002')

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
        """Make HTTP request to repository layer"""
        url = f"{self.repository_url.rstrip('/')}/{endpoint.lstrip('/')}"

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

            if response.status_code == 404:
                return None  # Not found

            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                if response.status_code == 404:
                    return None
                raise DatabaseError(error_msg)

            return result.get('data')

        except requests.exceptions.RequestException as e:
            raise DatabaseError(f"HTTP Repository Error: {str(e)}")

    def _deserialize_user(self, data: dict) -> Optional[User]:
        """Convert dict to User object"""
        if data is None:
            return None

        # Create User with a dummy password (will be overridden)
        # Repository Layer doesn't send password_hash for security reasons
        user = User(
            username=data['username'],
            email=data['email'],
            password='DUMMY_PASSWORD_NOT_USED'  # Dummy password to satisfy __init__
        )

        # Now set the actual attributes from repository data
        user.id = data.get('id')
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.role = UserRole[data['role']] if data.get('role') else UserRole.USER
        user.status = UserStatus[data['status']] if data.get('status') else UserStatus.ACTIVE
        user.is_verified = data.get('is_verified', False)
        user.is_active = data.get('is_active', True)

        # Set optional fields
        user.phone = data.get('phone')
        user.avatar_url = data.get('avatar_url')

        # Set password_hash if provided (needed for Service Layer password verification)
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

    def _serialize_user(self, user: User) -> dict:
        """Convert User object to dict"""
        data = {
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name if user.role else 'USER',
            'status': user.status.name if user.status else 'ACTIVE',
            'is_verified': getattr(user, 'is_verified', False),
            'is_active': getattr(user, 'is_active', True)
        }

        # Add optional fields if present
        if hasattr(user, 'phone') and user.phone:
            data['phone'] = user.phone
        if hasattr(user, 'avatar_url') and user.avatar_url:
            data['avatar_url'] = user.avatar_url

        return data

    def create(self, user: User) -> User:
        """Create user"""
        data = self._serialize_user(user)
        result = self._make_request('POST', '/repository/users', data=data)
        return self._deserialize_user(result)

    def getById(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = self._make_request('GET', f'/repository/users/{user_id}')
        return self._deserialize_user(result)

    def getByUsername(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = self._make_request('GET', f'/repository/users/username/{username}')
        return self._deserialize_user(result)

    def getByEmail(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = self._make_request('GET', f'/repository/users/email/{email}')
        return self._deserialize_user(result)

    def update(self, user: User) -> User:
        """Update user"""
        data = self._serialize_user(user)
        result = self._make_request('PUT', f'/repository/users/{user.id}', data=data)
        return self._deserialize_user(result)

    def delete(self, user_id: int) -> bool:
        """Delete user"""
        result = self._make_request('DELETE', f'/repository/users/{user_id}')
        return result.get('deleted', False) if result else False

    def existsByUsername(self, username: str) -> bool:
        """Check if username exists"""
        result = self._make_request('GET', f'/repository/users/exists/username/{username}')
        return result.get('exists', False) if result else False

    def existsByEmail(self, email: str) -> bool:
        """Check if email exists"""
        result = self._make_request('GET', f'/repository/users/exists/email/{email}')
        return result.get('exists', False) if result else False

    def getAll(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> tuple[List[User], int]:
        """Get all users (paginated)"""
        params = {'page': page, 'per_page': per_page}
        if role:
            params['role'] = role.name
        if status:
            params['status'] = status.name

        result = self._make_request('GET', '/repository/users', params=params)

        if result is None:
            return [], 0

        users = [self._deserialize_user(u) for u in result.get('users', [])]
        total = result.get('pagination', {}).get('total', 0)

        return users, total

    def count(self) -> int:
        """Get total user count"""
        result = self._make_request('GET', '/repository/users/count')
        return result.get('count', 0) if result else 0
