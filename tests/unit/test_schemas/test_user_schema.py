"""
User Schema Unit Tests
Tests for app/schemas/user_schema.py
"""
import pytest
from marshmallow import ValidationError

from app.schemas.user_schema import (
    UserCreateSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    PublicUserCreateSchema,
    PublicUserUpdateSchema,
)


class TestUserCreateSchema:
    """Tests for UserCreateSchema"""

    @pytest.fixture
    def schema(self):
        return UserCreateSchema()

    def test_valid_user_data(self, schema):
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'SecurePass1',
        }
        result = schema.load(data)
        assert result['username'] == 'alice'
        assert result['email'] == 'alice@example.com'

    def test_username_too_short_raises(self, schema):
        data = {'username': 'ab', 'email': 'a@b.com', 'password': 'SecurePass1'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'username' in exc.value.messages

    def test_username_too_long_raises(self, schema):
        data = {'username': 'a' * 81, 'email': 'a@b.com', 'password': 'SecurePass1'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'username' in exc.value.messages

    def test_invalid_email_raises(self, schema):
        data = {'username': 'alice', 'email': 'not-an-email', 'password': 'SecurePass1'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'email' in exc.value.messages

    def test_password_no_uppercase_raises(self, schema):
        data = {'username': 'alice', 'email': 'a@b.com', 'password': 'lowercase1'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'password' in exc.value.messages

    def test_password_no_lowercase_raises(self, schema):
        data = {'username': 'alice', 'email': 'a@b.com', 'password': 'UPPERCASE1'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'password' in exc.value.messages

    def test_password_no_digit_raises(self, schema):
        data = {'username': 'alice', 'email': 'a@b.com', 'password': 'NoDigitsHere'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'password' in exc.value.messages

    def test_password_too_short_raises(self, schema):
        data = {'username': 'alice', 'email': 'a@b.com', 'password': 'Ab1'}
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'password' in exc.value.messages

    def test_missing_required_fields(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({})
        assert 'username' in exc.value.messages
        assert 'email' in exc.value.messages
        assert 'password' in exc.value.messages

    def test_optional_fields_accepted(self, schema):
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'SecurePass1',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'phone': '+1234567890',
        }
        result = schema.load(data)
        assert result['first_name'] == 'Alice'
        assert result['last_name'] == 'Smith'

    def test_first_name_too_long_raises(self, schema):
        data = {
            'username': 'alice', 'email': 'a@b.com', 'password': 'SecurePass1',
            'first_name': 'A' * 51
        }
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'first_name' in exc.value.messages


class TestUserUpdateSchema:
    """Tests for UserUpdateSchema"""

    @pytest.fixture
    def schema(self):
        return UserUpdateSchema()

    def test_valid_email_update(self, schema):
        data = {'email': 'new@example.com'}
        result = schema.load(data)
        assert result['email'] == 'new@example.com'

    def test_invalid_email_raises(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'email': 'bad-email'})
        assert 'email' in exc.value.messages

    def test_empty_update_allowed(self, schema):
        # All fields optional
        result = schema.load({})
        assert result == {}

    def test_first_name_too_long_raises(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'first_name': 'A' * 51})
        assert 'first_name' in exc.value.messages

    def test_last_name_too_long_raises(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'last_name': 'B' * 51})
        assert 'last_name' in exc.value.messages

    def test_avatar_url_too_long_raises(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'avatar_url': 'http://x.com/' + 'a' * 300})
        assert 'avatar_url' in exc.value.messages


class TestChangePasswordSchema:
    """Tests for ChangePasswordSchema"""

    @pytest.fixture
    def schema(self):
        return ChangePasswordSchema()

    def test_valid_password_change(self, schema):
        data = {'old_password': 'OldPass1', 'new_password': 'NewSecure2'}
        result = schema.load(data)
        assert result['new_password'] == 'NewSecure2'

    def test_missing_old_password(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'new_password': 'NewSecure2'})
        assert 'old_password' in exc.value.messages

    def test_missing_new_password(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'old_password': 'OldPass1'})
        assert 'new_password' in exc.value.messages

    def test_new_password_no_uppercase(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'old_password': 'OldPass1', 'new_password': 'nouppercasedigit1'})
        assert 'new_password' in exc.value.messages

    def test_new_password_no_lowercase(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'old_password': 'OldPass1', 'new_password': 'NOLOWER1'})
        assert 'new_password' in exc.value.messages

    def test_new_password_no_digit(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'old_password': 'OldPass1', 'new_password': 'NoDigitsHere'})
        assert 'new_password' in exc.value.messages

    def test_new_password_too_short(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'old_password': 'OldPass1', 'new_password': 'Ab1'})
        assert 'new_password' in exc.value.messages


class TestPublicUserCreateSchema:
    """Tests for PublicUserCreateSchema"""

    @pytest.fixture
    def schema(self):
        return PublicUserCreateSchema()

    def test_valid_public_create(self, schema):
        data = {'email': 'pub@example.com', 'first_name': 'Alice', 'last_name': 'Smith'}
        result = schema.load(data)
        assert result['email'] == 'pub@example.com'

    def test_unknown_fields_excluded(self, schema):
        data = {
            'email': 'pub@example.com',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'unknown_field': 'ignored'
        }
        result = schema.load(data)
        assert 'unknown_field' not in result

    def test_missing_required_raises(self, schema):
        with pytest.raises(ValidationError) as exc:
            schema.load({'email': 'pub@example.com'})
        assert 'first_name' in exc.value.messages or 'last_name' in exc.value.messages


class TestPublicUserUpdateSchema:
    """Tests for PublicUserUpdateSchema"""

    @pytest.fixture
    def schema(self):
        return PublicUserUpdateSchema()

    def test_valid_update(self, schema):
        data = {'first_name': 'Bob', 'last_name': 'Jones'}
        result = schema.load(data)
        assert result['first_name'] == 'Bob'

    def test_unknown_fields_excluded(self, schema):
        data = {'first_name': 'Bob', 'extra': 'ignored'}
        result = schema.load(data)
        assert 'extra' not in result

    def test_empty_update_allowed(self, schema):
        result = schema.load({})
        assert isinstance(result, dict)
