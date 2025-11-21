"""
gRPC Communication Implementation
For layered and microservices modes using gRPC protocol
"""
import os
import grpc
from typing import Dict, Any
import json

from app.communication.interfaces import (
    ServiceCommunicationInterface,
    RepositoryCommunicationInterface,
    CommunicationMode,
    CommunicationProtocol,
    DeploymentMode
)
from app.utils.Exceptions import APIException, NotFoundError


class GRPCServiceCommunication(ServiceCommunicationInterface):
    """
    gRPC service communication
    For Controller → Service communication via gRPC
    """

    def __init__(self, service_urls: list, deployment_mode: DeploymentMode):
        """
        Initialize gRPC service communication

        Args:
            service_urls: List of service URLs (host:port format)
            deployment_mode: Deployment mode (layered or microservices)
        """
        self.service_urls = service_urls
        self.current_url_index = 0
        self.deployment_mode = deployment_mode

        # Determine communication mode
        if deployment_mode == DeploymentMode.LAYERED:
            self._mode = CommunicationMode.LAYERED_GRPC
        else:
            self._mode = CommunicationMode.MICROSERVICES_GRPC

        self._protocol = CommunicationProtocol.GRPC

        # Create gRPC channels (connection pooling)
        self.channels = {}
        self.stubs = {}
        self._initialize_connections()

    def _initialize_connections(self):
        """Initialize gRPC channels and stubs"""
        for url in self.service_urls:
            # Remove http:// or https:// prefix if present
            grpc_url = url.replace('http://', '').replace('https://', '')

            # Create gRPC channel with options
            channel = grpc.insecure_channel(
                grpc_url,
                options=[
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 10000),
                    ('grpc.keepalive_timeout_ms', 5000),
                ]
            )
            self.channels[url] = channel

            # TODO: Create actual gRPC stub when protobuf is defined
            # from app.grpc import user_service_pb2_grpc
            # self.stubs[url] = user_service_pb2_grpc.UserServiceStub(channel)

    def _get_next_url(self) -> str:
        """Get next service URL (round-robin)"""
        url = self.service_urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.service_urls)
        return url

    def _make_grpc_call(self, method_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make gRPC call

        Args:
            method_name: gRPC method name
            request_data: Request data as dict

        Returns:
            Response data as dict
        """
        url = self._get_next_url()

        try:
            # TODO: Implement actual gRPC call when protobuf is defined
            # stub = self.stubs[url]
            # request = user_service_pb2.UserRequest(**request_data)
            # response = stub.GetUser(request, timeout=30)
            # return MessageToDict(response)

            # Placeholder implementation
            raise NotImplementedError(
                "gRPC implementation requires protobuf definitions. "
                "Please generate .proto files and gRPC stubs first. "
                "For now, use HTTP mode or implement protobuf definitions."
            )

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise NotFoundError(f"Resource not found: {method_name}")
            elif e.code() == grpc.StatusCode.UNAVAILABLE:
                raise APIException(f"Service unavailable: {url}")
            else:
                raise APIException(f"gRPC error: {e.code()} - {e.details()}")

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call service method via gRPC"""
        return self._make_grpc_call(method, kwargs)

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check via gRPC"""
        try:
            # TODO: Implement gRPC health check
            # channel = self.channels[self.service_urls[0]]
            # grpc.channel_ready_future(channel).result(timeout=5)
            # return True
            return False  # Not implemented yet
        except:
            return False

    def get_users(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """Get users list via gRPC"""
        return self._make_grpc_call('GetUsers', {
            'page': page,
            'per_page': per_page,
            **filters
        })

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID via gRPC"""
        return self._make_grpc_call('GetUser', {'user_id': user_id})

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user via gRPC"""
        return self._make_grpc_call('CreateUser', user_data)

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user via gRPC"""
        return self._make_grpc_call('UpdateUser', {'user_id': user_id, **user_data})

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user via gRPC"""
        return self._make_grpc_call('DeleteUser', {'user_id': user_id})

    def __del__(self):
        """Close gRPC channels on cleanup"""
        for channel in self.channels.values():
            channel.close()


class GRPCRepositoryCommunication(RepositoryCommunicationInterface):
    """
    gRPC repository communication
    For Service → Repository communication via gRPC
    """

    def __init__(self, repository_urls: list, deployment_mode: DeploymentMode):
        """
        Initialize gRPC repository communication

        Args:
            repository_urls: List of repository URLs (host:port format)
            deployment_mode: Deployment mode (layered or microservices)
        """
        self.repository_urls = repository_urls
        self.current_url_index = 0
        self.deployment_mode = deployment_mode

        # Determine communication mode
        if deployment_mode == DeploymentMode.LAYERED:
            self._mode = CommunicationMode.LAYERED_GRPC
        else:
            self._mode = CommunicationMode.MICROSERVICES_GRPC

        self._protocol = CommunicationProtocol.GRPC

        # Create gRPC channels
        self.channels = {}
        self.stubs = {}
        self._initialize_connections()

    def _initialize_connections(self):
        """Initialize gRPC channels and stubs"""
        for url in self.repository_urls:
            grpc_url = url.replace('http://', '').replace('https://', '')
            channel = grpc.insecure_channel(grpc_url)
            self.channels[url] = channel

            # TODO: Create actual gRPC stub
            # from app.grpc import repository_pb2_grpc
            # self.stubs[url] = repository_pb2_grpc.RepositoryServiceStub(channel)

    def _get_next_url(self) -> str:
        """Get next repository URL (round-robin)"""
        url = self.repository_urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.repository_urls)
        return url

    def _make_grpc_call(self, method_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make gRPC call to repository"""
        url = self._get_next_url()

        try:
            # TODO: Implement actual gRPC call
            raise NotImplementedError(
                "gRPC repository implementation requires protobuf definitions. "
                "Please generate .proto files and gRPC stubs first."
            )
        except grpc.RpcError as e:
            raise APIException(f"Repository gRPC error: {e.code()} - {e.details()}")

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call repository method via gRPC"""
        return self._make_grpc_call(method, kwargs)

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check via gRPC"""
        try:
            # TODO: Implement gRPC health check
            return False  # Not implemented yet
        except:
            return False

    def query(self, entity: str, filters: Dict[str, Any],
              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Query entities via gRPC"""
        return self._make_grpc_call('Query', {
            'entity': entity,
            'filters': filters,
            'page': page,
            'per_page': per_page
        })

    def get_by_id(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID via gRPC"""
        return self._make_grpc_call('GetById', {
            'entity': entity,
            'entity_id': entity_id
        })

    def create(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity via gRPC"""
        return self._make_grpc_call('Create', {
            'entity': entity,
            'data': data
        })

    def update(self, entity: str, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity via gRPC"""
        return self._make_grpc_call('Update', {
            'entity': entity,
            'entity_id': entity_id,
            'data': data
        })

    def delete(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Delete entity via gRPC"""
        return self._make_grpc_call('Delete', {
            'entity': entity,
            'entity_id': entity_id
        })

    def __del__(self):
        """Close gRPC channels on cleanup"""
        for channel in self.channels.values():
            channel.close()
