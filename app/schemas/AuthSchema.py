"""
Auth Schemas
Authentication data serialization schemas
"""
from marshmallow import Schema, fields, validate, ValidationError
import re


def validate_safe_string(value):
    """
    Validate that string doesn't contain HTML/script tags or other dangerous characters
    """
    if not value:
        return value

    # Check for HTML tags, script tags, or SQL injection patterns
    dangerous_patterns = [
        r'<\s*script', r'<\s*\/\s*script',  # Script tags
        r'<\s*iframe', r'<\s*\/\s*iframe',  # Iframe tags
        r'javascript:', r'onerror\s*=', r'onload\s*=',  # Event handlers
        r'<\s*img', r'<\s*embed', r'<\s*object',  # Other potentially dangerous tags
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError('Invalid characters detected in input')

    return value


class LoginSchema(Schema):
    """Login schema"""
    username_or_email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class RegisterSchema(Schema):
    """Registration schema"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=80),
            validate_safe_string
        ]
    )
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True
    )
    first_name = fields.Str(
        validate=[
            validate.Length(max=50),
            validate_safe_string
        ],
        allow_none=True
    )
    last_name = fields.Str(
        validate=[
            validate.Length(max=50),
            validate_safe_string
        ],
        allow_none=True
    )


class RefreshTokenSchema(Schema):
    """Refresh token schema"""
    refresh_token = fields.Str(required=True)
