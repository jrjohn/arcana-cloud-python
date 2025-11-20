"""
Dependency Injection Container
Manages all services and repository dependencies using dependency-injector
"""
from dependency_injector import containers, providers

from app.Extensions import db


class Container(containers.DeclarativeContainer):
    """DI Container, manages all dependency injection"""

    # Configuration provider
    config = providers.Configuration()

    # Database Session Factory
    db_session = providers.Callable(
        lambda: db.session
    )

    # ==================== Repositories ====================
    from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
    from app.repositories.implementations.TransactionRepositoryImpl import TransactionRepositoryImpl

    user_repository = providers.Factory(
        UserRepositoryImpl,
        session=db_session
    )

    transaction_repository = providers.Factory(
        TransactionRepositoryImpl,
        session=db_session
    )

    # ==================== Services ====================
    from app.services.implementations.UserServiceImpl import UserServiceImpl
    from app.services.implementations.AuthServiceImpl import AuthServiceImpl
    from app.services.implementations.TransactionServiceImpl import TransactionServiceImpl

    user_service = providers.Factory(
        UserServiceImpl,
        user_repository=user_repository
    )

    auth_service = providers.Factory(
        AuthServiceImpl,
        user_repository=user_repository
    )

    transaction_service = providers.Factory(
        TransactionServiceImpl,
        transaction_repository=transaction_repository
    )

    # ==================== Service Clients (for distributed mode) ====================
    from app.services.clients.ServiceClient import ServiceClient

    user_service_client = providers.Factory(
        ServiceClient,
        service_name='user-service',
        service_urls=config.USER_SERVICE_URLS
    )

    auth_service_client = providers.Factory(
        ServiceClient,
        service_name='auth-service',
        service_urls=config.AUTH_SERVICE_URLS
    )

    # ==================== Repository Clients (for distributed mode) ====================
    from app.repositories.clients.RepositoryClient import RepositoryClient

    user_repository_client = providers.Factory(
        RepositoryClient,
        repository_name='user-repository',
        repository_urls=config.USER_REPO_URLS
    )
