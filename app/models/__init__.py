"""Data models package"""
from app.models.User import User
from app.models.OAuthToken import OAuthToken

__all__ = [
    'User',
    'OAuthToken'
]
