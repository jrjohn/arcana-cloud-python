"""
Service Client
Inter-service communication client - HTTP/gRPC support
"""
import os
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from app.services.clients.load_balancer import LoadBalancer
from app.utils.exceptions import (
    ServiceUnavailableError, APIException, NotFoundError, ConflictError,
    ValidationError, AuthenticationError, AuthorizationError
)

logger = logging.getLogger(__name__)


class ServiceClient:
    """Service client - For inter-service communication"""

    def __init__(
        self,
        service_name: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.3
    ):
        """
        Initialize服務客戶端

        Args:
            service_name: Service name (such as 'user-service', 'auth-service'）
            timeout: Request timeout (seconds)
            max_retries: Maximum retry count
            backoff_factor: Retry interval factor
        """
        self.service_name = service_name
        self.timeout = timeout

        # 從環境變數獲取Service URL list
        env_key = f"{service_name.upper().replace('-', '_')}_URLS"
        urls_str = os.getenv(env_key, '')

        if not urls_str:
            # If multiple URLs not configured, use default single URL
            default_url = os.getenv(
                f"{service_name.upper().replace('-', '_')}_URL",
                f"http://localhost:5000"
            )
            service_urls = [default_url]
        else:
            service_urls = [url.strip() for url in urls_str.split(',') if url.strip()]

        # Initialize負載平衡器
        self.load_balancer = LoadBalancer(service_urls)

        # Configure HTTP session (connection pool + retry)
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"ServiceClient initialized for {service_name} with URLs: {service_urls}")

    def call(
        self,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call remote service

        Args:
            endpoint: API endpoint (such as '/api/v1/users'）
            method: HTTP method
            data: Request body data
            headers: Request headers
            params: URL parameters

        Returns:
            Response data

        Raises:
            ServiceUnavailableError: Service unavailable
        """
        # 獲取Service URL
        base_url = self.load_balancer.get_next_url()
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # 設置默認Request headers
        if headers is None:
            headers = {}

        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('User-Agent', f'ServiceClient/{self.service_name}')

        try:
            logger.debug(f"Calling {method} {url}")

            # Send request
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                params=params,
                timeout=self.timeout
            )

            # Check response status
            response.raise_for_status()

            # Mark service as healthy
            self.load_balancer.mark_healthy(base_url)

            # Parse response
            try:
                return response.json()
            except ValueError:
                return {'data': response.text}

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error calling {url}: {e}")

            # 如果是 5xx 錯誤，Mark service as unhealthy
            if e.response.status_code >= 500:
                self.load_balancer.mark_unhealthy(base_url)

            # Try to parse error response from service
            error_msg = f"Service {self.service_name} returned error: {e.response.status_code}"
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
            if status_code == 400:
                raise ValidationError(error_msg)
            elif status_code == 401:
                raise AuthenticationError(error_msg)
            elif status_code == 403:
                raise AuthorizationError(error_msg)
            elif status_code == 404:
                raise NotFoundError(error_msg)
            elif status_code == 409:
                raise ConflictError(error_msg)
            elif status_code >= 500:
                raise ServiceUnavailableError(error_msg)
            else:
                raise APIException(error_msg, error_code=error_code, status_code=status_code)

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error calling {url}: {e}")
            self.load_balancer.mark_unhealthy(base_url)

            raise ServiceUnavailableError(
                f"Cannot connect to service {self.service_name}"
            )

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout calling {url}: {e}")
            self.load_balancer.mark_unhealthy(base_url)

            raise ServiceUnavailableError(
                f"Service {self.service_name} request timeout"
            )

        except Exception as e:
            logger.error(f"Unexpected error calling {url}: {e}")

            raise ServiceUnavailableError(
                f"Service {self.service_name} unavailable: {str(e)}"
            )

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request"""
        return self.call(endpoint, method='GET', **kwargs)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """POST request"""
        return self.call(endpoint, method='POST', data=data, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        return self.call(endpoint, method='PUT', data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        return self.call(endpoint, method='DELETE', **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """PATCH request"""
        return self.call(endpoint, method='PATCH', data=data, **kwargs)

    def health_check(self) -> bool:
        """
        Check service health status

        Returns:
            Whether healthy
        """
        try:
            response = self.get('/health')
            return response.get('status') == 'healthy'
        except Exception as e:
            logger.warning(f"Health check failed for {self.service_name}: {e}")
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get service information

        Returns:
            Service information dictionary
        """
        return {
            'service_name': self.service_name,
            'all_urls': self.load_balancer.get_all_urls(),
            'healthy_urls': self.load_balancer.get_healthy_urls(),
            'health_status': self.load_balancer.get_health_status()
        }
