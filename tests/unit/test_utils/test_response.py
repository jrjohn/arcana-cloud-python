"""
Response Helpers Unit Tests
Tests for standardized API response helpers
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from app.utils.Response import (
    success_response,
    error_response,
    paginated_response,
    get_request_id
)


class TestSuccessResponse:
    """Test success_response helper"""

    def test_success_response_default(self):
        """Test success response with default values"""
        # Act
        response, status_code = success_response()

        # Assert
        assert status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Success'
        assert data['data'] is None
        assert 'timestamp' in data
        assert 'request_id' in data

    def test_success_response_with_data(self):
        """Test success response with data"""
        # Arrange
        test_data = {'id': 1, 'name': 'Test'}

        # Act
        response, status_code = success_response(data=test_data)

        # Assert
        data = json.loads(response.data)
        assert data['data'] == test_data

    def test_success_response_with_custom_message(self):
        """Test success response with custom message"""
        # Act
        response, status_code = success_response(message='User created')

        # Assert
        data = json.loads(response.data)
        assert data['message'] == 'User created'

    def test_success_response_with_custom_status_code(self):
        """Test success response with custom status code"""
        # Act
        response, status_code = success_response(status_code=201)

        # Assert
        assert status_code == 201

    def test_success_response_timestamp_format(self):
        """Test success response timestamp format"""
        # Act
        response, status_code = success_response()

        # Assert
        data = json.loads(response.data)
        timestamp = data['timestamp']
        assert 'T' in timestamp
        assert timestamp.endswith('Z')

    def test_success_response_with_list_data(self):
        """Test success response with list data"""
        # Arrange
        test_data = [{'id': 1}, {'id': 2}, {'id': 3}]

        # Act
        response, status_code = success_response(data=test_data)

        # Assert
        data = json.loads(response.data)
        assert len(data['data']) == 3

    def test_success_response_with_nested_data(self):
        """Test success response with nested data"""
        # Arrange
        test_data = {
            'user': {
                'id': 1,
                'profile': {
                    'name': 'Test',
                    'settings': {'theme': 'dark'}
                }
            }
        }

        # Act
        response, status_code = success_response(data=test_data)

        # Assert
        data = json.loads(response.data)
        assert data['data']['user']['profile']['settings']['theme'] == 'dark'


class TestErrorResponse:
    """Test error_response helper"""

    def test_error_response_default(self):
        """Test error response with default values"""
        # Act
        response, status_code = error_response()

        # Assert
        assert status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'INTERNAL_ERROR'
        assert data['error']['message'] == 'An error occurred'
        assert 'timestamp' in data
        assert 'request_id' in data

    def test_error_response_custom_message(self):
        """Test error response with custom message"""
        # Act
        response, status_code = error_response(message='User not found')

        # Assert
        data = json.loads(response.data)
        assert data['error']['message'] == 'User not found'

    def test_error_response_custom_status_code(self):
        """Test error response with custom status code"""
        # Act
        response, status_code = error_response(status_code=404)

        # Assert
        assert status_code == 404

    def test_error_response_custom_error_code(self):
        """Test error response with custom error code"""
        # Act
        response, status_code = error_response(error_code='USER_NOT_FOUND')

        # Assert
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'

    def test_error_response_with_details(self):
        """Test error response with error details"""
        # Arrange
        details = {
            'field': 'email',
            'reason': 'Invalid format'
        }

        # Act
        response, status_code = error_response(details=details)

        # Assert
        data = json.loads(response.data)
        assert data['error']['details'] == details

    def test_error_response_validation_errors(self):
        """Test error response with validation errors"""
        # Arrange
        details = {
            'errors': {
                'email': ['Invalid format'],
                'password': ['Too short', 'Missing uppercase']
            }
        }

        # Act
        response, status_code = error_response(
            message='Validation failed',
            status_code=400,
            error_code='VALIDATION_ERROR',
            details=details
        )

        # Assert
        data = json.loads(response.data)
        assert data['error']['details']['errors']['email'][0] == 'Invalid format'
        assert len(data['error']['details']['errors']['password']) == 2


class TestPaginatedResponse:
    """Test paginated_response helper"""

    def test_paginated_response_basic(self):
        """Test paginated response with basic pagination"""
        # Arrange
        items = [{'id': 1}, {'id': 2}, {'id': 3}]

        # Act
        response, status_code = paginated_response(
            items=items,
            page=1,
            per_page=10,
            total=3
        )

        # Assert
        assert status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['items']) == 3
        assert data['data']['pagination']['page'] == 1
        assert data['data']['pagination']['per_page'] == 10
        assert data['data']['pagination']['total'] == 3
        assert data['data']['pagination']['pages'] == 1

    def test_paginated_response_multiple_pages(self):
        """Test paginated response with multiple pages"""
        # Arrange
        items = [{'id': i} for i in range(10)]

        # Act
        response, status_code = paginated_response(
            items=items,
            page=2,
            per_page=10,
            total=50
        )

        # Assert
        data = json.loads(response.data)
        assert data['data']['pagination']['pages'] == 5
        assert data['data']['pagination']['page'] == 2

    def test_paginated_response_last_page_partial(self):
        """Test paginated response on last page with partial items"""
        # Arrange
        items = [{'id': 21}, {'id': 22}]  # Only 2 items on last page

        # Act
        response, status_code = paginated_response(
            items=items,
            page=3,
            per_page=10,
            total=22
        )

        # Assert
        data = json.loads(response.data)
        assert data['data']['pagination']['pages'] == 3
        assert len(data['data']['items']) == 2

    def test_paginated_response_empty_results(self):
        """Test paginated response with no results"""
        # Act
        response, status_code = paginated_response(
            items=[],
            page=1,
            per_page=10,
            total=0
        )

        # Assert
        data = json.loads(response.data)
        assert len(data['data']['items']) == 0
        assert data['data']['pagination']['total'] == 0
        assert data['data']['pagination']['pages'] == 0

    def test_paginated_response_custom_message(self):
        """Test paginated response with custom message"""
        # Act
        response, status_code = paginated_response(
            items=[{'id': 1}],
            page=1,
            per_page=10,
            total=1,
            message='Users retrieved successfully'
        )

        # Assert
        data = json.loads(response.data)
        assert data['message'] == 'Users retrieved successfully'

    def test_paginated_response_pages_calculation(self):
        """Test pages calculation in paginated response"""
        # Test various total/per_page combinations
        test_cases = [
            (100, 10, 10),  # Exact division
            (105, 10, 11),  # Needs extra page
            (99, 10, 10),   # Just under 100
            (1, 10, 1),     # Single item
            (0, 10, 0),     # No items
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

    def test_get_request_id_from_g(self):
        """Test getting request ID from flask g object"""
        # Arrange
        with patch('app.utils.Response.g') as mock_g:
            mock_g.request_id = 'test-request-id-123'

            # Act
            result = get_request_id()

            # Assert
            assert result == 'test-request-id-123'

    def test_get_request_id_generates_new(self):
        """Test generating new request ID when not in g"""
        # Arrange
        with patch('app.utils.Response.g') as mock_g:
            # Simulate no request_id attribute
            type(mock_g).request_id = property(lambda self: AttributeError())

            # Act
            result = get_request_id()

            # Assert
            assert result is not None
            assert len(result) > 0
            # Should be a UUID format
            assert '-' in result

    def test_get_request_id_unique(self):
        """Test that generated request IDs are unique"""
        # Arrange
        with patch('app.utils.Response.g') as mock_g:
            type(mock_g).request_id = property(lambda self: AttributeError())

            # Act
            id1 = get_request_id()
            id2 = get_request_id()

            # Assert
            assert id1 != id2


class TestResponseIntegration:
    """Test response helpers integration"""

    def test_all_responses_have_timestamp(self):
        """Test that all response types include timestamp"""
        # Success response
        response1, _ = success_response()
        data1 = json.loads(response1.data)
        assert 'timestamp' in data1

        # Error response
        response2, _ = error_response()
        data2 = json.loads(response2.data)
        assert 'timestamp' in data2

        # Paginated response
        response3, _ = paginated_response([], 1, 10, 0)
        data3 = json.loads(response3.data)
        assert 'timestamp' in data3

    def test_all_responses_have_request_id(self):
        """Test that all response types include request ID"""
        # Success response
        response1, _ = success_response()
        data1 = json.loads(response1.data)
        assert 'request_id' in data1

        # Error response
        response2, _ = error_response()
        data2 = json.loads(response2.data)
        assert 'request_id' in data2

        # Paginated response
        response3, _ = paginated_response([], 1, 10, 0)
        data3 = json.loads(response3.data)
        assert 'request_id' in data3

    def test_response_content_type(self):
        """Test that responses have correct content type"""
        # Act
        response, _ = success_response()

        # Assert
        assert response.content_type == 'application/json'
