"""
Auth Schemas
Authentication data serialization schemas
"""
from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    """Login schema"""
    username_or_email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class RegisterSchema(Schema):
    """Registration schema"""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80)
    )
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True
    )
    first_name = fields.Str(
        validate=validate.Length(max=50),
        allow_none=True
    )
    last_name = fields.Str(
        validate=validate.Length(max=50),
        allow_none=True
    )


class RefreshTokenSchema(Schema):
    """Refresh token schema"""
    refresh_token = fields.Str(required=True)
