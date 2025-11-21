"""
Communication Interfaces
Abstract interfaces for cross-layer communication
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from enum import Enum


class CommunicationMode(Enum):
    """Communication mode enumeration"""
    MONOLITHIC = "monolithic"  # Direct in-process calls
    LAYERED_HTTP = "layered_http"  # HTTP/REST for layered
    LAYERED_GRPC = "layered_grpc"  # gRPC for layered
    MICROSERVICES_HTTP = "microservices_http"  # HTTP/REST for microservices
    MICROSERVICES_GRPC = "microservices_grpc"  # gRPC for microservices


class DeploymentMode(Enum):
    """Deployment mode enumeration"""
    MONOLITHIC = "monolithic"
    LAYERED = "layered"
    MICROSERVICES = "microservices"


class CommunicationProtocol(Enum):
    """Communication protocol enumeration"""
    DIRECT = "direct"  # Direct in-process calls
    HTTP = "http"  # HTTP/REST
    GRPC = "grpc"  # gRPC


T = TypeVar('T')  # Generic type for return values


class CommunicationInterface(ABC, Generic[T]):
    """
    Abstract interface for cross-layer communication

    Supports:
    - Monolithic: Direct in-process calls
    - Layered: HTTP/REST or gRPC between layers
    - Microservices: HTTP/REST or gRPC between services
    """

    @abstractmethod
    def call(self, method: str, **kwargs) -> T:
        """
        Call a remote or local method

        Args:
            method: Method name to call
            **kwargs: Method arguments

        Returns:
            Method result
        """
        pass

    @abstractmethod
    def get_mode(self) -> CommunicationMode:
        """Get current communication mode"""
        pass

    @abstractmethod
    def get_protocol(self) -> CommunicationProtocol:
        """Get current communication protocol"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if communication channel is healthy"""
        pass


class ServiceCommunicationInterface(CommunicationInterface[Dict[str, Any]]):
    """
    Service layer communication interface
    For Controller → Service communication
    """

    @abstractmethod
    def get_users(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """Get users list"""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID"""
        pass

    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        pass

    @abstractmethod
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user"""
        pass


class RepositoryCommunicationInterface(CommunicationInterface[Dict[str, Any]]):
    """
    Repository layer communication interface
    For Service → Repository communication
    """

    @abstractmethod
    def query(self, entity: str, filters: Dict[str, Any],
              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Query entities"""
        pass

    @abstractmethod
    def get_by_id(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID"""
        pass

    @abstractmethod
    def create(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity"""
        pass

    @abstractmethod
    def update(self, entity: str, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity"""
        pass

    @abstractmethod
    def delete(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Delete entity"""
        pass
