"""
User Service Adapter
Provides a unified interface that works in both monolithic and layered modes
"""
import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from app.services.clients.service_client import ServiceClient
from app.services.implementations.user_service_impl import UserServiceImpl
from app.repositories.implementations.user_repository_impl import UserRepositoryImpl
from app.extensions import db
from app.models.user import User, UserRole, UserStatus
from app.utils.exceptions import NotFoundError, APIException


class UserServiceInterface(ABC):
    """Abstract interface for UserService"""

    @abstractmethod
    def getUsers(self, page: int = 1, per_page: int = 20,
                 role: Optional[UserRole] = None,
                 status: Optional[UserStatus] = None) -> Dict[str, Any]:
        """Get paginated users"""
        pass

    @abstractmethod
    def getUserById(self, user_id: int) -> User:
        """Get user by ID"""
        pass

    @abstractmethod
    def createUser(self, username: str, email: str, password: str,
                   first_name: Optional[str] = None,
                   last_name: Optional[str] = None,
                   phone: Optional[str] = None,
                   avatar_url: Optional[str] = None) -> User:
        """Create new user"""
        pass

    @abstractmethod
    def updateUser(self, user_id: int, **kwargs) -> User:
        """Update user"""
        pass

    @abstractmethod
    def deleteUser(self, user_id: int) -> None:
        """Delete user"""
        pass

    @abstractmethod
    def changePassword(self, user_id: int, old_password: str, new_password: str) -> None:
        """Change password"""
        pass

    @abstractmethod
    def verifyUser(self, user_id: int) -> User:
        """Verify user"""
        pass

    @abstractmethod
    def updateUserStatus(self, user_id: int, status: UserStatus) -> User:
        """Update user status"""
        pass


class MonolithicUserService(UserServiceInterface):
    """Monolithic mode: Direct service calls"""

    def __init__(self):
        user_repo = UserRepositoryImpl(db.session)
        self.service = UserServiceImpl(user_repo)

    def getUsers(self, page: int = 1, per_page: int = 20,
                 role: Optional[UserRole] = None,
                 status: Optional[UserStatus] = None) -> Dict[str, Any]:
        return self.service.getUsers(page=page, per_page=per_page, role=role, status=status)

    def getUserById(self, user_id: int) -> User:
        return self.service.getUserById(user_id)

    def createUser(self, username: str, email: str, password: str,
                   first_name: Optional[str] = None,
                   last_name: Optional[str] = None,
                   phone: Optional[str] = None,
                   avatar_url: Optional[str] = None) -> User:
        return self.service.createUser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            avatar_url=avatar_url
        )

    def updateUser(self, user_id: int, **kwargs) -> User:
        return self.service.updateUser(user_id, **kwargs)

    def deleteUser(self, user_id: int) -> None:
        return self.service.deleteUser(user_id)

    def changePassword(self, user_id: int, old_password: str, new_password: str) -> None:
        return self.service.changePassword(user_id, old_password, new_password)

    def verifyUser(self, user_id: int) -> User:
        return self.service.verifyUser(user_id)

    def updateUserStatus(self, user_id: int, status: UserStatus) -> User:
        return self.service.updateUserStatus(user_id, status)


class LayeredUserService(UserServiceInterface):
    """Layered mode: HTTP/REST calls via ServiceClient"""

    def __init__(self):
        # Get service URLs from environment
        service_urls_str = os.getenv('USER_SERVICE_URLS', 'http://localhost:5001')
        service_urls = [url.strip() for url in service_urls_str.split(',')]

        self.client = ServiceClient(
            service_name='user-service',
            timeout=30,
            max_retries=3
        )
        self.client.load_balancer.urls = service_urls

    def getUsers(self, page: int = 1, per_page: int = 20,
                 role: Optional[UserRole] = None,
                 status: Optional[UserStatus] = None) -> Dict[str, Any]:
        """HTTP GET /internal/users"""
        params = {
            'page': page,
            'per_page': per_page
        }
        if role:
            params['role'] = role.value
        if status:
            params['status'] = status.value

        response = self.client.get('/internal/users', params=params)
        if not response.get('success'):
            raise APIException(response.get('error', 'Unknown error'))

        return response['data']

    def getUserById(self, user_id: int) -> User:
        """HTTP GET /internal/users/{user_id}"""
        response = self.client.get(f'/internal/users/{user_id}')

        if not response.get('success'):
            error = response.get('error', 'User not found')
            raise NotFoundError(error)

        # Convert dict back to User object
        user_data = response['data']
        return User(**user_data)

    def createUser(self, username: str, email: str, password: str,
                   first_name: Optional[str] = None,
                   last_name: Optional[str] = None,
                   phone: Optional[str] = None,
                   avatar_url: Optional[str] = None) -> User:
        """HTTP POST /internal/users"""
        data = {
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'avatar_url': avatar_url
        }

        response = self.client.post('/internal/users', data=data)

        if not response.get('success'):
            raise APIException(response.get('error', 'Failed to create user'))

        user_data = response['data']
        return User(**user_data)

    def updateUser(self, user_id: int, **kwargs) -> User:
        """HTTP PUT /internal/users/{user_id}"""
        response = self.client.put(f'/internal/users/{user_id}', data=kwargs)

        if not response.get('success'):
            error = response.get('error', 'Failed to update user')
            raise APIException(error)

        user_data = response['data']
        return User(**user_data)

    def deleteUser(self, user_id: int) -> None:
        """HTTP DELETE /internal/users/{user_id}"""
        response = self.client.delete(f'/internal/users/{user_id}')

        if not response.get('success'):
            error = response.get('error', 'Failed to delete user')
            raise APIException(error)

    def changePassword(self, user_id: int, old_password: str, new_password: str) -> None:
        """HTTP PUT /internal/users/{user_id}/password"""
        data = {
            'old_password': old_password,
            'new_password': new_password
        }

        response = self.client.put(f'/internal/users/{user_id}/password', data=data)

        if not response.get('success'):
            error = response.get('error', 'Failed to change password')
            raise APIException(error)

    def verifyUser(self, user_id: int) -> User:
        """HTTP POST /internal/users/{user_id}/verify"""
        response = self.client.post(f'/internal/users/{user_id}/verify')

        if not response.get('success'):
            error = response.get('error', 'Failed to verify user')
            raise APIException(error)

        user_data = response['data']
        return User(**user_data)

    def updateUserStatus(self, user_id: int, status: UserStatus) -> User:
        """HTTP PUT /internal/users/{user_id}/status"""
        data = {'status': status.value}

        response = self.client.put(f'/internal/users/{user_id}/status', data=data)

        if not response.get('success'):
            error = response.get('error', 'Failed to update user status')
            raise APIException(error)

        user_data = response['data']
        return User(**user_data)


def get_user_service() -> UserServiceInterface:
    """
    Factory function to get appropriate UserService based on deployment mode

    Returns:
        - MonolithicUserService: For monolithic deployment (direct calls)
        - LayeredUserService: For layered deployment (HTTP/REST calls)
    """
    deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic')

    if deployment_layer == 'controller':
        # Controller layer uses HTTP client to communicate with Service layer
        return LayeredUserService()
    else:
        # Monolithic, service, or repository layers use direct service calls
        return MonolithicUserService()
