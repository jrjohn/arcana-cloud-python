"""
DI Container Unit Tests
Tests for app/di_container.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.di_container import DIContainer


class TestDIContainerRegisterSingleton:
    """Tests for register_singleton()"""

    def test_register_singleton_stores_factory(self):
        container = DIContainer()
        factory = lambda: object()
        container.register_singleton('svc', factory)
        assert 'svc' in container._factories
        assert container._singletons['svc'] is True

    def test_register_singleton_only_creates_once(self):
        container = DIContainer()
        call_count = {'n': 0}

        def factory():
            call_count['n'] += 1
            return object()

        container.register_singleton('svc', factory)
        obj1 = container.get('svc')
        obj2 = container.get('svc')
        assert obj1 is obj2
        assert call_count['n'] == 1


class TestDIContainerRegisterTransient:
    """Tests for register_transient()"""

    def test_register_transient_creates_new_each_time(self):
        container = DIContainer()
        container.register_transient('svc', lambda: object())
        obj1 = container.get('svc')
        obj2 = container.get('svc')
        assert obj1 is not obj2

    def test_register_transient_singleton_false(self):
        container = DIContainer()
        container.register_transient('svc', lambda: None)
        assert container._singletons['svc'] is False


class TestDIContainerRegisterInstance:
    """Tests for register_instance()"""

    def test_register_instance_returns_same_object(self):
        container = DIContainer()
        instance = object()
        container.register_instance('svc', instance)
        result = container.get('svc')
        assert result is instance

    def test_register_instance_marked_singleton(self):
        container = DIContainer()
        instance = object()
        container.register_instance('svc', instance)
        assert container._singletons['svc'] is True


class TestDIContainerGet:
    """Tests for get()"""

    def test_get_unregistered_raises_key_error(self):
        container = DIContainer()
        with pytest.raises(KeyError) as exc_info:
            container.get('nonexistent')
        assert 'nonexistent' in str(exc_info.value)

    def test_get_registered_singleton(self):
        container = DIContainer()
        mock_obj = Mock()
        container.register_singleton('svc', lambda: mock_obj)
        assert container.get('svc') is mock_obj

    def test_get_cached_instance_skips_factory(self):
        container = DIContainer()
        instance = object()
        container._instances['svc'] = instance
        result = container.get('svc')
        assert result is instance


class TestDIContainerClear:
    """Tests for clear()"""

    def test_clear_removes_cached_instances(self):
        container = DIContainer()
        container.register_singleton('svc', lambda: object())
        container.get('svc')
        assert 'svc' in container._instances
        container.clear()
        assert container._instances == {}

    def test_clear_preserves_factories(self):
        container = DIContainer()
        container.register_singleton('svc', lambda: object())
        container.get('svc')
        container.clear()
        assert 'svc' in container._factories


class TestDIContainerReset:
    """Tests for reset()"""

    def test_reset_clears_everything(self):
        container = DIContainer()
        container.register_singleton('svc', lambda: object())
        container.get('svc')
        container.reset()
        assert container._instances == {}
        assert container._factories == {}
        assert container._singletons == {}

    def test_after_reset_get_raises_key_error(self):
        container = DIContainer()
        container.register_singleton('svc', lambda: object())
        container.reset()
        with pytest.raises(KeyError):
            container.get('svc')


class TestDIContainerMultipleDependencies:
    """Tests for multiple registered dependencies"""

    def test_multiple_singletons(self):
        container = DIContainer()
        container.register_singleton('a', lambda: {'key': 'a'})
        container.register_singleton('b', lambda: {'key': 'b'})
        assert container.get('a')['key'] == 'a'
        assert container.get('b')['key'] == 'b'

    def test_mixed_registration(self):
        container = DIContainer()
        shared = object()
        container.register_instance('singleton', shared)
        container.register_transient('transient', lambda: object())

        assert container.get('singleton') is shared
        t1 = container.get('transient')
        t2 = container.get('transient')
        assert t1 is not t2


class TestGetContainer:
    """Tests for get_container() helper"""

    def test_get_container_returns_di_container(self):
        from app.di_container import get_container
        container = get_container()
        assert isinstance(container, DIContainer)

    def test_get_container_returns_same_instance(self):
        from app.di_container import get_container
        c1 = get_container()
        c2 = get_container()
        assert c1 is c2


class TestGetUserService:
    """Tests for get_user_service() helper"""

    def test_get_user_service_raises_if_not_initialized(self):
        """get_user_service should raise KeyError if not registered"""
        from app.di_container import get_container, get_user_service

        container = get_container()
        # Remove user_service if present to test uninitialized state
        was_registered = 'user_service' in container._factories
        if was_registered:
            # Just ensure it's registered - skip this test
            pytest.skip("user_service already registered in global container")

        with pytest.raises(KeyError):
            get_user_service()


class TestGetAuthService:
    """Tests for get_auth_service() helper"""

    def test_get_auth_service_raises_if_not_initialized(self):
        """get_auth_service should raise KeyError if not registered"""
        from app.di_container import get_container, get_auth_service

        container = get_container()
        was_registered = 'auth_service' in container._factories
        if was_registered:
            pytest.skip("auth_service already registered in global container")

        with pytest.raises(KeyError):
            get_auth_service()
