"""
OAuthToken DAO - Database access operations for OAuth tokens.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.oauth_token import OAuthToken


class OAuthTokenDao:
    """Data Access Object for OAuthToken database operations."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_token(self, token: str) -> Optional[OAuthToken]:
        return self._session.query(OAuthToken).filter(OAuthToken.token == token).first()

    def find_by_user_id(self, user_id: int) -> List[OAuthToken]:
        return self._session.query(OAuthToken).filter(OAuthToken.user_id == user_id).all()

    def save(self, token: OAuthToken) -> OAuthToken:
        self._session.add(token)
        self._session.flush()
        return token

    def delete_by_token(self, token: str) -> int:
        return self._session.query(OAuthToken).filter(OAuthToken.token == token).delete()

    def delete_expired(self) -> int:
        from datetime import datetime, timezone
        return self._session.query(OAuthToken).filter(
            OAuthToken.expires_at < datetime.now(timezone.utc)
        ).delete()
