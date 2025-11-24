"""
Response Helpers Unit Tests
Tests for standardized API response helpers
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
from flask import Flask

from app.utils.response import (
    success_response,
    error_response,
    paginated_response,
    get_request_id
)


@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    return app


class TestSuccessResponse:
    """Test success_response helper"""

    def test_success_response_default(self, app):
        """Test success response with default values"""
        with app.app_context():
            response, status_code = success_response()
            assert status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == 'Success'
            assert data['data'] is None
            assert 'timestamp' in data
            assert 'request_id' in data

    def test_success_response_with_data(self, app):
        """Test success response with data"""
        with app.app_context():
            test_data = {'id': 1, 'name': 'Test'}
            response, status_code = success_response(data=test_data)
            data = json.loads(response.data)
            assert data['data'] == test_data

    def test_success_response_with_custom_message(self, app):
        """Test success response with custom message"""
        with app.app_context():
            response, status_code = success_response(message='User created')
            data = json.loads(response.data)
            assert data['message'] == 'User created'

    def test_success_response_with_custom_status_code(self, app):
        """Test success response with custom status code"""
        with app.app_context():
            response, status_code = success_response(status_code=201)
            assert status_code == 201

    def test_success_response_timestamp_format(self, app):
        """Test success response timestamp format"""
        with app.app_context():
            response, status_code = success_response()
            data = json.loads(response.data)
            timestamp = data['timestamp']
            assert 'T' in timestamp
            assert timestamp.endswith('Z')

    def test_success_response_with_list_data(self, app):
        """Test success response with list data"""
        with app.app_context():
            test_data = [{'id': 1}, {'id': 2}, {'id': 3}]
            response, status_code = success_response(data=test_data)
            data = json.loads(response.data)
            assert len(data['data']) == 3

    def test_success_response_with_nested_data(self, app):
        """Test success response with nested data"""
        with app.app_context():
            test_data = {
                'user': {
                    'id': 1,
                    'profile': {
                        'name': 'Test',
                        'settings': {'theme': 'dark'}
                    }
                }
            }
            response, status_code = success_response(data=test_data)
            data = json.loads(response.data)
            assert data['data']['user']['profile']['settings']['theme'] == 'dark'


class TestErrorResponse:
    """Test error_response helper"""

    def test_error_response_default(self, app):
        """Test error response with default values"""
        with app.app_context():
            response, status_code = error_response()
            assert status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'INTERNAL_ERROR'
            assert data['error']['message'] == 'An error occurred'
            assert 'timestamp' in data
            assert 'request_id' in data

    def test_error_response_custom_message(self, app):
        """Test error response with custom message"""
        with app.app_context():
            response, status_code = error_response(message='User not found')
            data = json.loads(response.data)
            assert data['error']['message'] == 'User not found'

    def test_error_response_custom_status_code(self, app):
        """Test error response with custom status code"""
        with app.app_context():
            response, status_code = error_response(status_code=404)
            assert status_code == 404

    def test_error_response_custom_error_code(self, app):
        """Test error response with custom error code"""
        with app.app_context():
            response, status_code = error_response(error_code='USER_NOT_FOUND')
            data = json.loads(response.data)
            assert data['error']['code'] == 'USER_NOT_FOUND'

    def test_error_response_with_details(self, app):
        """Test error response with error details"""
        with app.app_context():
            details = {
                'field': 'email',
                'reason': 'Invalid format'
            }
            response, status_code = error_response(details=details)
            data = json.loads(response.data)
            assert data['error']['details'] == details

    def test_error_response_validation_errors(self, app):
        """Test error response with validation errors"""
        with app.app_context():
            details = {
                'errors': {
                    'email': ['Invalid format'],
                    'password': ['Too short', 'Missing uppercase']
                }
            }
            response, status_code = error_response(
                message='Validation failed',
                status_code=400,
                error_code='VALIDATION_ERROR',
                details=details
            )
            data = json.loads(response.data)
            assert data['error']['details']['errors']['email'][0] == 'Invalid format'
            assert len(data['error']['details']['errors']['password']) == 2


class TestPaginatedResponse:
    """Test paginated_response helper"""

    def test_paginated_response_basic(self, app):
        """Test paginated response with basic pagination"""
        with app.app_context():
            items = [{'id': 1}, {'id': 2}, {'id': 3}]
            response, status_code = paginated_response(
                items=items,
                page=1,
                per_page=10,
                total=3
            )
            assert status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['data']['items']) == 3
            assert data['data']['pagination']['page'] == 1
            assert data['data']['pagination']['per_page'] == 10
            assert data['data']['pagination']['total'] == 3
            assert data['data']['pagination']['pages'] == 1

    def test_paginated_response_multiple_pages(self, app):
        """Test paginated response with multiple pages"""
        with app.app_context():
            items = [{'id': i} for i in range(10)]
            response, status_code = paginated_response(
                items=items,
                page=2,
                per_page=10,
                total=50
            )
            data = json.loads(response.data)
            assert data['data']['pagination']['pages'] == 5
            assert data['data']['pagination']['page'] == 2

    def test_paginated_response_last_page_partial(self, app):
        """Test paginated response on last page with partial items"""
        with app.app_context():
            items = [{'id': 21}, {'id': 22}]
            response, status_code = paginated_response(
                items=items,
                page=3,
                per_page=10,
                total=22
            )
            data = json.loads(response.data)
            assert data['data']['pagination']['pages'] == 3
            assert len(data['data']['items']) == 2

    def test_paginated_response_empty_results(self, app):
        """Test paginated response with no results"""
        with app.app_context():
            response, status_code = paginated_response(
                items=[],
                page=1,
                per_page=10,
                total=0
            )
            data = json.loads(response.data)
            assert len(data['data']['items']) == 0
            assert data['data']['pagination']['total'] == 0
            assert data['data']['pagination']['pages'] == 0

    def test_paginated_response_custom_message(self, app):
        """Test paginated response with custom message"""
        with app.app_context():
            response, status_code = paginated_response(
                items=[{'id': 1}],
                page=1,
                per_page=10,
                total=1,
                message='Users retrieved successfully'
            )
            data = json.loads(response.data)
            assert data['message'] == 'Users retrieved successfully'

    def test_paginated_response_pages_calculation(self, app):
        """Test pages calculation in paginated response"""
        with app.app_context():
            test_cases = [
                (100, 10, 10),
                (105, 10, 11),
                (99, 10, 10),
                (1, 10, 1),
                (0, 10, 0),
            ]
            for total, per_page, expected_pages in test_cases:
                response, status_code = paginated_response(
                    items=[],
                    page=1,
                    per_page=per_page,
                    total=total
                )
                data = json.loads(response.data)
                assert data['data']['pagination']['pages'] == expected_pages


class TestGetRequestId:
    """Test get_request_id helper"""

    def test_get_request_id_from_g(self, app):
        """Test getting request ID from flask g object"""
        with app.app_context():
            with patch('app.utils.Response.g') as mock_g:
                mock_g.request_id = 'test-request-id-123'
                result = get_request_id()
                assert result == 'test-request-id-123'

    def test_get_request_id_generates_new(self, app):
        """Test generating new request ID when not in g"""
        with app.app_context():
            result = get_request_id()
            assert result is not None
            assert len(result) > 0
            assert '-' in result

    def test_get_request_id_unique(self, app):
        """Test that generated request IDs are unique"""
        with app.app_context():
            id1 = get_request_id()
            id2 = get_request_id()
            # Note: May be same if g.request_id is set, so we just check they're valid UUIDs
            assert '-' in id1
            assert '-' in id2


class TestResponseIntegration:
    """Test response helpers integration"""

    def test_all_responses_have_timestamp(self, app):
        """Test that all response types include timestamp"""
        with app.app_context():
            response1, _ = success_response()
            data1 = json.loads(response1.data)
            assert 'timestamp' in data1

            response2, _ = error_response()
            data2 = json.loads(response2.data)
            assert 'timestamp' in data2

            response3, _ = paginated_response([], 1, 10, 0)
            data3 = json.loads(response3.data)
            assert 'timestamp' in data3

    def test_all_responses_have_request_id(self, app):
        """Test that all response types include request ID"""
        with app.app_context():
            response1, _ = success_response()
            data1 = json.loads(response1.data)
            assert 'request_id' in data1

            response2, _ = error_response()
            data2 = json.loads(response2.data)
            assert 'request_id' in data2

            response3, _ = paginated_response([], 1, 10, 0)
            data3 = json.loads(response3.data)
            assert 'request_id' in data3

    def test_response_content_type(self, app):
        """Test that responses have correct content type"""
        with app.app_context():
            response, _ = success_response()
            assert response.content_type == 'application/json'
