"""
User Service gRPC Server
Implements UserService gRPC interface for Service Layer
"""
import grpc
from concurrent import futures
from datetime import datetime

from app.grpc_protos import user_service_pb2, user_service_pb2_grpc, common_pb2
from app.di_container import get_user_service
from app.utils.Exceptions import APIException, NotFoundError, ConflictError, ValidationError, AuthenticationError
from app.models.user import UserRole, UserStatus


class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    """gRPC servicer for User Service"""

    def __init__(self, app=None):
        self.user_service = None
        self.app = app

    def _get_user_service(self):
        """Get user service from DI container"""
        if not self.user_service:
            self.user_service = get_user_service()
        return self.user_service

    def _user_to_proto(self, user) -> common_pb2.User:
        """Convert User model or dict to protobuf User message"""
        # Handle both User objects and dictionaries
        if isinstance(user, dict):
            return common_pb2.User(
                id=user.get('id', 0) or 0,
                username=user.get('username', '') or "",
                email=user.get('email', '') or "",
                password_hash=user.get('password_hash', '') or "",
                first_name=user.get('first_name', '') or "",
                last_name=user.get('last_name', '') or "",
                role=user.get('role', 'USER') or "USER",
                status=user.get('status', 'ACTIVE') or "ACTIVE",
                is_verified=user.get('is_verified', False),
                is_active=user.get('is_active', True),
                phone=user.get('phone', '') or "",
                avatar_url=user.get('avatar_url', '') or "",
                created_at=user.get('created_at', '') or "",
                updated_at=user.get('updated_at', '') or "",
                last_login_at=user.get('last_login_at', '') or ""
            )
        else:
            # User object
            return common_pb2.User(
                id=user.id or 0,
                username=user.username or "",
                email=user.email or "",
                password_hash=user.password_hash or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                role=user.role.name if user.role else "USER",
                status=user.status.name if user.status else "ACTIVE",
                is_verified=user.is_verified if hasattr(user, 'is_verified') else False,
                is_active=user.is_active if hasattr(user, 'is_active') else True,
                phone=user.phone or "",
                avatar_url=user.avatar_url or "",
                created_at=user.created_at.isoformat() if user.created_at else "",
                updated_at=user.updated_at.isoformat() if user.updated_at else "",
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else ""
            )

    def GetUsers(self, request, context):
        """Get users list"""
        try:
            with self.app.app_context():
                service = self._get_user_service()

                # Parse filters
                role = UserRole[request.role.upper()] if request.role else None
                status = UserStatus[request.status.upper()] if request.status else None

                # Get users
                result = service.getUsers(
                    page=request.page or 1,
                    per_page=request.per_page or 20,
                    role=role,
                    status=status
                )

                # Convert to protobuf
                users = [self._user_to_proto(u) for u in result.get('items', [])]
                pagination = common_pb2.PaginationResponse(
                    page=result.get('page', 1),
                    per_page=result.get('per_page', 20),
                    total=result.get('total', 0),
                    total_pages=result.get('total_pages', 0)
                )

                return user_service_pb2.GetUsersResponse(
                    users=users,
                    pagination=pagination
                )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_service_pb2.GetUsersResponse()

    def GetUserById(self, request, context):
        """Get user by ID"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                user = service.getUserById(request.user_id)
                return self._user_to_proto(user)
        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def CreateUser(self, request, context):
        """Create new user"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                user_data = {
                    'username': request.username,
                    'email': request.email,
                    'password': request.password,
                    'first_name': request.first_name,
                    'last_name': request.last_name,
                    'phone': request.phone,
                    'avatar_url': request.avatar_url
                }
                user = service.createUser(**user_data)
                return self._user_to_proto(user)
        except ConflictError as e:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            return common_pb2.User()
        except ValidationError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def UpdateUser(self, request, context):
        """Update user"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                user_data = {}
                if request.username:
                    user_data['username'] = request.username
                if request.email:
                    user_data['email'] = request.email
                if request.first_name:
                    user_data['first_name'] = request.first_name
                if request.last_name:
                    user_data['last_name'] = request.last_name
                if request.phone:
                    user_data['phone'] = request.phone
                if request.avatar_url:
                    user_data['avatar_url'] = request.avatar_url
                if request.role:
                    user_data['role'] = UserRole[request.role.upper()]
                if request.status:
                    user_data['status'] = UserStatus[request.status.upper()]

                user = service.updateUser(request.user_id, **user_data)
                return self._user_to_proto(user)
        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
        except ConflictError as e:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def DeleteUser(self, request, context):
        """Delete user"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                success = service.deleteUser(request.user_id)
                return user_service_pb2.DeleteUserResponse(
                    success=success,
                    message="User deleted successfully"
                )
        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return user_service_pb2.DeleteUserResponse(success=False, message=str(e))
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_service_pb2.DeleteUserResponse(success=False, message=str(e))

    def ChangePassword(self, request, context):
        """Change user password"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                success = service.changePassword(
                    request.user_id,
                    request.old_password,
                    request.new_password
                )
                return user_service_pb2.ChangePasswordResponse(
                    success=success,
                    message="Password changed successfully"
                )
        except AuthenticationError as e:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(str(e))
            return user_service_pb2.ChangePasswordResponse(success=False, message=str(e))
        except ValidationError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return user_service_pb2.ChangePasswordResponse(success=False, message=str(e))
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_service_pb2.ChangePasswordResponse(success=False, message=str(e))

    def VerifyUser(self, request, context):
        """Verify user"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                user = service.verifyUser(request.user_id)
                return self._user_to_proto(user)
        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def UpdateUserStatus(self, request, context):
        """Update user status"""
        try:
            with self.app.app_context():
                service = self._get_user_service()
                status = UserStatus[request.status.upper()]
                user = service.updateUserStatus(request.user_id, status)
                return self._user_to_proto(user)
        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def HealthCheck(self, request, context):
        """Health check"""
        return common_pb2.HealthCheckResponse(status="healthy")


def serve(port=50051):
    """Start gRPC server"""
    import os
    from app import create_app

    # Initialize Flask app to set up database and DI container
    config_name = os.getenv('FLASK_ENV', 'production')
    app = create_app(config_name)

    # Allow port override from environment
    port = int(os.getenv('GRPC_PORT', port))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(app), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"User Service gRPC server started on port {port}")
    return server


if __name__ == '__main__':
    import time
    server = serve()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
