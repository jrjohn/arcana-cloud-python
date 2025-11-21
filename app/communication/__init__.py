"""
Communication Layer Package
Abstract communication layer supporting multiple deployment modes
"""
from app.communication.factory import CommunicationFactory
from app.communication.interfaces import CommunicationInterface

__all__ = ['CommunicationFactory', 'CommunicationInterface']
