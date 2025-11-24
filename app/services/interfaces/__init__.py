"""Service interfaces package"""
from app.services.interfaces.user_service import UserService
from app.services.interfaces.auth_service import AuthService

__all__ = [
    'UserService',
    'AuthService'
]
