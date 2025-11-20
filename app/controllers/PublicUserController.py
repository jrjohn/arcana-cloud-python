"""
Public User Controller
Public user API controller (no authentication required)
Simplified REST API for user management without authentication
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.schemas.UserSchema import PublicUserCreateSchema, PublicUserUpdateSchema
from app.decorators.ValidationDecorators import validate_schema, validate_pagination
from app.models.user import User
from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
from app.services.implementations.UserServiceImpl import UserServiceImpl
from app.Extensions import db
from app.utils.Exceptions import APIException, NotFoundError


# Create blueprint for public user API
public_user_bp = Blueprint('public_users', __name__, url_prefix='/api/public/users')


def get_user_service() -> UserServiceImpl:
    """Get UserService instance"""
    user_repo = UserRepositoryImpl(db.session)
    return UserServiceImpl(user_repo)


def public_api_response(data=None, status_code=200, **kwargs):
    """
    Create public API response

    Args:
        data: Response data
        status_code: HTTP status code
        **kwargs: Additional response fields

    Returns:
        Flask JSON response
    """
    response = {}

    if data is not None:
        response['data'] = data

    # Add any additional fields (like support, pagination, etc.)
    response.update(kwargs)

    return jsonify(response), status_code


@public_user_bp.route('', methods=['GET'])
@validate_pagination()
def list_users():
    """
    List users (Public API)
    ---
    GET /api/public/users?page=1&per_page=6

    Response:
    {
        "page": 1,
        "per_page": 6,
        "total": 12,
        "total_pages": 2,
        "data": [
            {
                "id": 1,
                "email": "janet.weaver@example.com",
                "first_name": "Janet",
                "last_name": "Weaver",
                "avatar": "https://ui-avatars.com/api/?name=Janet&background=007bff&color=fff&size=128"
            }
        ]
    }
    """
    try:
        user_service = get_user_service()
        page = request.pagination.get('page', 1)
        per_page = request.pagination.get('per_page', 6)  # Default is 6

        # Get users directly from repository instead of using service's getUsers
        # to avoid the toDict() conversion
        from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
        from app.Extensions import db
        user_repo = UserRepositoryImpl(db.session)
        users, total = user_repo.getAll(page=page, per_page=per_page)

        # Convert to public API format
        users_data = [user.toPublicDict() for user in users]

        return public_api_response(
            data=users_data,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@public_user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    """
    Get single user (Public API)
    ---
    GET /api/public/users/{id}

    Response:
    {
        "data": {
            "id": 2,
            "email": "janet.weaver@example.com",
            "first_name": "Janet",
            "last_name": "Weaver",
            "avatar": "https://ui-avatars.com/api/?name=Janet&background=007bff&color=fff&size=128"
        }
    }
    """
    try:
        user_service = get_user_service()
        user = user_service.getUserById(user_id)

        return public_api_response(data=user.toPublicDict())

    except NotFoundError:
        return jsonify({}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@public_user_bp.route('', methods=['POST'])
@validate_schema(PublicUserCreateSchema)
def create_user():
    """
    Create user (Public API)
    ---
    POST /api/public/users
    {
        "email": "eve.holt@example.com",
        "first_name": "Eve",
        "last_name": "Holt",
        "avatar": "https://ui-avatars.com/api/?name=Eve&background=007bff&color=fff&size=128",
        "job": "Developer"
    }

    Response:
    {
        "data": {
            "id": 4,
            "email": "eve.holt@example.com",
            "first_name": "Eve",
            "last_name": "Holt",
            "avatar": "https://ui-avatars.com/api/?name=Eve&background=007bff&color=fff&size=128"
        },
        "createdAt": "2024-01-20T12:34:56.789Z"
    }
    """
    try:
        data = request.validated_data

        # Generate default username from email if not provided
        username = data['email'].split('@')[0]

        # Create user with default password (since public API doesn't require it)
        # In a real implementation, you might want to send a password reset email
        user_service = get_user_service()
        user = user_service.createUser(
            username=username,
            email=data['email'],
            password='DefaultPass123',  # Default password for public API
            first_name=data['first_name'],
            last_name=data['last_name'],
            avatar_url=data.get('avatar')
        )

        return public_api_response(
            data=user.toPublicDict(),
            createdAt=datetime.utcnow().isoformat() + 'Z',
            status_code=201
        )

    except APIException as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@public_user_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
@validate_schema(PublicUserUpdateSchema)
def update_user(user_id: int):
    """
    Update user (Public API)
    ---
    PUT /api/public/users/{id}
    PATCH /api/public/users/{id}
    {
        "email": "eve.holt@example.com",
        "first_name": "Eve",
        "last_name": "Holt",
        "job": "Senior Developer"
    }

    Response:
    {
        "data": {
            "id": 4,
            "email": "eve.holt@example.com",
            "first_name": "Eve",
            "last_name": "Holt",
            "avatar": "https://ui-avatars.com/api/?name=Eve&background=007bff&color=fff&size=128"
        },
        "updatedAt": "2024-01-20T12:34:56.789Z"
    }
    """
    try:
        data = request.validated_data
        user_service = get_user_service()

        # Map avatar field if present
        if 'avatar' in data:
            data['avatar_url'] = data.pop('avatar')

        # Remove job field (not stored in our model)
        data.pop('job', None)

        # Actually update the user in the database
        user = user_service.updateUser(user_id, **data)

        return public_api_response(
            data=user.toPublicDict(),
            updatedAt=datetime.utcnow().isoformat() + 'Z'
        )

    except NotFoundError:
        return jsonify({}), 404
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@public_user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    """
    Delete user (Public API)
    ---
    DELETE /api/public/users/{id}

    Response: 204 No Content
    """
    try:
        user_service = get_user_service()

        # Actually delete the user from the database
        user_service.deleteUser(user_id)

        # Return 204 No Content on successful deletion
        return '', 204

    except NotFoundError:
        return jsonify({}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
