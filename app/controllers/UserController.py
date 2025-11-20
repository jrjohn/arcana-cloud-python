"""
User Controller
User management API controller
"""
from flask import request, g

from app.controllers import user_bp
from app.decorators.AuthDecorators import token_required, role_required
from app.decorators.ValidationDecorators import validate_schema, validate_pagination
from app.schemas.UserSchema import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    ChangePasswordSchema
)
from app.models.User import UserRole, UserStatus
from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
from app.services.implementations.UserServiceImpl import UserServiceImpl
from app.Extensions import db
from app.utils.Response import success_response, error_response, paginated_response
from app.utils.Exceptions import APIException


def get_user_service() -> UserServiceImpl:
    """Get UserService instance"""
    user_repo = UserRepositoryImpl(db.session)
    return UserServiceImpl(user_repo)


@user_bp.route('', methods=['GET'])
@token_required
@role_required([UserRole.ADMIN])
@validate_pagination()
def get_users():
    """
    Get user列表（管理員）
    ---
    GET /api/users?page=1&per_page=20&role=user&status=active
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user_service = get_user_service()
        page = request.pagination['page']
        per_page = request.pagination['per_page']

        # Optional filter conditions
        role_str = request.args.get('role')
        status_str = request.args.get('status')

        role = UserRole[role_str.upper()] if role_str else None
        status = UserStatus[status_str.upper()] if status_str else None

        result = user_service.getUsers(
            page=page,
            per_page=per_page,
            role=role,
            status=status
        )

        return paginated_response(
            items=result['items'],
            page=result['pagination']['page'],
            per_page=result['pagination']['per_page'],
            total=result['pagination']['total'],
            message='Users retrieved successfully'
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
            message='Failed to get users',
            status_code=500,
            error_code='GET_USERS_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id: int):
    """
    Get user詳情
    ---
    GET /api/users/{user_id}
    Headers: Authorization: Bearer <access_token>
    """
    try:
        current_user = g.current_user

        # Can only view own information or admin can view everyone
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            return error_response(
                message='Permission denied',
                status_code=403,
                error_code='PERMISSION_DENIED'
            )

        user_service = get_user_service()
        user = user_service.getUserById(user_id)

        return success_response(
            data=user.toDict(),
            message='User retrieved successfully'
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
            message='Failed to get user',
            status_code=500,
            error_code='GET_USER_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('', methods=['POST'])
@token_required
@role_required([UserRole.ADMIN])
@validate_schema(UserCreateSchema)
def create_user():
    """
    Create user（管理員）
    ---
    POST /api/users
    Headers: Authorization: Bearer <access_token>
    {
        "username": "jane_doe",
        "email": "jane@example.com",
        "password": "SecurePass123",
        "first_name": "Jane",
        "last_name": "Doe"
    }
    """
    try:
        data = request.validated_data
        user_service = get_user_service()

        user = user_service.createUser(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone')
        )

        return success_response(
            data=user.toDict(),
            message='User created successfully',
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
            message='Failed to create user',
            status_code=500,
            error_code='CREATE_USER_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@validate_schema(UserUpdateSchema)
def update_user(user_id: int):
    """
    Update user信息
    ---
    PUT /api/users/{user_id}
    Headers: Authorization: Bearer <access_token>
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "+1234567890"
    }
    """
    try:
        current_user = g.current_user

        # Can only update own information or admin can update everyone
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            return error_response(
                message='Permission denied',
                status_code=403,
                error_code='PERMISSION_DENIED'
            )

        data = request.validated_data
        user_service = get_user_service()

        user = user_service.updateUser(user_id, **data)

        return success_response(
            data=user.toDict(),
            message='User updated successfully'
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
            message='Failed to update user',
            status_code=500,
            error_code='UPDATE_USER_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@role_required([UserRole.ADMIN])
def delete_user(user_id: int):
    """
    Delete user（管理員）
    ---
    DELETE /api/users/{user_id}
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user_service = get_user_service()
        user_service.deleteUser(user_id)

        return success_response(
            message='User deleted successfully'
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
            message='Failed to delete user',
            status_code=500,
            error_code='DELETE_USER_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('/<int:user_id>/password', methods=['PUT'])
@token_required
@validate_schema(ChangePasswordSchema)
def change_password(user_id: int):
    """
    修改Password
    ---
    PUT /api/users/{user_id}/password
    Headers: Authorization: Bearer <access_token>
    {
        "old_password": "OldPass123",
        "new_password": "NewPass123"
    }
    """
    try:
        current_user = g.current_user

        # 只能修改自己的Password
        if current_user.id != user_id:
            return error_response(
                message='Permission denied',
                status_code=403,
                error_code='PERMISSION_DENIED'
            )

        data = request.validated_data
        user_service = get_user_service()

        user_service.changePassword(
            user_id=user_id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )

        return success_response(
            message='Password changed successfully'
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
            message='Failed to change password',
            status_code=500,
            error_code='CHANGE_PASSWORD_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('/<int:user_id>/verify', methods=['POST'])
@token_required
@role_required([UserRole.ADMIN])
def verify_user(user_id: int):
    """
    Verify user（管理員）
    ---
    POST /api/users/{user_id}/verify
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user_service = get_user_service()
        user = user_service.verifyUser(user_id)

        return success_response(
            data=user.toDict(),
            message='User verified successfully'
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
            message='Failed to verify user',
            status_code=500,
            error_code='VERIFY_USER_FAILED',
            details={'error': str(e)}
        )


@user_bp.route('/<int:user_id>/status', methods=['PUT'])
@token_required
@role_required([UserRole.ADMIN])
def update_user_status(user_id: int):
    """
    Update user狀態（管理員）
    ---
    PUT /api/users/{user_id}/status
    Headers: Authorization: Bearer <access_token>
    {
        "status": "suspended"
    }
    """
    try:
        data = request.get_json()
        status_str = data.get('status')

        if not status_str:
            return error_response(
                message='Status is required',
                status_code=400,
                error_code='VALIDATION_ERROR'
            )

        try:
            status = UserStatus[status_str.upper()]
        except KeyError:
            return error_response(
                message=f'Invalid status: {status_str}',
                status_code=400,
                error_code='VALIDATION_ERROR'
            )

        user_service = get_user_service()
        user = user_service.updateUserStatus(user_id, status)

        return success_response(
            data=user.toDict(),
            message='User status updated successfully'
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
            message='Failed to update user status',
            status_code=500,
            error_code='UPDATE_STATUS_FAILED',
            details={'error': str(e)}
        )
