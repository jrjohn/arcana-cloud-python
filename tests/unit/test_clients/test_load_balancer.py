"""
Load Balancer Unit Tests
Tests for LoadBalancer implementation
"""
import pytest
import threading
from unittest.mock import Mock, patch

from app.services.clients.LoadBalancer import LoadBalancer


class TestLoadBalancer:
    """LoadBalancer test class"""

    def test_initialization_with_urls(self):
        """Test load balancer initialization with URLs"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']

        # Act
        lb = LoadBalancer(urls)

        # Assert
        assert lb.service_urls == urls
        assert lb.current_index == 0
        assert len(lb.health_status) == 3
        assert all(status for status in lb.health_status.values())

    def test_initialization_empty_urls_raises_error(self):
        """Test load balancer initialization with empty URLs raises error"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            LoadBalancer([])

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_get_next_url_round_robin(self):
        """Test round robin URL selection"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)

        # Act
        url1 = lb.get_next_url()
        url2 = lb.get_next_url()
        url3 = lb.get_next_url()
        url4 = lb.get_next_url()  # Should wrap around

        # Assert
        assert url1 == urls[0]
        assert url2 == urls[1]
        assert url3 == urls[2]
        assert url4 == urls[0]  # Back to first

    def test_get_next_url_single_service(self):
        """Test URL selection with single service"""
        # Arrange
        urls = ['http://service1.com']
        lb = LoadBalancer(urls)

        # Act
        url1 = lb.get_next_url()
        url2 = lb.get_next_url()
        url3 = lb.get_next_url()

        # Assert
        assert url1 == urls[0]
        assert url2 == urls[0]
        assert url3 == urls[0]

    def test_get_next_url_skips_unhealthy(self):
        """Test that unhealthy services are skipped"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[1])  # Mark service2 as unhealthy

        # Act
        url1 = lb.get_next_url()
        url2 = lb.get_next_url()
        url3 = lb.get_next_url()

        # Assert
        assert url1 in [urls[0], urls[2]]
        assert url2 in [urls[0], urls[2]]
        assert url3 in [urls[0], urls[2]]
        assert urls[1] not in [url1, url2, url3]

    def test_get_next_url_all_unhealthy_returns_first(self):
        """Test that when all services are unhealthy, first service is returned"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[0])
        lb.mark_unhealthy(urls[1])

        # Act
        url = lb.get_next_url()

        # Assert
        assert url == urls[0]  # Returns first as fallback

    def test_mark_healthy(self):
        """Test marking service as healthy"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[0])

        # Act
        lb.mark_healthy(urls[0])

        # Assert
        assert lb.health_status[urls[0]] is True

    def test_mark_unhealthy(self):
        """Test marking service as unhealthy"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)

        # Act
        lb.mark_unhealthy(urls[0])

        # Assert
        assert lb.health_status[urls[0]] is False

    def test_mark_healthy_invalid_url_ignored(self):
        """Test marking non-existent URL as healthy is ignored"""
        # Arrange
        urls = ['http://service1.com']
        lb = LoadBalancer(urls)

        # Act
        lb.mark_healthy('http://nonexistent.com')

        # Assert - Should not raise error
        assert 'http://nonexistent.com' not in lb.health_status

    def test_mark_unhealthy_invalid_url_ignored(self):
        """Test marking non-existent URL as unhealthy is ignored"""
        # Arrange
        urls = ['http://service1.com']
        lb = LoadBalancer(urls)

        # Act
        lb.mark_unhealthy('http://nonexistent.com')

        # Assert - Should not raise error
        assert 'http://nonexistent.com' not in lb.health_status

    def test_get_all_urls(self):
        """Test getting all URLs"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)

        # Act
        result = lb.get_all_urls()

        # Assert
        assert result == urls
        assert result is not lb.service_urls  # Should be a copy

    def test_get_healthy_urls(self):
        """Test getting only healthy URLs"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[1])

        # Act
        result = lb.get_healthy_urls()

        # Assert
        assert len(result) == 2
        assert urls[0] in result
        assert urls[2] in result
        assert urls[1] not in result

    def test_get_healthy_urls_all_healthy(self):
        """Test getting healthy URLs when all are healthy"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)

        # Act
        result = lb.get_healthy_urls()

        # Assert
        assert len(result) == 2
        assert result == urls

    def test_get_healthy_urls_all_unhealthy(self):
        """Test getting healthy URLs when all are unhealthy"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[0])
        lb.mark_unhealthy(urls[1])

        # Act
        result = lb.get_healthy_urls()

        # Assert
        assert len(result) == 0

    def test_get_health_status(self):
        """Test getting health status of all services"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[1])

        # Act
        result = lb.get_health_status()

        # Assert
        assert result[urls[0]] is True
        assert result[urls[1]] is False
        assert result[urls[2]] is True
        assert result is not lb.health_status  # Should be a copy

    def test_thread_safety(self):
        """Test that load balancer is thread-safe"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)
        results = []

        def get_url():
            for _ in range(100):
                url = lb.get_next_url()
                results.append(url)

        # Act
        threads = [threading.Thread(target=get_url) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == 1000
        # All results should be valid URLs
        assert all(url in urls for url in results)

    def test_concurrent_health_status_updates(self):
        """Test concurrent health status updates"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)

        def mark_services():
            for _ in range(50):
                lb.mark_unhealthy(urls[0])
                lb.mark_healthy(urls[0])

        # Act
        threads = [threading.Thread(target=mark_services) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - Should not crash, final state may vary
        assert urls[0] in lb.health_status

    def test_recovery_scenario(self):
        """Test service recovery scenario"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com']
        lb = LoadBalancer(urls)

        # Act - Service goes down
        lb.mark_unhealthy(urls[0])
        url1 = lb.get_next_url()

        # Service recovers
        lb.mark_healthy(urls[0])
        url2 = lb.get_next_url()

        # Assert
        assert url1 == urls[1]  # Should use healthy service
        assert url2 in urls  # Can use either now

    def test_multiple_unhealthy_marks(self):
        """Test marking same service unhealthy multiple times"""
        # Arrange
        urls = ['http://service1.com']
        lb = LoadBalancer(urls)

        # Act
        lb.mark_unhealthy(urls[0])
        lb.mark_unhealthy(urls[0])
        lb.mark_unhealthy(urls[0])

        # Assert
        assert lb.health_status[urls[0]] is False

    def test_multiple_healthy_marks(self):
        """Test marking same service healthy multiple times"""
        # Arrange
        urls = ['http://service1.com']
        lb = LoadBalancer(urls)
        lb.mark_unhealthy(urls[0])

        # Act
        lb.mark_healthy(urls[0])
        lb.mark_healthy(urls[0])
        lb.mark_healthy(urls[0])

        # Assert
        assert lb.health_status[urls[0]] is True

    def test_get_next_url_continues_round_robin_after_health_change(self):
        """Test that round robin continues correctly after health status changes"""
        # Arrange
        urls = ['http://service1.com', 'http://service2.com', 'http://service3.com']
        lb = LoadBalancer(urls)

        # Act
        url1 = lb.get_next_url()  # service1
        lb.mark_unhealthy(urls[1])  # Mark service2 unhealthy
        url2 = lb.get_next_url()  # Should skip service2, get service3
        url3 = lb.get_next_url()  # Should get service1 again

        # Assert
        assert url1 == urls[0]
        assert url2 == urls[2]  # Skipped service2
        assert url3 == urls[0]  # Back to service1
