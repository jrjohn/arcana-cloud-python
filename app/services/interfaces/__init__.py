"""Service interfaces package"""
from app.services.interfaces.UserService import UserService
from app.services.interfaces.AuthService import AuthService

__all__ = [
    'UserService',
    'AuthService'
]
