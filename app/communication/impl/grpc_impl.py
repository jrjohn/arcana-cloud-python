"""
gRPC Communication Implementation
For layered and microservices modes using gRPC protocol
"""
import os
import grpc
from typing import Dict, Any, Optional
from google.protobuf.json_format import MessageToDict

from app.communication.interfaces import (
    ServiceCommunicationInterface,
    RepositoryCommunicationInterface,
    CommunicationMode,
    CommunicationProtocol,
    DeploymentMode
)
from app.grpc_protos import (
    user_service_pb2, user_service_pb2_grpc,
    repository_service_pb2, repository_service_pb2_grpc,
    common_pb2
)
from app.utils.exceptions import (
    APIException, NotFoundError, ConflictError,
    ValidationError, AuthenticationError, AuthorizationError
)
from app.models.user import UserRole, UserStatus


class GRPCServiceCommunicationImpl(ServiceCommunicationInterface):
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
            self.stubs[url] = user_service_pb2_grpc.UserServiceStub(channel)

    def _get_next_stub(self):
        """Get next service stub (round-robin)"""
        url = self.service_urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.service_urls)
        return self.stubs[url]

    def _proto_to_dict(self, user: common_pb2.User) -> Dict[str, Any]:
        """Convert protobuf User to dict"""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'status': user.status,
            'is_verified': user.is_verified,
            'is_active': user.is_active,
            'phone': user.phone if user.phone else None,
            'avatar_url': user.avatar_url if user.avatar_url else None,
            'created_at': user.created_at if user.created_at else None,
            'updated_at': user.updated_at if user.updated_at else None,
            'last_login_at': user.last_login_at if user.last_login_at else None,
        }

    def _handle_grpc_error(self, e: grpc.RpcError):
        """Handle gRPC errors and convert to appropriate exceptions"""
        code = e.code()
        details = e.details()

        if code == grpc.StatusCode.NOT_FOUND:
            raise NotFoundError(details)
        elif code == grpc.StatusCode.ALREADY_EXISTS:
            raise ConflictError(details)
        elif code == grpc.StatusCode.INVALID_ARGUMENT:
            raise ValidationError(details)
        elif code == grpc.StatusCode.UNAUTHENTICATED:
            raise AuthenticationError(details)
        elif code == grpc.StatusCode.PERMISSION_DENIED:
            raise AuthorizationError(details)
        elif code == grpc.StatusCode.UNAVAILABLE:
            raise APIException(f"Service unavailable: {details}", status_code=503)
        else:
            raise APIException(f"gRPC error: {code} - {details}", status_code=500)

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call service method via gRPC"""
        # Generic method call - not used in this implementation
        raise NotImplementedError("Use specific methods like get_users, create_user, etc.")

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check via gRPC"""
        try:
            stub = self._get_next_stub()
            response = stub.HealthCheck(common_pb2.Empty(), timeout=5)
            return response.status == "healthy"
        except Exception:
            return False

    def get_users(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """Get users list via gRPC"""
        try:
            stub = self._get_next_stub()

            # Build request
            request = user_service_pb2.GetUsersRequest(
                page=page,
                per_page=per_page,
                role=filters.get('role').name if filters.get('role') else "",
                status=filters.get('status').name if filters.get('status') else ""
            )

            # Make gRPC call
            response = stub.GetUsers(request, timeout=30)

            # Convert response
            users = [self._proto_to_dict(user) for user in response.users]

            return {
                'items': users,
                'pagination': {
                    'page': response.pagination.page,
                    'per_page': response.pagination.per_page,
                    'total': response.pagination.total,
                    'pages': response.pagination.total_pages
                }
            }

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID via gRPC"""
        try:
            stub = self._get_next_stub()
            request = user_service_pb2.GetUserByIdRequest(user_id=user_id)
            response = stub.GetUserById(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user via gRPC"""
        try:
            stub = self._get_next_stub()

            request = user_service_pb2.CreateUserRequest(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                phone=user_data.get('phone', ''),
                avatar_url=user_data.get('avatar_url', '')
            )

            response = stub.CreateUser(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user via gRPC"""
        try:
            stub = self._get_next_stub()

            request = user_service_pb2.UpdateUserRequest(
                user_id=user_id,
                username=user_data.get('username', ''),
                email=user_data.get('email', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                phone=user_data.get('phone', ''),
                avatar_url=user_data.get('avatar_url', ''),
                role=user_data.get('role', ''),
                status=user_data.get('status', '')
            )

            response = stub.UpdateUser(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user via gRPC"""
        try:
            stub = self._get_next_stub()
            request = user_service_pb2.DeleteUserRequest(user_id=user_id)
            response = stub.DeleteUser(request, timeout=10)
            return {'success': response.success, 'message': response.message}

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password via gRPC"""
        try:
            stub = self._get_next_stub()

            request = user_service_pb2.ChangePasswordRequest(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password
            )

            response = stub.ChangePassword(request, timeout=10)
            return {'success': response.success, 'message': response.message}

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def verify_user(self, user_id: int) -> Dict[str, Any]:
        """Verify user via gRPC"""
        try:
            stub = self._get_next_stub()
            request = user_service_pb2.VerifyUserRequest(user_id=user_id)
            response = stub.VerifyUser(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def update_user_status(self, user_id: int, status: str) -> Dict[str, Any]:
        """Update user status via gRPC"""
        try:
            stub = self._get_next_stub()

            request = user_service_pb2.UpdateUserStatusRequest(
                user_id=user_id,
                status=status
            )

            response = stub.UpdateUserStatus(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def __del__(self):
        """Close gRPC channels on cleanup"""
        for channel in self.channels.values():
            try:
                channel.close()
            except Exception:  # noqa: BLE001
                pass


class GRPCRepositoryCommunicationImpl(RepositoryCommunicationInterface):
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

            channel = grpc.insecure_channel(
                grpc_url,
                options=[
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 10000),
                    ('grpc.keepalive_timeout_ms', 5000),
                ]
            )
            self.channels[url] = channel
            self.stubs[url] = repository_service_pb2_grpc.RepositoryServiceStub(channel)

    def _get_next_stub(self):
        """Get next repository stub (round-robin)"""
        url = self.repository_urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.repository_urls)
        return self.stubs[url]

    def _proto_to_dict(self, user: common_pb2.User) -> Dict[str, Any]:
        """Convert protobuf User to dict"""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'status': user.status,
            'is_verified': user.is_verified,
            'is_active': user.is_active,
            'phone': user.phone if user.phone else None,
            'avatar_url': user.avatar_url if user.avatar_url else None,
            'created_at': user.created_at if user.created_at else None,
            'updated_at': user.updated_at if user.updated_at else None,
            'last_login_at': user.last_login_at if user.last_login_at else None,
        }

    def _handle_grpc_error(self, e: grpc.RpcError):
        """Handle gRPC errors and convert to appropriate exceptions"""
        code = e.code()
        details = e.details()

        if code == grpc.StatusCode.NOT_FOUND:
            raise NotFoundError(details)
        elif code == grpc.StatusCode.ALREADY_EXISTS:
            raise ConflictError(details)
        elif code == grpc.StatusCode.INVALID_ARGUMENT:
            raise ValidationError(details)
        elif code == grpc.StatusCode.UNAVAILABLE:
            raise APIException(f"Repository unavailable: {details}", status_code=503)
        else:
            raise APIException(f"Repository gRPC error: {code} - {details}", status_code=500)

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call repository method via gRPC"""
        # Generic method call - not used in this implementation
        raise NotImplementedError("Use specific methods like query_users, get_user_by_id, etc.")

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check via gRPC"""
        try:
            stub = self._get_next_stub()
            response = stub.HealthCheck(common_pb2.Empty(), timeout=5)
            return response.status == "healthy"
        except Exception:
            return False

    def query_users(self, page: int = 1, per_page: int = 20, role: Optional[str] = None,
                    status: Optional[str] = None) -> tuple:
        """Query users via gRPC"""
        try:
            stub = self._get_next_stub()

            request = repository_service_pb2.QueryUsersRequest(
                page=page,
                per_page=per_page,
                role=role if role else "",
                status=status if status else ""
            )

            response = stub.QueryUsers(request, timeout=30)

            # Convert to User objects (simplified - return dicts)
            users = [self._proto_to_dict(user) for user in response.users]

            return users, response.total

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID via gRPC"""
        try:
            stub = self._get_next_stub()
            request = repository_service_pb2.GetUserByIdRepositoryRequest(user_id=user_id)
            response = stub.GetUserById(request, timeout=10)

            if response.id == 0:  # Empty response
                return None

            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_grpc_error(e)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username via gRPC"""
        try:
            stub = self._get_next_stub()
            request = repository_service_pb2.GetUserByUsernameRequest(username=username)
            response = stub.GetUserByUsername(request, timeout=10)

            if response.id == 0:
                return None

            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_grpc_error(e)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email via gRPC"""
        try:
            stub = self._get_next_stub()
            request = repository_service_pb2.GetUserByEmailRequest(email=email)
            response = stub.GetUserByEmail(request, timeout=10)

            if response.id == 0:
                return None

            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_grpc_error(e)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user via gRPC"""
        try:
            stub = self._get_next_stub()

            request = repository_service_pb2.CreateUserRepositoryRequest(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                role=user_data.get('role', 'USER'),
                status=user_data.get('status', 'ACTIVE'),
                is_verified=user_data.get('is_verified', False),
                is_active=user_data.get('is_active', True),
                phone=user_data.get('phone', ''),
                avatar_url=user_data.get('avatar_url', '')
            )

            response = stub.CreateUser(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user via gRPC"""
        try:
            stub = self._get_next_stub()

            request = repository_service_pb2.UpdateUserRepositoryRequest(
                user_id=user_data['id'],
                username=user_data.get('username', ''),
                email=user_data.get('email', ''),
                password_hash=user_data.get('password_hash', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                role=user_data.get('role', ''),
                status=user_data.get('status', ''),
                is_verified=user_data.get('is_verified', False),
                is_active=user_data.get('is_active', True),
                phone=user_data.get('phone', ''),
                avatar_url=user_data.get('avatar_url', '')
            )

            response = stub.UpdateUser(request, timeout=10)
            return self._proto_to_dict(response)

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def delete_user(self, user_id: int) -> bool:
        """Delete user via gRPC"""
        try:
            stub = self._get_next_stub()
            request = repository_service_pb2.DeleteUserRepositoryRequest(user_id=user_id)
            response = stub.DeleteUser(request, timeout=10)
            return response.success

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def exists_by_username(self, username: str) -> bool:
        """Check if username exists via gRPC"""
        try:
            stub = self._get_next_stub()
            request = repository_service_pb2.ExistsByUsernameRequest(username=username)
            response = stub.ExistsByUsername(request, timeout=10)
            return response.exists

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def exists_by_email(self, email: str) -> bool:
        """Check if email exists via gRPC"""
        try:
            stub = self._get_next_stub()
            request = repository_service_pb2.ExistsByEmailRequest(email=email)
            response = stub.ExistsByEmail(request, timeout=10)
            return response.exists

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def count_users(self) -> int:
        """Count users via gRPC"""
        try:
            stub = self._get_next_stub()
            response = stub.CountUsers(common_pb2.Empty(), timeout=10)
            return response.count

        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def query(self, entity: str, filters: Dict[str, Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Query entities - delegates to entity-specific methods"""
        if entity == 'users':
            role = filters.get('role') if filters else None
            status = filters.get('status') if filters else None
            users, total = self.query_users(page, per_page, role, status)
            return {'users': users, 'total': total}
        else:
            raise NotImplementedError(f"Entity '{entity}' not supported by gRPC repository communication")

    def get_by_id(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID - delegates to entity-specific methods"""
        if entity == 'users':
            return self.get_user_by_id(entity_id)
        else:
            raise NotImplementedError(f"Entity '{entity}' not supported by gRPC repository communication")

    def create(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity - delegates to entity-specific methods"""
        if entity == 'users':
            return self.create_user(data)
        else:
            raise NotImplementedError(f"Entity '{entity}' not supported by gRPC repository communication")

    def update(self, entity: str, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity - delegates to entity-specific methods"""
        if entity == 'users':
            # Merge entity_id into data for update_user
            user_data = {**data, 'id': entity_id}
            return self.update_user(user_data)
        else:
            raise NotImplementedError(f"Entity '{entity}' not supported by gRPC repository communication")

    def delete(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Delete entity - delegates to entity-specific methods"""
        if entity == 'users':
            success = self.delete_user(entity_id)
            return {'success': success}
        else:
            raise NotImplementedError(f"Entity '{entity}' not supported by gRPC repository communication")

    def __del__(self):
        """Close gRPC channels on cleanup"""
        for channel in self.channels.values():
            try:
                channel.close()
            except Exception:  # noqa: BLE001
                pass
