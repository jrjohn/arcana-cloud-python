"""
Communication Factory
Factory pattern for creating appropriate communication layer based on configuration
"""
import os
from typing import Optional
from enum import Enum

from app.communication.interfaces import (
    ServiceCommunicationInterface,
    RepositoryCommunicationInterface,
    DeploymentMode,
    CommunicationProtocol
)
from app.communication.impl.direct import (
    DirectServiceCommunication,
    DirectRepositoryCommunication
)
from app.communication.impl.http_rest import (
    HTTPServiceCommunication,
    HTTPRepositoryCommunication
)
from app.communication.impl.grpc_impl import (
    GRPCServiceCommunication,
    GRPCRepositoryCommunication
)


class CommunicationFactory:
    """
    Factory for creating communication layer instances

    Automatically selects the appropriate implementation based on:
    1. DEPLOYMENT_MODE: monolithic, layered, microservices
    2. COMMUNICATION_PROTOCOL: http, grpc (optional, defaults based on mode)
    3. Current layer (DEPLOYMENT_LAYER): controller, service, repository

    Decision Matrix:
    ┌──────────────────┬──────────────┬─────────────────┬────────────────┐
    │ Deployment Mode  │ Protocol     │ Layer           │ Implementation │
    ├──────────────────┼──────────────┼─────────────────┼────────────────┤
    │ monolithic       │ direct       │ any             │ Direct         │
    ├──────────────────┼──────────────┼─────────────────┼────────────────┤
    │ layered          │ http (default)│ controller     │ HTTP           │
    │                  │              │ service         │ Direct         │
    ├──────────────────┼──────────────┼─────────────────┼────────────────┤
    │ layered          │ grpc         │ controller      │ gRPC           │
    │                  │              │ service         │ Direct         │
    ├──────────────────┼──────────────┼─────────────────┼────────────────┤
    │ microservices    │ http (default)│ any            │ HTTP           │
    ├──────────────────┼──────────────┼─────────────────┼────────────────┤
    │ microservices    │ grpc         │ any             │ gRPC           │
    └──────────────────┴──────────────┴─────────────────┴────────────────┘
    """

    @staticmethod
    def _get_deployment_mode() -> DeploymentMode:
        """Get deployment mode from environment"""
        mode_str = os.getenv('DEPLOYMENT_MODE', 'monolithic').lower()
        try:
            return DeploymentMode(mode_str)
        except ValueError:
            return DeploymentMode.MONOLITHIC

    @staticmethod
    def _get_deployment_layer() -> str:
        """Get current deployment layer from environment"""
        return os.getenv('DEPLOYMENT_LAYER', 'monolithic').lower()

    @staticmethod
    def _get_communication_protocol() -> Optional[CommunicationProtocol]:
        """Get communication protocol from environment (optional)"""
        protocol_str = os.getenv('COMMUNICATION_PROTOCOL', '').lower()
        if not protocol_str:
            return None
        try:
            return CommunicationProtocol(protocol_str)
        except ValueError:
            return None

    @staticmethod
    def _should_use_remote_communication(deployment_mode: DeploymentMode,
                                         deployment_layer: str) -> bool:
        """
        Determine if remote communication should be used

        Args:
            deployment_mode: Deployment mode (monolithic, layered, microservices)
            deployment_layer: Current layer (controller, service, repository)

        Returns:
            True if remote communication is needed
        """
        # Monolithic mode: always use direct communication
        if deployment_mode == DeploymentMode.MONOLITHIC:
            return False

        # Layered mode:
        # - Controller → Service: remote
        # - Service → Repository: direct (same container)
        if deployment_mode == DeploymentMode.LAYERED:
            return deployment_layer == 'controller'

        # Microservices mode: always remote
        if deployment_mode == DeploymentMode.MICROSERVICES:
            return True

        return False

    @staticmethod
    def _get_default_protocol(deployment_mode: DeploymentMode) -> CommunicationProtocol:
        """
        Get default communication protocol for deployment mode

        Args:
            deployment_mode: Deployment mode

        Returns:
            Default communication protocol
        """
        if deployment_mode == DeploymentMode.MONOLITHIC:
            return CommunicationProtocol.DIRECT

        # For layered and microservices, default to HTTP
        # Can be overridden by COMMUNICATION_PROTOCOL environment variable
        return CommunicationProtocol.HTTP

    @classmethod
    def create_service_communication(cls, service_instance=None) -> ServiceCommunicationInterface:
        """
        Create service communication layer (Controller → Service)

        Automatically selects implementation based on environment variables:
        - DEPLOYMENT_MODE: monolithic, layered, microservices
        - DEPLOYMENT_LAYER: controller, service, repository
        - COMMUNICATION_PROTOCOL: http, grpc (optional)
        - USER_SERVICE_URLS: Service URLs (for remote communication)

        Args:
            service_instance: Optional service instance for dependency injection.
                             If provided, will be used for DirectServiceCommunication.
                             If None, will create dependencies internally (legacy behavior).

        Returns:
            ServiceCommunicationInterface implementation

        Example:
            # Monolithic mode with DI
            service = container.get('user_service')
            comm = CommunicationFactory.create_service_communication(service_instance=service)
            → DirectServiceCommunication(service)

            # Layered mode with HTTP
            DEPLOYMENT_MODE=layered
            DEPLOYMENT_LAYER=controller
            USER_SERVICE_URLS=http://service-layer:5001
            → HTTPServiceCommunication

            # Layered mode with gRPC
            DEPLOYMENT_MODE=layered
            DEPLOYMENT_LAYER=controller
            COMMUNICATION_PROTOCOL=grpc
            USER_SERVICE_URLS=service-layer:50051
            → GRPCServiceCommunication
        """
        deployment_mode = cls._get_deployment_mode()
        protocol_override = cls._get_communication_protocol()

        # Check if remote communication is needed
        use_remote = cls._should_use_remote_communication(deployment_mode, deployment_layer)

        if not use_remote:
            # Use direct communication (monolithic mode or service layer in layered mode)
            if service_instance is None:
                # Legacy behavior: create dependencies internally
                from app.services.impl.user_service_impl import UserServiceImpl
                from app.repositories.impl.user_repository_impl import UserRepositoryImpl
                from app.extensions import db

                user_repo = UserRepositoryImpl(db.session)
                service_instance = UserServiceImpl(user_repo)

            return DirectServiceCommunication(service_instance)

        # Remote communication needed - determine protocol
        protocol = protocol_override or cls._get_default_protocol(deployment_mode)

        # Get service URLs
        service_urls_str = os.getenv('USER_SERVICE_URLS', 'http://localhost:5001')
        service_urls = [url.strip() for url in service_urls_str.split(',')]

        if protocol == CommunicationProtocol.GRPC:
            return GRPCServiceCommunication(service_urls, deployment_mode)
        else:
            return HTTPServiceCommunication(service_urls, deployment_mode)

    @classmethod
    def create_repository_communication(cls, repository_instance=None) -> RepositoryCommunicationInterface:
        """
        Create repository communication layer (Service → Repository)

        Automatically selects implementation based on environment variables:
        - DEPLOYMENT_MODE: monolithic, layered, microservices
        - DEPLOYMENT_LAYER: controller, service, repository
        - COMMUNICATION_PROTOCOL: http, grpc (optional)
        - USER_REPO_URLS: Repository URLs (for remote communication)

        Args:
            repository_instance: Optional repository instance for dependency injection.
                                If provided, will be used for DirectRepositoryCommunication.
                                If None, will create dependencies internally (legacy behavior).

        Returns:
            RepositoryCommunicationInterface implementation

        Example:
            # Monolithic mode with DI
            repo = container.get('user_repository')
            comm = CommunicationFactory.create_repository_communication(repository_instance=repo)
            → DirectRepositoryCommunication(repo)

            # Microservices mode with HTTP
            DEPLOYMENT_MODE=microservices
            DEPLOYMENT_LAYER=service
            USER_REPO_URLS=http://user-repository:5002
            → HTTPRepositoryCommunication

            # Microservices mode with gRPC
            DEPLOYMENT_MODE=microservices
            COMMUNICATION_PROTOCOL=grpc
            USER_REPO_URLS=user-repository:50052
            → GRPCRepositoryCommunication
        """
        deployment_mode = cls._get_deployment_mode()
        protocol_override = cls._get_communication_protocol()

        # In layered mode, service layer uses direct repository access
        # In microservices mode, always use remote communication
        use_remote = (deployment_mode == DeploymentMode.MICROSERVICES)

        if not use_remote:
            # Use direct communication
            if repository_instance is None:
                # Legacy behavior: create dependencies internally
                from app.repositories.impl.user_repository_impl import UserRepositoryImpl
                from app.extensions import db

                repository_instance = UserRepositoryImpl(db.session)

            return DirectRepositoryCommunication(repository_instance)

        # Remote communication needed
        protocol = protocol_override or cls._get_default_protocol(deployment_mode)

        # Get repository URLs
        repo_urls_str = os.getenv('USER_REPO_URLS', 'http://localhost:5002')
        repo_urls = [url.strip() for url in repo_urls_str.split(',')]

        if protocol == CommunicationProtocol.GRPC:
            return GRPCRepositoryCommunication(repo_urls, deployment_mode)
        else:
            return HTTPRepositoryCommunication(repo_urls, deployment_mode)

    @classmethod
    def get_communication_info(cls) -> dict:
        """
        Get current communication configuration information

        Returns:
            Dict with communication configuration details
        """
        deployment_mode = cls._get_deployment_mode()
        protocol_override = cls._get_communication_protocol()

        service_remote = cls._should_use_remote_communication(deployment_mode, deployment_layer)
        repo_remote = (deployment_mode == DeploymentMode.MICROSERVICES)

        service_protocol = protocol_override or cls._get_default_protocol(deployment_mode)
        repo_protocol = protocol_override or cls._get_default_protocol(deployment_mode)

        return {
            'deployment_mode': deployment_mode.value,
            'deployment_layer': deployment_layer,
            'communication_protocol': protocol_override.value if protocol_override else 'auto',
            'service_communication': {
                'remote': service_remote,
                'protocol': service_protocol.value,
                'urls': os.getenv('USER_SERVICE_URLS', 'N/A')
            },
            'repository_communication': {
                'remote': repo_remote,
                'protocol': repo_protocol.value,
                'urls': os.getenv('USER_REPO_URLS', 'N/A')
            }
        }
