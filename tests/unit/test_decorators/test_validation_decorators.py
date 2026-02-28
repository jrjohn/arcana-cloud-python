"""
Validation Decorators Unit Tests
Tests for app/decorators/validation_decorators.py
"""
import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask
from marshmallow import Schema, fields, ValidationError as MarshmallowValidationError


def _make_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


class SimpleSchema(Schema):
    name = fields.Str(required=True)
    age = fields.Int(required=True)


class TestValidateSchema:
    """Tests for validate_schema decorator"""

    def test_valid_json_passes_validation(self):
        from app.decorators.validation_decorators import validate_schema

        app = _make_app()

        @validate_schema(SimpleSchema, location='json')
        def create_user():
            from flask import request
            return (json.dumps(request.validated_data), 200)

        with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'name': 'Alice', 'age': 30}),
            content_type='application/json'
        ):
            response = create_user()
            assert response[1] == 200

    def test_invalid_json_returns_400(self):
        from app.decorators.validation_decorators import validate_schema

        app = _make_app()

        @validate_schema(SimpleSchema, location='json')
        def create_user():
            return ('ok', 200)

        # No JSON body → will fail silently
        with app.test_request_context('/', method='POST', content_type='text/plain', data='not json'):
            response = create_user()
            assert response[1] == 400

    def test_missing_required_field_returns_400(self):
        from app.decorators.validation_decorators import validate_schema

        app = _make_app()

        @validate_schema(SimpleSchema, location='json')
        def create_user():
            return ('ok', 200)

        with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'name': 'Alice'}),  # Missing 'age'
            content_type='application/json'
        ):
            response = create_user()
            assert response[1] == 400

    def test_args_location(self):
        from app.decorators.validation_decorators import validate_schema

        class SearchSchema(Schema):
            q = fields.Str(required=True)

        app = _make_app()

        @validate_schema(SearchSchema, location='args')
        def search():
            from flask import request
            return (request.validated_data['q'], 200)

        with app.test_request_context('/?q=hello', method='GET'):
            response = search()
            assert response[1] == 200
            assert response[0] == 'hello'

    def test_form_location(self):
        from app.decorators.validation_decorators import validate_schema

        class FormSchema(Schema):
            field = fields.Str(required=True)

        app = _make_app()

        @validate_schema(FormSchema, location='form')
        def form_route():
            from flask import request
            return (request.validated_data['field'], 200)

        with app.test_request_context(
            '/',
            method='POST',
            data={'field': 'value'},
            content_type='application/x-www-form-urlencoded'
        ):
            response = form_route()
            assert response[1] == 200

    def test_invalid_location_returns_500(self):
        from app.decorators.validation_decorators import validate_schema

        app = _make_app()

        @validate_schema(SimpleSchema, location='invalid')
        def bad_route():
            return ('ok', 200)

        with app.test_request_context('/', method='POST'):
            response = bad_route()
            assert response[1] == 500


class TestValidatePagination:
    """Tests for validate_pagination decorator"""

    def test_default_pagination_values(self):
        from app.decorators.validation_decorators import validate_pagination

        app = _make_app()

        @validate_pagination()
        def get_list():
            from flask import request
            return (json.dumps(request.pagination), 200)

        with app.test_request_context('/', method='GET'):
            response = get_list()
            assert response[1] == 200
            data = json.loads(response[0])
            assert data['page'] == 1
            assert data['per_page'] == 20

    def test_custom_pagination_values(self):
        from app.decorators.validation_decorators import validate_pagination

        app = _make_app()

        @validate_pagination()
        def get_list():
            from flask import request
            return (json.dumps(request.pagination), 200)

        with app.test_request_context('/?page=3&per_page=50', method='GET'):
            response = get_list()
            assert response[1] == 200
            data = json.loads(response[0])
            assert data['page'] == 3
            assert data['per_page'] == 50

    def test_invalid_page_returns_400(self):
        from app.decorators.validation_decorators import validate_pagination

        app = _make_app()

        @validate_pagination()
        def get_list():
            return ('ok', 200)

        with app.test_request_context('/?page=0', method='GET'):
            response = get_list()
            assert response[1] == 400

    def test_negative_per_page_returns_400(self):
        from app.decorators.validation_decorators import validate_pagination

        app = _make_app()

        @validate_pagination()
        def get_list():
            return ('ok', 200)

        with app.test_request_context('/?per_page=-1', method='GET'):
            response = get_list()
            assert response[1] == 400

    def test_per_page_exceeds_max_capped(self):
        from app.decorators.validation_decorators import validate_pagination

        app = _make_app()

        @validate_pagination(max_per_page=100)
        def get_list():
            from flask import request
            return (json.dumps(request.pagination), 200)

        with app.test_request_context('/?per_page=200', method='GET'):
            response = get_list()
            assert response[1] == 200
            data = json.loads(response[0])
            assert data['per_page'] <= 100
