"""
User Controller
User management API controller with abstract communication layer
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
from app.models.user import UserRole, UserStatus
from app.utils.Response import success_response, error_response, paginated_response
from app.utils.Exceptions import APIException

# Import DI container
from app.di_container import get_service_communication


@user_bp.route('', methods=['GET'])
@token_required
@role_required([UserRole.ADMIN])
@validate_pagination()
def get_users():
    """
    Get user list (Admin only)
    ---
    GET /api/v1/users?page=1&per_page=20&role=user&status=active
    Headers: Authorization: Bearer <access_token>
    """
    try:
        service_comm = get_service_communication()
        page = request.pagination['page']
        per_page = request.pagination['per_page']

        # Optional filter conditions
        role_str = request.args.get('role')
        status_str = request.args.get('status')

        filters = {}
        if role_str:
            try:
                filters['role'] = UserRole[role_str.upper()]
            except KeyError:
                valid_roles = [r.name for r in UserRole]
                return error_response(
                    message=f'Invalid role: {role_str}',
                    status_code=400,
                    error_code='INVALID_ROLE',
                    details={'valid_roles': valid_roles}
                )
        if status_str:
            try:
                filters['status'] = UserStatus[status_str.upper()]
            except KeyError:
                valid_statuses = [s.name for s in UserStatus]
                return error_response(
                    message=f'Invalid status: {status_str}',
                    status_code=400,
                    error_code='INVALID_STATUS',
                    details={'valid_statuses': valid_statuses}
                )

        # Call via communication layer (Direct/HTTP/gRPC based on mode)
        result = service_comm.get_users(
            page=page,
            per_page=per_page,
            **filters
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
    Get user details
    ---
    GET /api/v1/users/{user_id}
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

        service_comm = get_service_communication()

        # Call via communication layer
        user_data = service_comm.get_user_by_id(user_id)

        return success_response(
            data=user_data,
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
    Create user (Admin only)
    ---
    POST /api/v1/users
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
        service_comm = get_service_communication()

        # Call via communication layer
        user_data = service_comm.create_user(user_data=data)

        return success_response(
            data=user_data,
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
    Update user information
    ---
    PUT /api/v1/users/{user_id}
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
        service_comm = get_service_communication()

        # Call via communication layer
        user_data = service_comm.update_user(user_id=user_id, user_data=data)

        return success_response(
            data=user_data,
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
    Delete user (Admin only)
    ---
    DELETE /api/v1/users/{user_id}
    Headers: Authorization: Bearer <access_token>
    """
    try:
        service_comm = get_service_communication()

        # Call via communication layer
        service_comm.delete_user(user_id=user_id)

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
    Change password
    ---
    PUT /api/v1/users/{user_id}/password
    Headers: Authorization: Bearer <access_token>
    {
        "old_password": "OldPass123",
        "new_password": "NewPass123"
    }
    """
    try:
        current_user = g.current_user

        # Can only change own password
        if current_user.id != user_id:
            return error_response(
                message='Permission denied',
                status_code=403,
                error_code='PERMISSION_DENIED'
            )

        data = request.validated_data
        service_comm = get_service_communication()

        # Call specific method via communication layer
        result = service_comm.change_password(
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
    Verify user (Admin only)
    ---
    POST /api/v1/users/{user_id}/verify
    Headers: Authorization: Bearer <access_token>
    """
    try:
        service_comm = get_service_communication()

        # Call specific method via communication layer
        user_data = service_comm.verify_user(user_id=user_id)

        return success_response(
            data=user_data,
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
    Update user status (Admin only)
    ---
    PUT /api/v1/users/{user_id}/status
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

        service_comm = get_service_communication()

        # Call specific method via communication layer
        user_data = service_comm.update_user_status(
            user_id=user_id,
            status=status.name
        )

        return success_response(
            data=user_data,
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
