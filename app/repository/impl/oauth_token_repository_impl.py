"""
OAuthToken Repository Implementation
Delegates all persistence operations to the injected OAuthTokenDAO,
following the arcana-cloud-springboot OAuthTokenRepositoryImpl pattern.
"""
from typing import Optional, List
from datetime import datetime

from app.repository.oauth_token_repository import OAuthTokenRepository
from app.models.oauth_token import OAuthToken
# Import the underlying SQLAlchemy-based DAO (true DAO layer)
from app.repositories.interfaces.oauth_token_repository import OAuthTokenRepository as OAuthTokenDAO


class OAuthTokenRepositoryImpl(OAuthTokenRepository):
    """
    Concrete OAuth Token Repository.

    Wraps an OAuthTokenDAO so that the Service layer is decoupled
    from persistence details.  Constructor injection is used so the
    dependency can be swapped easily (e.g. in tests).
    """

    def __init__(self, token_dao: OAuthTokenDAO):
        """
        Initialize with an OAuthTokenDAO instance.

        Args:
            token_dao: Underlying DAO to delegate to
        """
        self._dao = token_dao

    # ------------------------------------------------------------------
    # BaseRepository implementation
    # ------------------------------------------------------------------

    def save(self, entity: OAuthToken) -> OAuthToken:
        """Create or update an OAuthToken."""
        if entity.id is None:
            return self._dao.create(entity)
        return self._dao.update(entity)

    def find_by_id(self, id: int) -> Optional[OAuthToken]:
        """Find a token by primary key via access-token lookup (no direct getById in dao)."""
        # The DAO does not expose getById directly; use the session-based approach
        # by searching through user tokens is impractical, so we expose a best-effort
        # implementation using the DAO's internal session if available.
        # Concrete: delegate to the impl's session when possible.
        dao = self._dao
        if hasattr(dao, 'session'):
            return dao.session.get(OAuthToken, id)  # SQLAlchemy 1.4+
        # Fallback: not supported without session access
        return None

    def find_all(self) -> List[OAuthToken]:
        """Return all tokens (not recommended for production; provided for completeness)."""
        dao = self._dao
        if hasattr(dao, 'session'):
            return dao.session.query(OAuthToken).all()
        return []

    def count(self) -> int:
        """Return total token count."""
        dao = self._dao
        if hasattr(dao, 'session'):
            from sqlalchemy import func
            return dao.session.query(func.count(OAuthToken.id)).scalar() or 0
        return 0

    def delete_by_id(self, id: int) -> bool:
        """Delete a token by its primary key."""
        dao = self._dao
        if hasattr(dao, 'session'):
            token = dao.session.get(OAuthToken, id)
            if token is None:
                return False
            dao.session.delete(token)
            dao.session.commit()
            return True
        return False

    def exists_by_id(self, id: int) -> bool:
        """Check whether a token with the given ID exists."""
        return self.find_by_id(id) is not None

    # ------------------------------------------------------------------
    # OAuthTokenRepository-specific methods
    # ------------------------------------------------------------------

    def find_by_access_token(self, access_token: str) -> Optional[OAuthToken]:
        """Find a token by its access token string."""
        return self._dao.getByAccessToken(access_token)

    def find_by_refresh_token(self, refresh_token: str) -> Optional[OAuthToken]:
        """Find a token by its refresh token string."""
        return self._dao.getByRefreshToken(refresh_token)

    def find_all_by_user_id(
        self, user_id: int, include_revoked: bool = False
    ) -> List[OAuthToken]:
        """Retrieve all tokens for a user."""
        return self._dao.getByUserId(user_id, include_revoked=include_revoked)

    def exists_by_access_token(self, access_token: str) -> bool:
        """Check whether an access token string exists in the store."""
        return self._dao.existsByAccessToken(access_token)

    def revoke(self, token_id: int) -> bool:
        """Revoke a single token by ID."""
        return self._dao.revoke(token_id)

    def revoke_all_by_user_id(self, user_id: int) -> int:
        """Revoke all active tokens owned by a user."""
        return self._dao.revokeAllByUserId(user_id)

    def delete_expired(self, before_date: Optional[datetime] = None) -> int:
        """Delete tokens that expired before the given date."""
        return self._dao.deleteExpired(before_date)
