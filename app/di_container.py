"""
Dependency Injection Container
Manages dependency injection for the entire application
"""
from typing import Dict, Any, Optional, Callable
from flask import Flask
from app.extensions import db


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


def initialize_dependencies(_app: Flask):
    """
    Initialize application dependencies

    This function registers all dependencies in the DI container.
    Should be called once during application startup.

    Args:
        app: Flask application instance
    """
    import os
    container = get_container()

    # Register database session
    container.register_instance('db_session', db.session)

    # Check deployment mode
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic').lower()

    # Register repositories
    def create_user_repository():
        deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic').lower()

        if deployment_mode == 'microservices' and deployment_layer != 'repository':
            # In microservices mode (Service/Controller layer), use gRPC or HTTP client
            communication_protocol = os.getenv('COMMUNICATION_PROTOCOL', 'http').lower()
            if communication_protocol == 'grpc':
                from app.repositories.clients.grpc_user_repository_client import GRPCUserRepositoryClient
                return GRPCUserRepositoryClient()
            else:
                from app.repositories.clients.http_user_repository_client import HTTPUserRepositoryClient
                return HTTPUserRepositoryClient()
        else:
            # In monolithic/layered mode OR repository layer, use direct database access
            from app.repositories.implementations.user_repository_impl import UserRepositoryImpl
            return UserRepositoryImpl(container.get('db_session'))

    def create_oauth_token_repository():
        from app.repositories.implementations.oauth_token_repository_impl import OAuthTokenRepositoryImpl
        return OAuthTokenRepositoryImpl(container.get('db_session'))

    container.register_singleton('user_repository', create_user_repository)
    container.register_singleton('oauth_token_repository', create_oauth_token_repository)

    # Register DAO layer (wraps repositories; Services depend on DAOs, not Repositories directly)
    def create_user_dao():
        from app.dao.impl.user_dao_impl import UserDaoImpl
        return UserDaoImpl(container.get('user_repository'))

    def create_oauth_token_dao():
        from app.dao.impl.oauth_token_dao_impl import OAuthTokenDaoImpl
        return OAuthTokenDaoImpl(container.get('oauth_token_repository'))

    container.register_singleton('user_dao', create_user_dao)
    container.register_singleton('oauth_token_dao', create_oauth_token_dao)

    # Register services
    def create_user_service():
        from app.services.implementations.user_service_impl import UserServiceImpl
        return UserServiceImpl(container.get('user_dao'))

    def create_auth_service():
        # Auth service is always local - uses direct implementation with DAOs
        # In microservices mode, it uses gRPC repository clients (via DAO layer)
        # This keeps authentication centralized in the controller layer
        from app.services.implementations.auth_service_impl import AuthServiceImpl
        return AuthServiceImpl(
            container.get('user_dao'),
            container.get('oauth_token_dao'),
        )

    container.register_singleton('user_service', create_user_service)
    container.register_singleton('auth_service', create_auth_service)

    # Register communication layer
    def create_service_communication():
        import os
        from app.communication import CommunicationFactory

        deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic').lower()
        deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic').lower()

        # Only create service instance if we're NOT in microservices/controller mode
        # In microservices/controller mode, we should use HTTP to reach Service Layer
        service_instance = None
        if not (deployment_mode == 'microservices' and deployment_layer == 'controller'):
            service_instance = container.get('user_service')

        return CommunicationFactory.create_service_communication(
            service_instance=service_instance
        )

    def create_repository_communication():
        import os
        from app.communication import CommunicationFactory

        deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic').lower()
        deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic').lower()

        # Only create repository instance if we're NOT in microservices/service mode
        # In microservices/service mode, we should use HTTP to reach Repository Layer
        repository_instance = None
        if not (deployment_mode == 'microservices' and deployment_layer == 'service'):
            repository_instance = container.get('user_repository')

        return CommunicationFactory.create_repository_communication(
            repository_instance=repository_instance
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


def get_user_dao():
    """
    Get user DAO from DI container.

    Returns:
        UserDaoImpl instance (implements UserDao)
    """
    return get_container().get('user_dao')


def get_oauth_token_dao():
    """
    Get OAuth token DAO from DI container.

    Returns:
        OAuthTokenDaoImpl instance (implements OAuthTokenDao)
    """
    return get_container().get('oauth_token_dao')
