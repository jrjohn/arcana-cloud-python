"""
Custom Exception Classes
Defines all custom exceptions used in the application
"""
from typing import Optional, Dict, Any


class APIException(Exception):
    """Base API Exception Class"""

    def __init__(
        self,
        message: str = 'An error occurred',
        status_code: int = 500,
        error_code: str = 'INTERNAL_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationError(APIException):
    """Validation Error"""

    def __init__(self, message: str = 'Validation failed', details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code='VALIDATION_ERROR',
            details=details
        )


class AuthenticationError(APIException):
    """Authentication Error"""

    def __init__(self, message: str = 'Authentication failed'):
        super().__init__(
            message=message,
            status_code=401,
            error_code='AUTHENTICATION_ERROR'
        )


class AuthorizationError(APIException):
    """Authorization Error"""

    def __init__(self, message: str = 'Permission denied'):
        super().__init__(
            message=message,
            status_code=403,
            error_code='AUTHORIZATION_ERROR'
        )


class NotFoundError(APIException):
    """Resource Not Found Error"""

    def __init__(self, message: str = 'Resource not found', resource_type: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code='NOT_FOUND',
            details={'resource_type': resource_type} if resource_type else {}
        )


class ConflictError(APIException):
    """Conflict Error (e.g., resource already exists)"""

    def __init__(self, message: str = 'Resource already exists'):
        super().__init__(
            message=message,
            status_code=409,
            error_code='CONFLICT'
        )


class RateLimitError(APIException):
    """Rate Limit Error"""

    def __init__(self, message: str = 'Rate limit exceeded'):
        super().__init__(
            message=message,
            status_code=429,
            error_code='RATE_LIMIT_EXCEEDED'
        )


class ServiceUnavailableError(APIException):
    """Service Unavailable Error"""

    def __init__(self, message: str = 'Service temporarily unavailable'):
        super().__init__(
            message=message,
            status_code=503,
            error_code='SERVICE_UNAVAILABLE'
        )


class DatabaseError(APIException):
    """Database Error"""

    def __init__(self, message: str = 'Database operation failed'):
        super().__init__(
            message=message,
            status_code=500,
            error_code='DATABASE_ERROR'
        )
