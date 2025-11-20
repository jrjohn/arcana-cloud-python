"""Repository interfaces package"""
from app.repositories.interfaces.UserRepository import UserRepository
from app.repositories.interfaces.OAuthTokenRepository import OAuthTokenRepository

__all__ = [
    'UserRepository',
    'OAuthTokenRepository'
]
