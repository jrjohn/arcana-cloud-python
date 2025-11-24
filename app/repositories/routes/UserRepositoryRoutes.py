"""
User Repository Layer HTTP API Routes
Exposes UserRepository data access as HTTP/REST endpoints for Service Layer (microservices mode)
"""
from flask import Blueprint, request, jsonify
from typing import Optional

from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
from app.Extensions import db
from app.models.user import User, UserRole, UserStatus
from app.utils.Exceptions import APIException, NotFoundError, DatabaseError

# Create blueprint for repository layer internal API
user_repository_bp = Blueprint('user_repository', __name__, url_prefix='/repository/users')


def get_user_repository() -> UserRepositoryImpl:
    """Get UserRepository instance"""
    return UserRepositoryImpl(db.session)


def serialize_user(user: User) -> dict:
    """Serialize User object to dict"""
    if user is None:
        return None
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role.name if user.role else None,
        'status': user.status.name if user.status else None,
        'password_hash': user.password_hash,  # Needed for Service Layer password verification
        'is_verified': user.is_verified if hasattr(user, 'is_verified') else False,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None
    }


@user_repository_bp.route('', methods=['GET'])
def get_all_users():
    """
    Repository Layer API: Get all users (paginated)
    ---
    GET /repository/users?page=1&per_page=20&role=USER&status=ACTIVE

    Called by Service Layer via RepositoryClient in microservices mode
    """
    try:
        user_repo = get_user_repository()

        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        role_str = request.args.get('role')
        status_str = request.args.get('status')

        # Parse role
        role = None
        if role_str:
            try:
                role = UserRole[role_str.upper()]
            except KeyError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid role: {role_str}'
                }), 400

        # Parse status
        status = None
        if status_str:
            try:
                status = UserStatus[status_str.upper()]
            except KeyError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid status: {status_str}'
                }), 400

        users, total = user_repo.getAll(
            page=page,
            per_page=per_page,
            role=role,
            status=status
        )

        return jsonify({
            'success': True,
            'data': {
                'users': [serialize_user(u) for u in users],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id: int):
    """
    Repository Layer API: Get user by ID
    ---
    GET /repository/users/{user_id}
    """
    try:
        user_repo = get_user_repository()
        user = user_repo.getById(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': f'User with ID {user_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'data': serialize_user(user)
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/username/<string:username>', methods=['GET'])
def get_user_by_username(username: str):
    """
    Repository Layer API: Get user by username
    ---
    GET /repository/users/username/{username}
    """
    try:
        user_repo = get_user_repository()
        user = user_repo.getByUsername(username)

        if not user:
            return jsonify({
                'success': False,
                'error': f'User with username {username} not found'
            }), 404

        return jsonify({
            'success': True,
            'data': serialize_user(user)
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/email/<string:email>', methods=['GET'])
def get_user_by_email(email: str):
    """
    Repository Layer API: Get user by email
    ---
    GET /repository/users/email/{email}
    """
    try:
        user_repo = get_user_repository()
        user = user_repo.getByEmail(email)

        if not user:
            return jsonify({
                'success': False,
                'error': f'User with email {email} not found'
            }), 404

        return jsonify({
            'success': True,
            'data': serialize_user(user)
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('', methods=['POST'])
def create_user():
    """
    Repository Layer API: Create user
    ---
    POST /repository/users
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password_hash": "hashed_password",
        "first_name": "John",
        "last_name": "Doe",
        "role": "USER",
        "status": "ACTIVE"
    }
    """
    try:
        data = request.get_json()
        user_repo = get_user_repository()

        # Create User object with dummy password (will be replaced with actual hash)
        user = User(
            username=data['username'],
            email=data['email'],
            password='DUMMY_PASSWORD_WILL_BE_REPLACED'
        )

        # Set password_hash if provided (from service layer that already hashed it)
        if 'password_hash' in data:
            user.password_hash = data['password_hash']

        # Set other optional fields
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.role = UserRole[data['role'].upper()] if 'role' in data else UserRole.USER
        user.status = UserStatus[data['status'].upper()] if 'status' in data else UserStatus.ACTIVE

        created_user = user_repo.create(user)

        return jsonify({
            'success': True,
            'data': serialize_user(created_user)
        }), 201

    except KeyError as e:
        return jsonify({
            'success': False,
            'error': f'Missing required field: {str(e)}'
        }), 400
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id: int):
    """
    Repository Layer API: Update user
    ---
    PUT /repository/users/{user_id}
    {
        "first_name": "Updated Name",
        "email": "updated@example.com"
    }
    """
    try:
        data = request.get_json()
        user_repo = get_user_repository()

        # Get existing user
        user = user_repo.getById(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': f'User with ID {user_id} not found'
            }), 404

        # Update fields
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'role' in data:
            user.role = UserRole[data['role'].upper()]
        if 'status' in data:
            user.status = UserStatus[data['status'].upper()]
        if 'password_hash' in data:
            user.password_hash = data['password_hash']
        if 'is_verified' in data:
            user.is_verified = data['is_verified']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'phone' in data:
            user.phone = data['phone']
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']

        updated_user = user_repo.update(user)

        return jsonify({
            'success': True,
            'data': serialize_user(updated_user)
        }), 200

    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    """
    Repository Layer API: Delete user
    ---
    DELETE /repository/users/{user_id}
    """
    try:
        user_repo = get_user_repository()
        success = user_repo.delete(user_id)

        return jsonify({
            'success': True,
            'data': {'deleted': success}
        }), 200

    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/exists/username/<string:username>', methods=['GET'])
def check_username_exists(username: str):
    """
    Repository Layer API: Check if username exists
    ---
    GET /repository/users/exists/username/{username}
    """
    try:
        user_repo = get_user_repository()
        exists = user_repo.existsByUsername(username)

        return jsonify({
            'success': True,
            'data': {'exists': exists}
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/exists/email/<string:email>', methods=['GET'])
def check_email_exists(email: str):
    """
    Repository Layer API: Check if email exists
    ---
    GET /repository/users/exists/email/{email}
    """
    try:
        user_repo = get_user_repository()
        exists = user_repo.existsByEmail(email)

        return jsonify({
            'success': True,
            'data': {'exists': exists}
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_repository_bp.route('/count', methods=['GET'])
def get_user_count():
    """
    Repository Layer API: Get total user count
    ---
    GET /repository/users/count
    """
    try:
        user_repo = get_user_repository()
        count = user_repo.count()

        return jsonify({
            'success': True,
            'data': {'count': count}
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
