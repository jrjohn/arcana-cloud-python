"""
Authentication Decorators
Authentication decorators - Annotation-based OAuth2 + JWT validation
"""
from functools import wraps
from typing import List, Optional, Callable
from flask import request, g

from app.models.user import User, UserRole
from app.utils.Exceptions import AuthenticationError, AuthorizationError
from app.utils.Response import error_response


def token_required(f: Callable) -> Callable:
    """
    Token validation decorator
    Validates Bearer Token in request and injects user information into g.current_user

    Usage:
        @token_required
        def protected_route():
            user = g.current_user
            return {'message': f'Hello {user.username}'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return error_response(
                message='Missing authorization header',
                status_code=401,
                error_code='MISSING_TOKEN'
            )

        # Validate Bearer token format
        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return error_response(
                    message='Invalid token type. Use Bearer token',
                    status_code=401,
                    error_code='INVALID_TOKEN_TYPE'
                )
        except ValueError:
            return error_response(
                message='Invalid authorization header format',
                status_code=401,
                error_code='INVALID_HEADER_FORMAT'
            )

        # Validate token（使用 AuthService）
        try:
            from app import create_app
            app = create_app()

            with app.app_context():
                from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
                from app.repositories.implementations.OAuthTokenRepositoryImpl import OAuthTokenRepositoryImpl
                from app.services.implementations.AuthServiceImpl import AuthServiceImpl
                from app.Extensions import db

                user_repo = UserRepositoryImpl(db.session)
                token_repo = OAuthTokenRepositoryImpl(db.session)
                auth_service = AuthServiceImpl(user_repo, token_repo)

                user = auth_service.validateToken(token)
                g.current_user = user

        except AuthenticationError as e:
            return error_response(
                message=e.message,
                status_code=e.status_code,
                error_code=e.error_code
            )
        except Exception as e:
            return error_response(
                message='Token validation failed',
                status_code=401,
                error_code='TOKEN_VALIDATION_FAILED',
                details={'error': str(e)}
            )

        return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles: List[UserRole]) -> Callable:
    """
    Role validation decorator
    Verify user角色是否在List of allowed roles中

    Args:
        allowed_roles: List of allowed roles

    Usage:
        @token_required
        @role_required([UserRole.ADMIN, UserRole.USER])
        def admin_route():
            return {'message': 'Admin access granted'}
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 確保已經Validate token
            if not hasattr(g, 'current_user'):
                return error_response(
                    message='Authentication required',
                    status_code=401,
                    error_code='AUTHENTICATION_REQUIRED'
                )

            user: User = g.current_user

            # Check user角色
            if user.role not in allowed_roles:
                return error_response(
                    message=f'Permission denied. Required roles: {[role.value for role in allowed_roles]}',
                    status_code=403,
                    error_code='INSUFFICIENT_PERMISSIONS',
                    details={
                        'user_role': user.role.value,
                        'required_roles': [role.value for role in allowed_roles]
                    }
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def permission_required(permissions: List[str]) -> Callable:
    """
    Permission validation decorator
    Verify user是否擁有指定的權限

    Args:
        permissions: List of required permissions

    Usage:
        @token_required
        @permission_required(['user:read', 'user:write'])
        def user_management_route():
            return {'message': 'User management access granted'}

    Note:
        This decorator requires has_permission() method implementation in User model
        or use independent permission system
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 確保已經Validate token
            if not hasattr(g, 'current_user'):
                return error_response(
                    message='Authentication required',
                    status_code=401,
                    error_code='AUTHENTICATION_REQUIRED'
                )

            user: User = g.current_user

            # Admin has all permissions
            if user.role == UserRole.ADMIN:
                return f(*args, **kwargs)

            # 檢查權限（簡化版本，實際應該從Database或緩存中檢查）
            # Assuming user has a permissions attribute or method
            user_permissions = getattr(user, 'permissions', [])

            missing_permissions = []
            for permission in permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)

            if missing_permissions:
                return error_response(
                    message=f'Missing required permissions: {missing_permissions}',
                    status_code=403,
                    error_code='INSUFFICIENT_PERMISSIONS',
                    details={
                        'required_permissions': permissions,
                        'missing_permissions': missing_permissions
                    }
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def optional_token(f: Callable) -> Callable:
    """
    可選 Token validation decorator
    Validates if request contains token, otherwise continues execution (suitable for public but personalizable endpoints)

    Usage:
        @optional_token
        def public_route():
            if hasattr(g, 'current_user'):
                return {'message': f'Hello {g.current_user.username}'}
            return {'message': 'Hello Guest'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token_type, token = auth_header.split(' ')
                if token_type.lower() == 'bearer':
                    from app import create_app
                    app = create_app()

                    with app.app_context():
                        from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
                        from app.repositories.implementations.OAuthTokenRepositoryImpl import OAuthTokenRepositoryImpl
                        from app.services.implementations.AuthServiceImpl import AuthServiceImpl
                        from app.Extensions import db

                        user_repo = UserRepositoryImpl(db.session)
                        token_repo = OAuthTokenRepositoryImpl(db.session)
                        auth_service = AuthServiceImpl(user_repo, token_repo)

                        user = auth_service.validateToken(token)
                        g.current_user = user
            except Exception:
                # Token Validation failed，繼續執行但不設置 current_user
                pass

        return f(*args, **kwargs)

    return decorated_function
