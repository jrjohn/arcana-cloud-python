"""
Standardized API Response Format
Unifies the response format for all API endpoints
"""
from datetime import datetime, timezone
from typing import Any, Optional, Dict
from uuid import uuid4
from flask import jsonify, Response, g


def success_response(
    data: Any = None,
    message: str = 'Success',
    status_code: int = 200
) -> tuple[Response, int]:
    """
    Success response format

    Args:
        data: Response data
        message: Response message
        status_code: HTTP status code

    Returns:
        (Response object, status code)
    """
    response_data = {
        'success': True,
        'data': data,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'request_id': get_request_id()
    }

    return jsonify(response_data), status_code


def error_response(
    message: str = 'An error occurred',
    status_code: int = 500,
    error_code: str = 'INTERNAL_ERROR',
    details: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Error response format

    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Error code
        details: Detailed error information

    Returns:
        (Response object, status code)
    """
    response_data = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message,
            'details': details or {}
        },
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'request_id': get_request_id()
    }

    return jsonify(response_data), status_code


def paginated_response(
    items: list,
    page: int,
    per_page: int,
    total: int,
    message: str = 'Success'
) -> tuple[Response, int]:
    """
    Paginated response format

    Args:
        items: Paginated data list
        page: Current page number
        per_page: Items per page
        total: Total count
        message: Response message

    Returns:
        (Response object, status code)
    """
    response_data = {
        'success': True,
        'data': {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        },
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'request_id': get_request_id()
    }

    return jsonify(response_data), 200


def get_request_id() -> str:
    """
    Get current request ID

    Returns:
        Request ID
    """
    if hasattr(g, 'request_id'):
        return g.request_id
    return str(uuid4())
