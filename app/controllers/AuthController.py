"""
Auth Controller
Authentication API controller
"""
from flask import request, g

from app.controllers import auth_bp
from app.decorators.AuthDecorators import token_required
from app.decorators.ValidationDecorators import validate_schema
from app.schemas.AuthSchema import LoginSchema, RegisterSchema, RefreshTokenSchema
from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
from app.repositories.implementations.OAuthTokenRepositoryImpl import OAuthTokenRepositoryImpl
from app.services.implementations.AuthServiceImpl import AuthServiceImpl
from app.Extensions import db
from app.utils.Response import success_response, error_response
from app.utils.Exceptions import APIException


def get_auth_service() -> AuthServiceImpl:
    """Get AuthService instance"""
    user_repo = UserRepositoryImpl(db.session)
    token_repo = OAuthTokenRepositoryImpl(db.session)
    return AuthServiceImpl(user_repo, token_repo)


@auth_bp.route('/register', methods=['POST'])
@validate_schema(RegisterSchema)
def register():
    """
    User registration
    ---
    POST /api/auth/register
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    try:
        data = request.validated_data
        auth_service = get_auth_service()

        result = auth_service.register(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )

        return success_response(
            data=result,
            message='User registered successfully',
            status_code=201
        )

    except APIException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details
        )
    except Exception as e:
        return error_response(
            message='Registration failed',
            status_code=500,
            error_code='REGISTRATION_FAILED',
            details={'error': str(e)}
        )


@auth_bp.route('/login', methods=['POST'])
@validate_schema(LoginSchema)
def login():
    """
    User login
    ---
    POST /api/auth/login
    {
        "username_or_email": "john_doe",
        "password": "SecurePass123"
    }
    """
    try:
        data = request.validated_data
        auth_service = get_auth_service()

        # Get client information
        client_name = request.headers.get('User-Agent', 'Unknown')
        ip_address = request.remote_addr

        result = auth_service.login(
            username_or_email=data['username_or_email'],
            password=data['password'],
            client_name=client_name,
            ip_address=ip_address,
            user_agent=client_name
        )

        return success_response(
            data=result,
            message='Login successful'
        )

    except APIException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details
        )
    except Exception as e:
        return error_response(
            message='Login failed',
            status_code=500,
            error_code='LOGIN_FAILED',
            details={'error': str(e)}
        )


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """
    User logout
    ---
    POST /api/auth/logout
    Headers: Authorization: Bearer <access_token>
    """
    try:
        # Get token from request header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]

        auth_service = get_auth_service()
        auth_service.logout(token)

        return success_response(
            message='Logout successful'
        )

    except APIException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details
        )
    except Exception as e:
        return error_response(
            message='Logout failed',
            status_code=500,
            error_code='LOGOUT_FAILED',
            details={'error': str(e)}
        )


@auth_bp.route('/refresh', methods=['POST'])
@validate_schema(RefreshTokenSchema)
def refresh_token():
    """
    刷新 Token
    ---
    POST /api/auth/refresh
    {
        "refresh_token": "<refresh_token>"
    }
    """
    try:
        data = request.validated_data
        auth_service = get_auth_service()

        result = auth_service.refreshToken(data['refresh_token'])

        return success_response(
            data=result,
            message='Token refreshed successfully'
        )

    except APIException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details
        )
    except Exception as e:
        return error_response(
            message='Token refresh failed',
            status_code=500,
            error_code='REFRESH_FAILED',
            details={'error': str(e)}
        )


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Get current user information
    ---
    GET /api/auth/me
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user = g.current_user
        return success_response(
            data=user.toDict(),
            message='User info retrieved successfully'
        )

    except Exception as e:
        return error_response(
            message='Failed to get user info',
            status_code=500,
            error_code='GET_USER_FAILED',
            details={'error': str(e)}
        )


@auth_bp.route('/tokens', methods=['GET'])
@token_required
def get_user_tokens():
    """
    Get all valid tokens for current user
    ---
    GET /api/auth/tokens
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user = g.current_user
        auth_service = get_auth_service()

        tokens = auth_service.getUserTokens(user.id)
        token_list = [token.toDict() for token in tokens]

        return success_response(
            data={'tokens': token_list},
            message='Tokens retrieved successfully'
        )

    except Exception as e:
        return error_response(
            message='Failed to get tokens',
            status_code=500,
            error_code='GET_TOKENS_FAILED',
            details={'error': str(e)}
        )


@auth_bp.route('/tokens/revoke-all', methods=['POST'])
@token_required
def revoke_all_tokens():
    """
    Revoke all tokens for current user
    ---
    POST /api/auth/tokens/revoke-all
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user = g.current_user
        auth_service = get_auth_service()

        count = auth_service.revokeAllTokens(user.id)

        return success_response(
            data={'revoked_count': count},
            message=f'Successfully revoked {count} tokens'
        )

    except Exception as e:
        return error_response(
            message='Failed to revoke tokens',
            status_code=500,
            error_code='REVOKE_TOKENS_FAILED',
            details={'error': str(e)}
        )
