"""
User Service Layer HTTP API Routes
Exposes UserService business logic as HTTP/REST endpoints for Controller Layer
"""
from flask import Blueprint, request, jsonify
from typing import Optional

from app.di_container import get_user_service as get_service_from_container
from app.models.user import UserRole, UserStatus
from app.utils.Exceptions import APIException, NotFoundError

# Create blueprint for service layer internal API
user_service_bp = Blueprint('user_service', __name__, url_prefix='/internal/users')


def get_user_service():
    """Get UserService instance from DI container"""
    return get_service_from_container()


@user_service_bp.route('', methods=['GET'])
def list_users():
    """
    Service Layer API: List users
    ---
    GET /internal/users?page=1&per_page=20&role=user&status=active

    Called by Controller Layer via ServiceClient
    """
    try:
        user_service = get_user_service()

        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        role_str = request.args.get('role')
        status_str = request.args.get('status')

        # Parse role with proper error handling
        role = None
        if role_str:
            try:
                role = UserRole[role_str.upper()]
            except KeyError:
                valid_roles = [r.name for r in UserRole]
                return jsonify({
                    'success': False,
                    'error': f'Invalid role: {role_str}. Valid roles: {", ".join(valid_roles)}',
                    'error_code': 'INVALID_ROLE'
                }), 400

        # Parse status with proper error handling
        status = None
        if status_str:
            try:
                status = UserStatus[status_str.upper()]
            except KeyError:
                valid_statuses = [s.name for s in UserStatus]
                return jsonify({
                    'success': False,
                    'error': f'Invalid status: {status_str}. Valid statuses: {", ".join(valid_statuses)}',
                    'error_code': 'INVALID_STATUS'
                }), 400

        result = user_service.getUsers(
            page=page,
            per_page=per_page,
            role=role,
            status=status
        )

        return jsonify({
            'success': True,
            'data': result
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


@user_service_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    """
    Service Layer API: Get single user
    ---
    GET /internal/users/{user_id}

    Called by Controller Layer via ServiceClient
    """
    try:
        user_service = get_user_service()
        user = user_service.getUserById(user_id)

        return jsonify({
            'success': True,
            'data': user.toDict()
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


@user_service_bp.route('', methods=['POST'])
def create_user():
    """
    Service Layer API: Create user
    ---
    POST /internal/users
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
        user_service = get_user_service()

        user = user_service.createUser(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone')
        )

        return jsonify({
            'success': True,
            'data': user.toDict()
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


@user_service_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id: int):
    """
    Service Layer API: Update user
    ---
    PUT /internal/users/{user_id}
    {
        "first_name": "Jane",
        "last_name": "Smith"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        user_service = get_user_service()

        user = user_service.updateUser(user_id, **data)

        return jsonify({
            'success': True,
            'data': user.toDict()
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


@user_service_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    """
    Service Layer API: Delete user
    ---
    DELETE /internal/users/{user_id}

    Called by Controller Layer via ServiceClient
    """
    try:
        user_service = get_user_service()
        user_service.deleteUser(user_id)

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
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


@user_service_bp.route('/<int:user_id>/password', methods=['PUT'])
def change_password(user_id: int):
    """
    Service Layer API: Change password
    ---
    PUT /internal/users/{user_id}/password
    {
        "old_password": "OldPass123",
        "new_password": "NewPass123"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        user_service = get_user_service()

        user_service.changePassword(
            user_id=user_id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
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


@user_service_bp.route('/<int:user_id>/verify', methods=['POST'])
def verify_user(user_id: int):
    """
    Service Layer API: Verify user
    ---
    POST /internal/users/{user_id}/verify

    Called by Controller Layer via ServiceClient
    """
    try:
        user_service = get_user_service()
        user = user_service.verifyUser(user_id)

        return jsonify({
            'success': True,
            'data': user.toDict()
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


@user_service_bp.route('/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id: int):
    """
    Service Layer API: Update user status
    ---
    PUT /internal/users/{user_id}/status
    {
        "status": "suspended"
    }

    Called by Controller Layer via ServiceClient
    """
    try:
        data = request.get_json()
        status_str = data.get('status')

        if not status_str:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400

        try:
            status = UserStatus[status_str.upper()]
        except KeyError:
            return jsonify({
                'success': False,
                'error': f'Invalid status: {status_str}'
            }), 400

        user_service = get_user_service()
        user = user_service.updateUserStatus(user_id, status)

        return jsonify({
            'success': True,
            'data': user.toDict()
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
