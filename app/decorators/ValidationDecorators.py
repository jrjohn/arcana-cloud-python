"""
Validation Decorators
Validation decorators - Schema-based request validation
"""
from functools import wraps
from typing import Callable, Type
from flask import request
from marshmallow import Schema, ValidationError as MarshmallowValidationError

from app.utils.Exceptions import ValidationError
from app.utils.Response import error_response


def validate_schema(schema_class: Type[Schema], location: str = 'json') -> Callable:
    """
    Schema validation decorator
    Validates request data using Marshmallow Schema

    Args:
        schema_class: Marshmallow Schema 類
        location: Data source location ('json', 'args', 'form')

    Usage:
        from marshmallow import Schema, fields

        class UserCreateSchema(Schema):
            username = fields.Str(required=True)
            email = fields.Email(required=True)
            password = fields.Str(required=True)

        @validate_schema(UserCreateSchema, location='json')
        def create_user():
            # request.validated_data 包含驗證後的數據
            data = request.validated_data
            return {'message': 'User created', 'data': data}
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request data
            if location == 'json':
                data = request.get_json(silent=True)
                if data is None:
                    return error_response(
                        message='Request body must be JSON',
                        status_code=400,
                        error_code='INVALID_JSON'
                    )
            elif location == 'args':
                data = request.args.to_dict()
            elif location == 'form':
                data = request.form.to_dict()
            else:
                return error_response(
                    message=f'Invalid location: {location}',
                    status_code=500,
                    error_code='INTERNAL_ERROR'
                )

            # Validate data
            try:
                schema = schema_class()
                validated_data = schema.load(data)
                request.validated_data = validated_data
            except MarshmallowValidationError as e:
                return error_response(
                    message='Validation failed',
                    status_code=400,
                    error_code='VALIDATION_ERROR',
                    details={'errors': e.messages}
                )
            except Exception as e:
                return error_response(
                    message='Validation failed',
                    status_code=400,
                    error_code='VALIDATION_ERROR',
                    details={'error': str(e)}
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_pagination(max_per_page: int = 100) -> Callable:
    """
    Pagination parameter validation decorator
    Validates page and per_page parameters

    Args:
        max_per_page: Maximum items per page

    Usage:
        @validate_pagination(max_per_page=50)
        def get_users():
            page = request.pagination['page']
            per_page = request.pagination['per_page']
            return {'page': page, 'per_page': per_page}
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 20))

                if page < 1:
                    return error_response(
                        message='Page must be >= 1',
                        status_code=400,
                        error_code='INVALID_PAGINATION'
                    )

                if per_page < 1 or per_page > max_per_page:
                    return error_response(
                        message=f'Per page must be between 1 and {max_per_page}',
                        status_code=400,
                        error_code='INVALID_PAGINATION'
                    )

                request.pagination = {
                    'page': page,
                    'per_page': per_page
                }

            except ValueError:
                return error_response(
                    message='Invalid pagination parameters',
                    status_code=400,
                    error_code='INVALID_PAGINATION'
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
