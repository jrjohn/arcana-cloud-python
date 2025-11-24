"""
HTTP/REST Communication Implementation
For layered and microservices modes using HTTP/REST protocol
"""
import os
from typing import Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.communication.interfaces import (
    ServiceCommunicationInterface,
    RepositoryCommunicationInterface,
    CommunicationMode,
    CommunicationProtocol,
    DeploymentMode
)
from app.utils.exceptions import (
    APIException, NotFoundError, ConflictError,
    ValidationError, AuthenticationError, AuthorizationError
)


class HTTPServiceCommunication(ServiceCommunicationInterface):
    """
    HTTP/REST service communication
    For Controller → Service communication via HTTP
    """

    def __init__(self, service_urls: list, deployment_mode: DeploymentMode):
        """
        Initialize HTTP service communication

        Args:
            service_urls: List of service URLs
            deployment_mode: Deployment mode (layered or microservices)
        """
        self.service_urls = service_urls
        self.current_url_index = 0
        self.deployment_mode = deployment_mode

        # Determine communication mode
        if deployment_mode == DeploymentMode.LAYERED:
            self._mode = CommunicationMode.LAYERED_HTTP
        else:
            self._mode = CommunicationMode.MICROSERVICES_HTTP

        self._protocol = CommunicationProtocol.HTTP

        # Setup HTTP session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_next_url(self) -> str:
        """Get next service URL (round-robin)"""
        url = self.service_urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.service_urls)
        return url

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None,
                      params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request"""
        base_url = self._get_next_url()
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CommunicationLayer/HTTP'
        }

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            # Try to parse error response from service layer
            error_msg = f"HTTP error: {e.response.status_code}"
            error_code = "HTTP_ERROR"

            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    error_msg = error_data.get('error', error_msg)
                    error_code = error_data.get('error_code', error_code)
            except:
                pass

            # Map HTTP status codes to appropriate exception types
            status_code = e.response.status_code
            if status_code == 404:
                raise NotFoundError(error_msg)
            elif status_code == 409:
                raise ConflictError(error_msg)
            elif status_code == 400:
                raise ValidationError(error_msg)
            elif status_code == 401:
                raise AuthenticationError(error_msg)
            elif status_code == 403:
                raise AuthorizationError(error_msg)
            else:
                raise APIException(error_msg, error_code=error_code, status_code=status_code)
        except requests.exceptions.ConnectionError:
            raise APIException(f"Cannot connect to service: {base_url}")
        except requests.exceptions.Timeout:
            raise APIException(f"Request timeout: {base_url}")

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call service method via HTTP"""
        # Map method name to HTTP endpoint
        endpoint = f"/internal/{method}"
        return self._make_request('POST', endpoint, data=kwargs)

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check"""
        try:
            base_url = self.service_urls[0]
            response = self.session.get(f"{base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_users(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """Get users list"""
        # Convert enum values to strings for HTTP transmission
        params = {'page': page, 'per_page': per_page}
        for key, value in filters.items():
            if hasattr(value, 'name'):  # Check if it's an enum
                params[key] = value.name
            else:
                params[key] = value

        result = self._make_request('GET', '/internal/users', params=params)
        return result.get('data', result)

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID"""
        result = self._make_request('GET', f'/internal/users/{user_id}')
        return result.get('data', result)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        result = self._make_request('POST', '/internal/users', data=user_data)
        return result.get('data', result)

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        result = self._make_request('PUT', f'/internal/users/{user_id}', data=user_data)
        return result.get('data', result)

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user"""
        result = self._make_request('DELETE', f'/internal/users/{user_id}')
        return result if result else {'success': True}

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        data = {'old_password': old_password, 'new_password': new_password}
        result = self._make_request('PUT', f'/internal/users/{user_id}/password', data=data)
        return result if result else {'success': True}

    def verify_user(self, user_id: int) -> Dict[str, Any]:
        """Verify user"""
        result = self._make_request('POST', f'/internal/users/{user_id}/verify')
        return result.get('data', result)

    def update_user_status(self, user_id: int, status: str) -> Dict[str, Any]:
        """Update user status"""
        data = {'status': status}
        result = self._make_request('PUT', f'/internal/users/{user_id}/status', data=data)
        return result.get('data', result)


class HTTPRepositoryCommunication(RepositoryCommunicationInterface):
    """
    HTTP/REST repository communication
    For Service → Repository communication via HTTP
    """

    def __init__(self, repository_urls: list, deployment_mode: DeploymentMode):
        """
        Initialize HTTP repository communication

        Args:
            repository_urls: List of repository URLs
            deployment_mode: Deployment mode (layered or microservices)
        """
        self.repository_urls = repository_urls
        self.current_url_index = 0
        self.deployment_mode = deployment_mode

        # Determine communication mode
        if deployment_mode == DeploymentMode.LAYERED:
            self._mode = CommunicationMode.LAYERED_HTTP
        else:
            self._mode = CommunicationMode.MICROSERVICES_HTTP

        self._protocol = CommunicationProtocol.HTTP

        # Setup HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=0.3)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_next_url(self) -> str:
        """Get next repository URL (round-robin)"""
        url = self.repository_urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.repository_urls)
        return url

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None,
                      params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request"""
        base_url = self._get_next_url()
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise APIException(f"Repository HTTP error: {str(e)}")

    def call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Call repository method via HTTP"""
        endpoint = f"/repository/{method}"
        return self._make_request('POST', endpoint, data=kwargs)

    def get_mode(self) -> CommunicationMode:
        """Get communication mode"""
        return self._mode

    def get_protocol(self) -> CommunicationProtocol:
        """Get communication protocol"""
        return self._protocol

    def health_check(self) -> bool:
        """Health check"""
        try:
            base_url = self.repository_urls[0]
            response = self.session.get(f"{base_url}/ready", timeout=5)
            return response.status_code == 200
        except:
            return False

    def query(self, entity: str, filters: Dict[str, Any],
              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Query entities"""
        params = {'page': page, 'per_page': per_page, **filters}
        return self._make_request('GET', f'/repository/{entity}', params=params)

    def get_by_id(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID"""
        return self._make_request('GET', f'/repository/{entity}/{entity_id}')

    def create(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity"""
        return self._make_request('POST', f'/repository/{entity}', data=data)

    def update(self, entity: str, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity"""
        return self._make_request('PUT', f'/repository/{entity}/{entity_id}', data=data)

    def delete(self, entity: str, entity_id: int) -> Dict[str, Any]:
        """Delete entity"""
        return self._make_request('DELETE', f'/repository/{entity}/{entity_id}')
