"""
Dependency Injection Container
Manages dependency injection for the entire application
"""
from typing import Dict, Any, Optional, Callable
from flask import Flask
from app.Extensions import db


class DIContainer:
    """
    Simple Dependency Injection Container

    Manages instances and their dependencies with support for:
    - Singleton instances (created once and reused)
    - Factory functions (create new instance each time)
    - Lazy initialization
    """

    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, bool] = {}

    def register_singleton(self, name: str, factory: Callable):
        """
        Register a singleton dependency

        Args:
            name: Dependency name
            factory: Factory function to create instance
        """
        self._factories[name] = factory
        self._singletons[name] = True

    def register_transient(self, name: str, factory: Callable):
        """
        Register a transient dependency (new instance each time)

        Args:
            name: Dependency name
            factory: Factory function to create instance
        """
        self._factories[name] = factory
        self._singletons[name] = False

    def register_instance(self, name: str, instance: Any):
        """
        Register an existing instance

        Args:
            name: Dependency name
            instance: Instance to register
        """
        self._instances[name] = instance
        self._singletons[name] = True

    def get(self, name: str) -> Any:
        """
        Get dependency instance

        Args:
            name: Dependency name

        Returns:
            Dependency instance

        Raises:
            KeyError: If dependency not registered
        """
        # Check if singleton instance already exists
        if name in self._instances:
            return self._instances[name]

        # Check if factory registered
        if name not in self._factories:
            raise KeyError(f"Dependency '{name}' not registered")

        # Create instance using factory
        instance = self._factories[name]()

        # Cache if singleton
        if self._singletons.get(name, False):
            self._instances[name] = instance

        return instance

    def clear(self):
        """Clear all cached instances"""
        self._instances.clear()

    def reset(self):
        """Reset container completely"""
        self._instances.clear()
        self._factories.clear()
        self._singletons.clear()


# Global DI container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    Get global DI container instance

    Returns:
        DIContainer instance
    """
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def initialize_dependencies(app: Flask):
    """
    Initialize application dependencies

    This function registers all dependencies in the DI container.
    Should be called once during application startup.

    Args:
        app: Flask application instance
    """
    container = get_container()

    # Register database session
    container.register_instance('db_session', db.session)

    # Register repositories
    def create_user_repository():
        from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
        return UserRepositoryImpl(container.get('db_session'))

    def create_oauth_token_repository():
        from app.repositories.implementations.OAuthTokenRepositoryImpl import OAuthTokenRepositoryImpl
        return OAuthTokenRepositoryImpl(container.get('db_session'))

    container.register_singleton('user_repository', create_user_repository)
    container.register_singleton('oauth_token_repository', create_oauth_token_repository)

    # Register services
    def create_user_service():
        from app.services.implementations.UserServiceImpl import UserServiceImpl
        return UserServiceImpl(container.get('user_repository'))

    def create_auth_service():
        from app.services.implementations.AuthServiceImpl import AuthServiceImpl
        return AuthServiceImpl(
            container.get('user_repository'),
            container.get('oauth_token_repository')
        )

    container.register_singleton('user_service', create_user_service)
    container.register_singleton('auth_service', create_auth_service)

    # Register communication layer
    def create_service_communication():
        from app.communication import CommunicationFactory
        return CommunicationFactory.create_service_communication(
            service_instance=container.get('user_service')
        )

    def create_repository_communication():
        from app.communication import CommunicationFactory
        return CommunicationFactory.create_repository_communication(
            repository_instance=container.get('user_repository')
        )

    # Communication layer is singleton in monolithic mode,
    # but could be transient in distributed modes
    container.register_singleton('service_communication', create_service_communication)
    container.register_singleton('repository_communication', create_repository_communication)


def get_service_communication():
    """
    Get service communication layer from DI container

    Returns:
        ServiceCommunicationInterface implementation
    """
    return get_container().get('service_communication')


def get_repository_communication():
    """
    Get repository communication layer from DI container

    Returns:
        RepositoryCommunicationInterface implementation
    """
    return get_container().get('repository_communication')


def get_user_service():
    """
    Get user service from DI container

    Returns:
        UserServiceImpl instance
    """
    return get_container().get('user_service')


def get_auth_service():
    """
    Get auth service from DI container

    Returns:
        AuthServiceImpl instance
    """
    return get_container().get('auth_service')


def get_user_repository():
    """
    Get user repository from DI container

    Returns:
        UserRepositoryImpl instance
    """
    return get_container().get('user_repository')
