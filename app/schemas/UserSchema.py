"""
User Schemas
User data serialization schemas
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


class UserSchema(Schema):
    """User output schema"""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    avatar_url = fields.Str(allow_none=True)
    role = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    last_login_at = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """User create schema"""
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
    phone = fields.Str(
        validate=validate.Length(max=20),
        allow_none=True
    )

    @validates('password')
    def validate_password(self, value):
        """驗證Password強度"""
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit')


class UserUpdateSchema(Schema):
    """User update schema"""
    email = fields.Email()
    first_name = fields.Str(validate=validate.Length(max=50))
    last_name = fields.Str(validate=validate.Length(max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    avatar_url = fields.Str(validate=validate.Length(max=255))


class ChangePasswordSchema(Schema):
    """修改Password Schema"""
    old_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True
    )

    @validates('new_password')
    def validate_new_password(self, value):
        """驗證新Password強度"""
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit')


# ============================================================================
# Public API Schemas (Simplified for public API compatibility)
# ============================================================================

class PublicUserSchema(Schema):
    """Public API user schema (simplified)"""
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    avatar = fields.Str(allow_none=True, attribute='avatar_url', data_key='avatar')


class PublicUserCreateSchema(Schema):
    """Public API user creation schema (simplified, no password required)"""
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    avatar = fields.Str(allow_none=True, data_key='avatar')
    job = fields.Str(allow_none=True)  # Allows arbitrary fields for compatibility


class PublicUserUpdateSchema(Schema):
    """Public API user update schema"""
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()
    avatar = fields.Str()
    job = fields.Str(allow_none=True)  # Allows arbitrary fields for compatibility
