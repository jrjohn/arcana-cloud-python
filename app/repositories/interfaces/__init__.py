"""Repository interfaces package"""
from app.repositories.interfaces.user_repository import UserRepository
from app.repositories.interfaces.oauth_token_repository import OAuthTokenRepository

__all__ = [
    'UserRepository',
    'OAuthTokenRepository'
]
