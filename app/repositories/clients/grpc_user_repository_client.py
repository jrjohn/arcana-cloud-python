"""
gRPC User Repository Client
Wraps GRPCRepositoryCommunication to provide repository interface
"""
import os
from typing import List, Tuple, Optional
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole, UserStatus
from app.communication import CommunicationFactory


class GRPCUserRepositoryClient(UserRepository):
    """gRPC client for User Repository"""

    def __init__(self):
        """Initialize gRPC repository client"""
        # Get repository URLs from environment
        self.repository_urls = os.getenv('REPOSITORY_URL', 'localhost:50052')

        # Create gRPC repository communication
        self.comm = CommunicationFactory.create_repository_communication()

    def getAll(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> Tuple[List[User], int]:
        """Get all users with pagination"""
        users_data, total = self.comm.query_users(
            page=page,
            per_page=per_page,
            role=role.name if role else None,
            status=status.name if status else None
        )

        # Convert dictionaries to User objects
        users = [self._dict_to_user(u) for u in users_data]

        return users, total

    def getById(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = self.comm.get_user_by_id(user_id)
        return self._dict_to_user(result) if result else None

    def getByUsername(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = self.comm.get_user_by_username(username)
        return self._dict_to_user(result) if result else None

    def getByEmail(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = self.comm.get_user_by_email(email)
        return self._dict_to_user(result) if result else None

    def create(self, user: User) -> User:
        """Create new user"""
        user_data = {
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name if user.role else 'USER',
            'status': user.status.name if user.status else 'ACTIVE',
            'is_verified': user.is_verified if hasattr(user, 'is_verified') else False,
            'is_active': user.is_active if hasattr(user, 'is_active') else True,
            'phone': user.phone,
            'avatar_url': user.avatar_url
        }

        result = self.comm.create_user(user_data)
        return self._dict_to_user(result)

    def update(self, user: User) -> User:
        """Update user"""
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name if user.role else None,
            'status': user.status.name if user.status else None,
            'is_verified': user.is_verified if hasattr(user, 'is_verified') else None,
            'is_active': user.is_active if hasattr(user, 'is_active') else None,
            'phone': user.phone,
            'avatar_url': user.avatar_url
        }

        # Merge user.id into user_data
        user_data['id'] = user.id
        result = self.comm.update_user(user_data)
        return self._dict_to_user(result)

    def delete(self, user_id: int) -> bool:
        """Delete user"""
        return self.comm.delete_user(user_id)

    def existsByUsername(self, username: str) -> bool:
        """Check if username exists"""
        return self.comm.exists_by_username(username)

    def existsByEmail(self, email: str) -> bool:
        """Check if email exists"""
        return self.comm.exists_by_email(email)

    def count(self) -> int:
        """Count total users"""
        return self.comm.count_users()

    def _dict_to_user(self, data: dict) -> "User | None":
        """Convert dictionary to User object"""
        if not data:
            return None

        # Create user with dummy password, then override password_hash
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password="",  # Dummy password, will be overridden
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=UserRole[data.get('role')] if data.get('role') else UserRole.USER,
            status=UserStatus[data.get('status')] if data.get('status') else UserStatus.ACTIVE,
            phone=data.get('phone'),
            avatar_url=data.get('avatar_url')
        )

        # Set ID and other fields
        user.id = data.get('id')
        user.password_hash = data.get('password_hash')  # Override the hash from dummy password
        user.is_verified = data.get('is_verified', False)
        user.is_active = data.get('is_active', True)

        # Handle datetime fields
        if data.get('created_at'):
            from datetime import datetime
            user.created_at = datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at']
        if data.get('updated_at'):
            from datetime import datetime
            user.updated_at = datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
        if data.get('last_login_at'):
            from datetime import datetime
            user.last_login_at = datetime.fromisoformat(data['last_login_at']) if isinstance(data['last_login_at'], str) else data['last_login_at']

        return user
