"""Communication Implementations Package"""
from app.communication.impl.direct_impl import (
    DirectServiceCommunicationImpl,
    DirectRepositoryCommunicationImpl
)
from app.communication.impl.http_rest_impl import (
    HTTPServiceCommunicationImpl,
    HTTPRepositoryCommunicationImpl
)
from app.communication.impl.grpc_impl import (
    GRPCServiceCommunicationImpl,
    GRPCRepositoryCommunicationImpl
)

__all__ = [
    'DirectServiceCommunicationImpl',
    'DirectRepositoryCommunicationImpl',
    'HTTPServiceCommunicationImpl',
    'HTTPRepositoryCommunicationImpl',
    'GRPCServiceCommunicationImpl',
    'GRPCRepositoryCommunicationImpl',
]
