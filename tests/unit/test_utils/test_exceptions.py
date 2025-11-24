"""
Custom Exceptions Unit Tests
Tests for custom exception classes
"""
import pytest

from app.utils.exceptions import (
    APIException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServiceUnavailableError,
    DatabaseError
)


class TestAPIException:
    """Test base APIException class"""

    def test_api_exception_default(self):
        """Test APIException with default values"""
        # Act
        exc = APIException()

        # Assert
        assert exc.message == 'An error occurred'
        assert exc.status_code == 500
        assert exc.error_code == 'INTERNAL_ERROR'
        assert exc.details == {}

    def test_api_exception_custom(self):
        """Test APIException with custom values"""
        # Act
        exc = APIException(
            message='Custom error',
            status_code=418,
            error_code='CUSTOM_ERROR',
            details={'key': 'value'}
        )

        # Assert
        assert exc.message == 'Custom error'
        assert exc.status_code == 418
        assert exc.error_code == 'CUSTOM_ERROR'
        assert exc.details == {'key': 'value'}

    def test_api_exception_str(self):
        """Test string representation of APIException"""
        # Arrange
        exc = APIException(message='Test error')

        # Act
        result = str(exc)

        # Assert
        assert 'Test error' in result


class TestValidationError:
    """Test ValidationError class"""

    def test_validation_error_default(self):
        """Test ValidationError with default message"""
        # Act
        exc = ValidationError()

        # Assert
        assert exc.message == 'Validation failed'
        assert exc.status_code == 400
        assert exc.error_code == 'VALIDATION_ERROR'

    def test_validation_error_custom_message(self):
        """Test ValidationError with custom message"""
        # Act
        exc = ValidationError(message='Invalid email format')

        # Assert
        assert exc.message == 'Invalid email format'
        assert exc.status_code == 400

    def test_validation_error_with_details(self):
        """Test ValidationError with details"""
        # Act
        exc = ValidationError(
            message='Validation failed',
            details={'email': 'Invalid format', 'password': 'Too short'}
        )

        # Assert
        assert exc.details == {'email': 'Invalid format', 'password': 'Too short'}


class TestAuthenticationError:
    """Test AuthenticationError class"""

    def test_authentication_error_default(self):
        """Test AuthenticationError with default message"""
        # Act
        exc = AuthenticationError()

        # Assert
        assert exc.message == 'Authentication failed'
        assert exc.status_code == 401
        assert exc.error_code == 'AUTHENTICATION_ERROR'

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message"""
        # Act
        exc = AuthenticationError(message='Invalid credentials')

        # Assert
        assert exc.message == 'Invalid credentials'
        assert exc.status_code == 401


class TestAuthorizationError:
    """Test AuthorizationError class"""

    def test_authorization_error_default(self):
        """Test AuthorizationError with default message"""
        # Act
        exc = AuthorizationError()

        # Assert
        assert exc.message == 'Permission denied'
        assert exc.status_code == 403
        assert exc.error_code == 'AUTHORIZATION_ERROR'

    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message"""
        # Act
        exc = AuthorizationError(message='Insufficient permissions')

        # Assert
        assert exc.message == 'Insufficient permissions'
        assert exc.status_code == 403


class TestNotFoundError:
    """Test NotFoundError class"""

    def test_not_found_error_default(self):
        """Test NotFoundError with default message"""
        # Act
        exc = NotFoundError()

        # Assert
        assert exc.message == 'Resource not found'
        assert exc.status_code == 404
        assert exc.error_code == 'NOT_FOUND'

    def test_not_found_error_custom_message(self):
        """Test NotFoundError with custom message"""
        # Act
        exc = NotFoundError(message='User not found')

        # Assert
        assert exc.message == 'User not found'

    def test_not_found_error_with_resource_type(self):
        """Test NotFoundError with resource type"""
        # Act
        exc = NotFoundError(message='User not found', resource_type='User')

        # Assert
        assert exc.details == {'resource_type': 'User'}


class TestConflictError:
    """Test ConflictError class"""

    def test_conflict_error_default(self):
        """Test ConflictError with default message"""
        # Act
        exc = ConflictError()

        # Assert
        assert exc.message == 'Resource already exists'
        assert exc.status_code == 409
        assert exc.error_code == 'CONFLICT'

    def test_conflict_error_custom_message(self):
        """Test ConflictError with custom message"""
        # Act
        exc = ConflictError(message='Username already exists')

        # Assert
        assert exc.message == 'Username already exists'


class TestRateLimitError:
    """Test RateLimitError class"""

    def test_rate_limit_error_default(self):
        """Test RateLimitError with default message"""
        # Act
        exc = RateLimitError()

        # Assert
        assert exc.message == 'Rate limit exceeded'
        assert exc.status_code == 429
        assert exc.error_code == 'RATE_LIMIT_EXCEEDED'

    def test_rate_limit_error_custom_message(self):
        """Test RateLimitError with custom message"""
        # Act
        exc = RateLimitError(message='Too many requests')

        # Assert
        assert exc.message == 'Too many requests'


class TestServiceUnavailableError:
    """Test ServiceUnavailableError class"""

    def test_service_unavailable_error_default(self):
        """Test ServiceUnavailableError with default message"""
        # Act
        exc = ServiceUnavailableError()

        # Assert
        assert exc.message == 'Service temporarily unavailable'
        assert exc.status_code == 503
        assert exc.error_code == 'SERVICE_UNAVAILABLE'

    def test_service_unavailable_error_custom_message(self):
        """Test ServiceUnavailableError with custom message"""
        # Act
        exc = ServiceUnavailableError(message='Database is down')

        # Assert
        assert exc.message == 'Database is down'


class TestDatabaseError:
    """Test DatabaseError class"""

    def test_database_error_default(self):
        """Test DatabaseError with default message"""
        # Act
        exc = DatabaseError()

        # Assert
        assert exc.message == 'Database operation failed'
        assert exc.status_code == 500
        assert exc.error_code == 'DATABASE_ERROR'

    def test_database_error_custom_message(self):
        """Test DatabaseError with custom message"""
        # Act
        exc = DatabaseError(message='Connection timeout')

        # Assert
        assert exc.message == 'Connection timeout'


class TestExceptionInheritance:
    """Test exception inheritance"""

    def test_all_exceptions_inherit_from_api_exception(self):
        """Test that all custom exceptions inherit from APIException"""
        # Assert
        assert issubclass(ValidationError, APIException)
        assert issubclass(AuthenticationError, APIException)
        assert issubclass(AuthorizationError, APIException)
        assert issubclass(NotFoundError, APIException)
        assert issubclass(ConflictError, APIException)
        assert issubclass(RateLimitError, APIException)
        assert issubclass(ServiceUnavailableError, APIException)
        assert issubclass(DatabaseError, APIException)

    def test_all_exceptions_inherit_from_base_exception(self):
        """Test that all exceptions inherit from base Exception"""
        # Assert
        assert issubclass(APIException, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(AuthenticationError, Exception)


class TestExceptionRaising:
    """Test raising exceptions"""

    def test_raise_validation_error(self):
        """Test raising ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(message='Test validation error')

        assert exc_info.value.message == 'Test validation error'

    def test_raise_authentication_error(self):
        """Test raising AuthenticationError"""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError(message='Test auth error')

        assert exc_info.value.message == 'Test auth error'

    def test_catch_as_api_exception(self):
        """Test catching specific exception as APIException"""
        with pytest.raises(APIException):
            raise ValidationError(message='Test error')

    def test_catch_as_base_exception(self):
        """Test catching as base Exception"""
        with pytest.raises(Exception):
            raise ValidationError(message='Test error')
