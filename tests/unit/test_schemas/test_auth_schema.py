"""
Auth Schema Unit Tests
Tests for app/schemas/auth_schema.py validators
"""
import pytest
from marshmallow import ValidationError


def _get_validate_safe_string():
    """Import the validator function"""
    from app.schemas.auth_schema import validate_safe_string
    return validate_safe_string


class TestValidateSafeString:

    def test_non_empty_safe_string_returns_value(self):
        f = _get_validate_safe_string()
        result = f('hello world')
        assert result == 'hello world'

    def test_empty_string_returns_value(self):
        """Line 14: if not value: return value"""
        f = _get_validate_safe_string()
        result = f('')
        assert result == ''

    def test_none_returns_none(self):
        """Line 14: if not value: return value (None is falsy)"""
        f = _get_validate_safe_string()
        result = f(None)
        assert result is None

    def test_script_tag_raises_validation_error(self):
        """Line 26: raise ValidationError for dangerous pattern"""
        f = _get_validate_safe_string()
        with pytest.raises(ValidationError):
            f('<script>alert("xss")</script>')

    def test_iframe_tag_raises_validation_error(self):
        f = _get_validate_safe_string()
        with pytest.raises(ValidationError):
            f('<iframe src="evil.com"></iframe>')

    def test_javascript_protocol_raises_validation_error(self):
        f = _get_validate_safe_string()
        with pytest.raises(ValidationError):
            f('javascript:alert(1)')

    def test_normal_username_passes(self):
        f = _get_validate_safe_string()
        result = f('john_doe123')
        assert result == 'john_doe123'
