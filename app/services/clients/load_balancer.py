"""
Load Balancer
Load balancer - Round Robin implementation
"""
import threading
from typing import List
import logging

logger = logging.getLogger(__name__)


class LoadBalancer:
    """Round Robin load balancer"""

    def __init__(self, service_urls: List[str]):
        """
        Initialize負載平衡器

        Args:
            service_urls: Service URL list
        """
        if not service_urls:
            raise ValueError("Service URLs cannot be empty")

        self.service_urls = service_urls
        self.current_index = 0
        self.lock = threading.Lock()
        self.health_status = dict.fromkeys(service_urls, True)

        logger.info(f"LoadBalancer initialized with {len(service_urls)} services: {service_urls}")

    def get_next_url(self) -> str:
        """
        Get next service URL (Round Robin)

        Returns:
            Service URL

        Raises:
            RuntimeError: No available services
        """
        with self.lock:
            # Filter out healthy services
            healthy_urls = [url for url in self.service_urls if self.health_status.get(url, True)]

            if not healthy_urls:
                logger.warning("No healthy services available, returning first service as fallback")
                # Return first service as fallback for recovery attempts
                return self.service_urls[0]

            # If current index points to unhealthy service, find next healthy service
            attempts = 0
            while attempts < len(self.service_urls):
                url = self.service_urls[self.current_index % len(self.service_urls)]
                self.current_index += 1

                if self.health_status.get(url, True):
                    logger.debug(f"Selected service: {url}")
                    return url

                attempts += 1

            # If all services unhealthy, return first service (attempt recovery)
            logger.warning("All services marked unhealthy, attempting recovery")
            return self.service_urls[0]

    def mark_unhealthy(self, url: str) -> None:
        """
        Mark service as unhealthy

        Args:
            url: Service URL
        """
        with self.lock:
            if url in self.health_status:
                self.health_status[url] = False
                logger.warning(f"Service marked as unhealthy: {url}")

    def mark_healthy(self, url: str) -> None:
        """
        Mark service as healthy

        Args:
            url: Service URL
        """
        with self.lock:
            if url in self.health_status:
                self.health_status[url] = True
                logger.info(f"Service marked as healthy: {url}")

    def get_all_urls(self) -> List[str]:
        """
        獲取所有Service URL

        Returns:
            Service URL list
        """
        return self.service_urls.copy()

    def get_healthy_urls(self) -> List[str]:
        """
        獲取所有健康的Service URL

        Returns:
            健康的Service URL list
        """
        with self.lock:
            return [url for url in self.service_urls if self.health_status.get(url, True)]

    def get_health_status(self) -> dict:
        """
        Get health status of all services

        Returns:
            Service health status dictionary
        """
        with self.lock:
            return self.health_status.copy()
