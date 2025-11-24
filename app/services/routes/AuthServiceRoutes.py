"""
Auth Service Layer HTTP API Routes
Exposes AuthService business logic as HTTP/REST endpoints for Controller Layer
"""
from flask import Blueprint, request, jsonify
from typing import Optional

from app.di_container import get_auth_service as get_service_from_container
from app.utils.Exceptions import APIException, NotFoundError, AuthenticationError

# Create blueprint for service layer internal API
auth_service_bp = Blueprint('auth_service', __name__, url_prefix='/internal/auth')


def get_auth_service():
    """Get AuthService instance from DI container"""
    return get_service_from_container()


@auth_service_bp.route('/register', methods=['POST'])
def register():
    """
    Service Layer API: User registration
    ---
    POST /internal/auth/register
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123",
        "first_name": "John",
        "last_name": "Doe"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        auth_service = get_auth_service()

        result = auth_service.register(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone')
        )

        return jsonify({
            'success': True,
            'data': result
        }), 201

    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/login', methods=['POST'])
def login():
    """
    Service Layer API: User login
    ---
    POST /internal/auth/login
    {
        "username_or_email": "john_doe",
        "password": "SecurePass123",
        "client_id": "web-client",
        "client_name": "Web Browser",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0..."
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        auth_service = get_auth_service()

        result = auth_service.login(
            username_or_email=data['username_or_email'],
            password=data['password'],
            client_id=data.get('client_id'),
            client_name=data.get('client_name'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent')
        )

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except AuthenticationError as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/logout', methods=['POST'])
def logout():
    """
    Service Layer API: User logout
    ---
    POST /internal/auth/logout
    {
        "access_token": "<access_token>"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        auth_service = get_auth_service()

        result = auth_service.logout(data['access_token'])

        return jsonify({
            'success': True,
            'data': {'logged_out': result}
        }), 200

    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Service Layer API: Refresh token
    ---
    POST /internal/auth/refresh
    {
        "refresh_token": "<refresh_token>"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        auth_service = get_auth_service()

        result = auth_service.refreshToken(data['refresh_token'])

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except AuthenticationError as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/validate', methods=['POST'])
def validate_token():
    """
    Service Layer API: Validate token
    ---
    POST /internal/auth/validate
    {
        "access_token": "<access_token>"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        auth_service = get_auth_service()

        user = auth_service.validateToken(data['access_token'])

        return jsonify({
            'success': True,
            'data': user.toDict()
        }), 200

    except AuthenticationError as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/tokens/<int:user_id>', methods=['GET'])
def get_user_tokens(user_id: int):
    """
    Service Layer API: Get user tokens
    ---
    GET /internal/auth/tokens/{user_id}

    Called by Controller Layer via ServiceClient
    """
    try:
        auth_service = get_auth_service()
        tokens = auth_service.getUserTokens(user_id)
        token_list = [token.toDict() for token in tokens]

        return jsonify({
            'success': True,
            'data': {'tokens': token_list}
        }), 200

    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/tokens/revoke-all/<int:user_id>', methods=['POST'])
def revoke_all_tokens(user_id: int):
    """
    Service Layer API: Revoke all user tokens
    ---
    POST /internal/auth/tokens/revoke-all/{user_id}

    Called by Controller Layer via ServiceClient
    """
    try:
        auth_service = get_auth_service()
        count = auth_service.revokeAllTokens(user_id)

        return jsonify({
            'success': True,
            'data': {'revoked_count': count}
        }), 200

    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_service_bp.route('/verify-password', methods=['POST'])
def verify_password():
    """
    Service Layer API: Verify password
    ---
    POST /internal/auth/verify-password
    {
        "user_id": 1,
        "password": "SecurePass123"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        auth_service = get_auth_service()

        # Get user first
        from app.di_container import get_user_service
        user_service = get_user_service()
        user = user_service.getUserById(data['user_id'])

        is_valid = auth_service.verifyPassword(user, data['password'])

        return jsonify({
            'success': True,
            'data': {'is_valid': is_valid}
        }), 200

    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
    except APIException as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
