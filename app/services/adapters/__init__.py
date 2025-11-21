"""Service Adapters - Unified interface for monolithic and layered modes"""
from app.services.adapters.UserServiceAdapter import get_user_service

__all__ = ['get_user_service']
