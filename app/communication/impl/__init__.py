"""Communication Implementations Package"""
from app.communication.impl.direct_impl import (
    DirectServiceCommunication,
    DirectRepositoryCommunication
)
from app.communication.impl.http_rest_impl import (
    HTTPServiceCommunication,
    HTTPRepositoryCommunication
)
from app.communication.impl.grpc_impl import (
    GRPCServiceCommunication,
    GRPCRepositoryCommunication
)

__all__ = [
    'DirectServiceCommunication',
    'DirectRepositoryCommunication',
    'HTTPServiceCommunication',
    'HTTPRepositoryCommunication',
    'GRPCServiceCommunication',
    'GRPCRepositoryCommunication',
]
