"""
HTTP Client for Microservices Testing
Makes actual HTTP requests to external microservice processes
"""
import os
import requests
from typing import Optional, Dict, Any


class HTTPTestClient:
    """
    HTTP Test Client for Microservices Mode

    This client makes actual HTTP requests to external microservice processes,
    unlike Flask test client which works in-process only.
    """

    def __init__(self, base_url: str = None):
        """
        Initialize HTTP test client

        Args:
            base_url: Base URL of the controller layer (default: http://localhost:5003)
        """
        self.base_url = base_url or os.getenv('CONTROLLER_URL', 'http://localhost:5003')
        self.session = requests.Session()

    def get(self, path: str, headers: Dict[str, str] = None, **kwargs) -> 'HTTPResponse':
        """Make GET request"""
        url = f"{self.base_url.rstrip('/')}{path}"
        response = self.session.get(url, headers=headers, **kwargs)
        return HTTPResponse(response)

    def post(self, path: str, json: Dict[str, Any] = None, data: Any = None, headers: Dict[str, str] = None, **kwargs) -> 'HTTPResponse':
        """Make POST request"""
        url = f"{self.base_url.rstrip('/')}{path}"
        # Remove Flask-specific kwargs that requests doesn't support
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['content_type']}

        # If data is provided (Flask test client style), use it
        if data is not None:
            # If content_type was application/json and data looks like JSON string, set proper headers
            if headers is None:
                headers = {}
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            response = self.session.post(url, data=data, headers=headers, **filtered_kwargs)
        else:
            response = self.session.post(url, json=json, headers=headers, **filtered_kwargs)
        return HTTPResponse(response)

    def put(self, path: str, json: Dict[str, Any] = None, data: Any = None, headers: Dict[str, str] = None, **kwargs) -> 'HTTPResponse':
        """Make PUT request"""
        url = f"{self.base_url.rstrip('/')}{path}"
        # Remove Flask-specific kwargs that requests doesn't support
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['content_type']}

        # If data is provided (Flask test client style), use it
        if data is not None:
            if headers is None:
                headers = {}
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            response = self.session.put(url, data=data, headers=headers, **filtered_kwargs)
        else:
            response = self.session.put(url, json=json, headers=headers, **filtered_kwargs)
        return HTTPResponse(response)

    def patch(self, path: str, json: Dict[str, Any] = None, data: Any = None, headers: Dict[str, str] = None, **kwargs) -> 'HTTPResponse':
        """Make PATCH request"""
        url = f"{self.base_url.rstrip('/')}{path}"
        # Remove Flask-specific kwargs that requests doesn't support
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['content_type']}

        # If data is provided (Flask test client style), use it
        if data is not None:
            if headers is None:
                headers = {}
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            response = self.session.patch(url, data=data, headers=headers, **filtered_kwargs)
        else:
            response = self.session.patch(url, json=json, headers=headers, **filtered_kwargs)
        return HTTPResponse(response)

    def delete(self, path: str, headers: Dict[str, str] = None, **kwargs) -> 'HTTPResponse':
        """Make DELETE request"""
        url = f"{self.base_url.rstrip('/')}{path}"
        response = self.session.delete(url, headers=headers, **kwargs)
        return HTTPResponse(response)


class HTTPResponse:
    """
    HTTP Response wrapper

    Provides Flask test client-compatible interface for requests.Response
    """

    def __init__(self, response: requests.Response):
        """
        Initialize response wrapper

        Args:
            response: requests.Response object
        """
        self._response = response

    @property
    def status_code(self) -> int:
        """Get status code"""
        return self._response.status_code

    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """Get JSON data"""
        try:
            return self._response.json()
        except Exception:
            return None

    @property
    def data(self) -> bytes:
        """Get raw data"""
        return self._response.content

    @property
    def text(self) -> str:
        """Get text content"""
        return self._response.text

    def get_json(self) -> Optional[Dict[str, Any]]:
        """Get JSON data (Flask test client compatibility)"""
        return self.json
