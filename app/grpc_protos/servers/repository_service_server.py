"""
Repository Service gRPC Server
Implements RepositoryService gRPC interface for Repository Layer
"""
import grpc
from concurrent import futures

from app.grpc_protos import repository_service_pb2, repository_service_pb2_grpc, common_pb2
from app.di_container import get_user_repository
from app.utils.exceptions import NotFoundError, ConflictError, ValidationError
from app.models.user import UserRole, UserStatus


class RepositoryServiceServicer(repository_service_pb2_grpc.RepositoryServiceServicer):
    """gRPC servicer for Repository Service"""

    def __init__(self, app=None):
        self.user_repository = None
        self.app = app

    def _get_user_repository(self):
        """Get user repository from DI container"""
        if not self.user_repository:
            self.user_repository = get_user_repository()
        return self.user_repository

    def _user_to_proto(self, user) -> common_pb2.User:
        """Convert User model to protobuf User message"""
        return common_pb2.User(
            id=user.id or 0,
            username=user.username or "",
            email=user.email or "",
            password_hash=user.password_hash or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            role=user.role.name if user.role else "USER",
            status=user.status.name if user.status else "ACTIVE",
            is_verified=getattr(user, 'is_verified', False),
            is_active=getattr(user, 'is_active', True),
            phone=getattr(user, 'phone', "") or "",
            avatar_url=getattr(user, 'avatar_url', "") or "",
            created_at=user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else "",
            updated_at=user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else "",
            last_login_at=user.last_login_at.isoformat() if hasattr(user, 'last_login_at') and user.last_login_at else ""
        )

    def QueryUsers(self, request, context):
        """Query users with pagination and filters"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()

                # Parse filters
                role = UserRole[request.role.upper()] if request.role else None
                status = UserStatus[request.status.upper()] if request.status else None

                # Query users
                users, total = repository.getAll(
                    page=request.page,
                    per_page=request.per_page,
                    role=role,
                    status=status
                )

                # Convert to proto
                proto_users = [self._user_to_proto(user) for user in users]

                return repository_service_pb2.QueryUsersResponse(
                    users=proto_users,
                    total=total
                )

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return repository_service_pb2.QueryUsersResponse()

    def GetUserById(self, request, context):
        """Get user by ID"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                user = repository.getById(request.user_id)

                if not user:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"User with ID {request.user_id} not found")
                    return common_pb2.User()

                return self._user_to_proto(user)

        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def GetUserByUsername(self, request, context):
        """Get user by username"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                user = repository.getByUsername(request.username)

                if not user:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"User with username '{request.username}' not found")
                    return common_pb2.User()

                return self._user_to_proto(user)

        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return common_pb2.User()

    def GetUserByEmail(self, request, context):
        """Get user by email"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                user = repository.getByEmail(request.email)

                if not user:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"User with email '{request.email}' not found")
                    return common_pb2.User()

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
                repository = self._get_user_repository()

                # Import User model
                from app.models.user import User

                # Parse role and status
                role = UserRole[request.role.upper()] if request.role else UserRole.USER
                status = UserStatus[request.status.upper()] if request.status else UserStatus.ACTIVE

                # Create user object with dummy password, then override password_hash
                user = User(
                    username=request.username,
                    email=request.email,
                    password="",  # Dummy password, will be overridden
                    first_name=request.first_name or None,
                    last_name=request.last_name or None,
                    role=role,
                    status=status,
                    phone=request.phone or None,
                    avatar_url=request.avatar_url or None
                )

                # Override with actual password hash
                user.password_hash = request.password_hash
                user.is_verified = request.is_verified
                user.is_active = request.is_active

                # Save to database
                created_user = repository.create(user)

                return self._user_to_proto(created_user)

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

    @staticmethod
    def _apply_update_fields(user, request) -> None:
        """Apply non-empty request fields onto the user object (S3776 helper)."""
        string_fields = ['username', 'email', 'password_hash', 'first_name',
                         'last_name', 'phone', 'avatar_url']
        for field in string_fields:
            value = getattr(request, field, None)
            if value:
                setattr(user, field, value)
        if request.role:
            user.role = UserRole[request.role.upper()]
        if request.status:
            user.status = UserStatus[request.status.upper()]
        # Boolean fields always carry a value in protobuf3
        user.is_verified = request.is_verified
        user.is_active = request.is_active

    def UpdateUser(self, request, context):
        """Update user"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                user = repository.getById(request.user_id)
                if not user:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"User with ID {request.user_id} not found")
                    return common_pb2.User()

                self._apply_update_fields(user, request)
                updated_user = repository.update(user)
                return self._user_to_proto(updated_user)

        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return common_pb2.User()
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

    def DeleteUser(self, request, context):
        """Delete user"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()

                # Check if user exists
                user = repository.getById(request.user_id)
                if not user:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"User with ID {request.user_id} not found")
                    return repository_service_pb2.DeleteUserRepositoryResponse(success=False)

                # Delete user
                success = repository.delete(request.user_id)

                return repository_service_pb2.DeleteUserRepositoryResponse(success=success)

        except NotFoundError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return repository_service_pb2.DeleteUserRepositoryResponse(success=False)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return repository_service_pb2.DeleteUserRepositoryResponse(success=False)

    def ExistsByUsername(self, request, context):
        """Check if username exists"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                exists = repository.existsByUsername(request.username)

                return repository_service_pb2.ExistsResponse(exists=exists)

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return repository_service_pb2.ExistsResponse(exists=False)

    def ExistsByEmail(self, request, context):
        """Check if email exists"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                exists = repository.existsByEmail(request.email)

                return repository_service_pb2.ExistsResponse(exists=exists)

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return repository_service_pb2.ExistsResponse(exists=False)

    def CountUsers(self, request, context):
        """Count total users"""
        try:
            with self.app.app_context():
                repository = self._get_user_repository()
                # Get all users and count them
                users, total = repository.getAll(page=1, per_page=1)

                return repository_service_pb2.CountResponse(count=total)

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return repository_service_pb2.CountResponse(count=0)

    def HealthCheck(self, request, context):
        """Health check endpoint"""
        return common_pb2.HealthCheckResponse(status="healthy")


def serve(port: int = 50052):
    """Start the gRPC server"""
    import os
    from app import create_app

    # Initialize Flask app to set up database and DI container
    config_name = os.getenv('FLASK_ENV', 'production')
    app = create_app(config_name)

    # Allow port override from environment
    port = int(os.getenv('GRPC_PORT', port))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    repository_service_pb2_grpc.add_RepositoryServiceServicer_to_server(
        RepositoryServiceServicer(app), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Repository Service gRPC Server started on port {port}")
    return server


if __name__ == '__main__':
    import time
    server = serve()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
