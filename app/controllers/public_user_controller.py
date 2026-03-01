"""
Public User Controller
Public user API controller (no authentication required)
Simplified REST API for user management without authentication
"""
import os
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

from app.schemas.user_schema import PublicUserCreateSchema, PublicUserUpdateSchema
from app.decorators.validation_decorators import validate_schema, validate_pagination
from app.models.user import User
from app.utils.exceptions import APIException, NotFoundError

# Import DI container
from app.di_container import get_service_communication


# Create blueprint for public user API
public_user_bp = Blueprint('public_users', __name__, url_prefix='/api/public/users')


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
        service_comm = get_service_communication()
        page = request.pagination.get('page', 1)
        per_page = request.pagination.get('per_page', 20)  # System default is 20

        # Get users through communication layer
        result = service_comm.get_users(page=page, per_page=per_page)

        # Convert to public API format
        users_data = []
        for user in result.get('items', []):
            if isinstance(user, dict):
                # Already in dict format, extract public fields
                public_user = {
                    'id': user.get('id'),
                    'email': user.get('email'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'avatar': user.get('avatar_url', user.get('avatar'))
                }
            else:
                # It's a User object, use toPublicDict if available
                public_user = user.toPublicDict() if hasattr(user, 'toPublicDict') else user
            users_data.append(public_user)

        return public_api_response(
            data=users_data,
            page=page,
            per_page=per_page,
            total=result.get('total', 0),
            total_pages=result.get('total_pages', 0)
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
        service_comm = get_service_communication()
        user_data = service_comm.get_user_by_id(user_id)

        # Convert to public API format if needed
        if isinstance(user_data, dict) and 'toPublicDict' not in user_data:
            # Already in dict format, extract public fields
            public_data = {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'avatar': user_data.get('avatar_url', user_data.get('avatar'))
            }
        else:
            public_data = user_data

        return public_api_response(data=public_data)

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
        # Replace invalid characters (dots, etc.) with underscores
        username = data['email'].split('@')[0].replace('.', '_')

        # Create user through communication layer
        service_comm = get_service_communication()
        user_data = service_comm.create_user(user_data={
            'username': username,
            'email': data['email'],
            'password': os.environ.get('DEFAULT_USER_PASSWORD', ''),  # Set via DEFAULT_USER_PASSWORD env var
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'avatar_url': data.get('avatar')
        })

        # Convert to public API format if needed
        if isinstance(user_data, dict) and 'toPublicDict' not in user_data:
            public_data = {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'avatar': user_data.get('avatar_url', user_data.get('avatar'))
            }
        else:
            public_data = user_data

        return public_api_response(
            data=public_data,
            createdAt=datetime.now(timezone.utc).isoformat() + 'Z',
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
        service_comm = get_service_communication()

        # Map avatar field if present
        if 'avatar' in data:
            data['avatar_url'] = data.pop('avatar')

        # Remove job field (not stored in our model)
        data.pop('job', None)

        # Update user through communication layer
        user_data = service_comm.update_user(user_id=user_id, user_data=data)

        # Convert to public API format if needed
        if isinstance(user_data, dict) and 'toPublicDict' not in user_data:
            public_data = {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'avatar': user_data.get('avatar_url', user_data.get('avatar'))
            }
        else:
            public_data = user_data

        return public_api_response(
            data=public_data,
            updatedAt=datetime.now(timezone.utc).isoformat() + 'Z'
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
        service_comm = get_service_communication()

        # Delete user through communication layer
        service_comm.delete_user(user_id)

        # Return 204 No Content on successful deletion
        return '', 204

    except NotFoundError:
        return jsonify({}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
