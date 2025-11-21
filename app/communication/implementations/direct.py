"""
Direct Communication Implementation
For monolithic mode - direct in-process method calls
"""
from typing import Dict, Any
from app.communication.interfaces import (
    ServiceCommunicationInterface,
    RepositoryCommunicationInterface,
    CommunicationMode,
    CommunicationProtocol
)


class DirectServiceCommunication(ServiceCommunicationInterface):
    """
    Direct service communication (Monolithic mode)
    Calls service layer directly without any network communication
    """

    def __init__(self, service_instance):
        """
        Initialize with actual service instance

        Args:
            service_instance: UserServiceImpl instance
        """
        self.service = service_instance
        self._mode = CommunicationMode.MONOLITHIC
        self._protocol = CommunicationProtocol.DIRECT

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call service method directly"""
        service_method = getattr(self.service, method)
        result = service_method(**kwargs)

        # Convert to dict if it's a model instance
        if hasattr(result, 'toDict'):
            return result.toDict()
        return result

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check - always healthy in direct mode"""
        return True

    def get_users(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """Get users list"""
        return self.service.getUsers(page=page, per_page=per_page, **filters)

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID"""
        user = self.service.getUserById(user_id)
        return user.toDict()

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        user = self.service.createUser(**user_data)
        return user.toDict()

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        user = self.service.updateUser(user_id, **user_data)
        return user.toDict()

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user"""
        self.service.deleteUser(user_id)
        return {'success': True, 'message': 'User deleted successfully'}


class DirectRepositoryCommunication(RepositoryCommunicationInterface):
    """
    Direct repository communication (Monolithic mode)
    Calls repository layer directly without any network communication
    """

    def __init__(self, repository_instance):
        """
        Initialize with actual repository instance

        Args:
            repository_instance: UserRepositoryImpl instance
        """
        self.repository = repository_instance
        self._mode = CommunicationMode.MONOLITHIC
        self._protocol = CommunicationProtocol.DIRECT

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call repository method directly"""
        repo_method = getattr(self.repository, method)
        result = repo_method(**kwargs)

        # Convert to dict if it's a model instance
        if hasattr(result, 'toDict'):
            return result.toDict()
        return result

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check - always healthy in direct mode"""
        return True

    def query(self, entity: str, filters: Dict[str, Any],
              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Query entities"""
        # Map to actual repository method
        results, total = self.repository.getAll(page=page, per_page=per_page)
        return {
            'items': [r.toDict() for r in results],
            'total': total,
            'page': page,
            'per_page': per_page
        }

    def get_by_id(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID"""
        result = self.repository.getById(entity_id)
        return result.toDict() if result else None

    def create(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity"""
        result = self.repository.create(**data)
        return result.toDict()

    def update(self, entity: str, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity"""
        result = self.repository.update(entity_id, **data)
        return result.toDict()

    def delete(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Delete entity"""
        self.repository.delete(entity_id)
        return {'success': True, 'message': f'{entity} deleted successfully'}
