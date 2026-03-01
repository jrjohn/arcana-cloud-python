"""
OAuth Token Repository Implementation
OAuth Token Repository implementation
"""
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.oauth_token import OAuthToken
from app.repositories.oauth_token_repository import OAuthTokenRepository
from app.utils.exceptions import DatabaseError, NotFoundError


class OAuthTokenRepositoryImpl(OAuthTokenRepository):
    """OAuth Token Repository implementation"""

    def __init__(self, session: Session):
        """
        Initialize

        Args:
            session: Database session
        """
        self.session = session

    def create(self, token: OAuthToken) -> OAuthToken:
        """Create token"""
        try:
            self.session.add(token)
            self.session.commit()
            self.session.refresh(token)
            return token
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to create token: {str(e)}")

    def getByAccessToken(self, access_token: str) -> Optional[OAuthToken]:
        """Get by access token"""
        try:
            return self.session.query(OAuthToken).filter(
                OAuthToken.access_token == access_token
            ).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get token by access token: {str(e)}")

    def getByRefreshToken(self, refresh_token: str) -> Optional[OAuthToken]:
        """Get by refresh token"""
        try:
            return self.session.query(OAuthToken).filter(
                OAuthToken.refresh_token == refresh_token
            ).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get token by refresh token: {str(e)}")

    def getByUserId(self, user_id: int, include_revoked: bool = False) -> List[OAuthToken]:
        """Get all tokens by user ID"""
        try:
            query = self.session.query(OAuthToken).filter(OAuthToken.user_id == user_id)

            if not include_revoked:
                query = query.filter(OAuthToken.is_revoked == False)

            return query.all()
        except Exception as e:
            raise DatabaseError(f"Failed to get tokens by user ID: {str(e)}")

    def update(self, token: OAuthToken) -> OAuthToken:
        """Update token"""
        try:
            self.session.commit()
            self.session.refresh(token)
            return token
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to update token: {str(e)}")

    def revoke(self, token_id: int) -> bool:
        """Revoke token"""
        try:
            token = self.session.query(OAuthToken).filter(OAuthToken.id == token_id).first()
            if not token:
                raise NotFoundError(f"Token with ID {token_id} not found", "OAuthToken")

            token.revoke()
            self.session.commit()
            return True
        except NotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to revoke token: {str(e)}")

    def revokeAllByUserId(self, user_id: int) -> int:
        """Revoke all tokens for user"""
        try:
            tokens = self.session.query(OAuthToken).filter(
                OAuthToken.user_id == user_id,
                OAuthToken.is_revoked == False
            ).all()

            count = 0
            for token in tokens:
                token.revoke()
                count += 1

            self.session.commit()
            return count
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to revoke all tokens: {str(e)}")

    def deleteExpired(self, before_date: Optional[datetime] = None) -> int:
        """Delete expired tokens"""
        try:
            if before_date is None:
                before_date = datetime.now(timezone.utc)

            tokens = self.session.query(OAuthToken).filter(
                OAuthToken.expires_at < before_date
            ).all()

            count = len(tokens)
            for token in tokens:
                self.session.delete(token)

            self.session.commit()
            return count
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete expired tokens: {str(e)}")

    def existsByAccessToken(self, access_token: str) -> bool:
        """Check if access token exists"""
        try:
            return self.session.query(
                self.session.query(OAuthToken).filter(
                    OAuthToken.access_token == access_token
                ).exists()
            ).scalar()
        except Exception as e:
            raise DatabaseError(f"Failed to check access token existence: {str(e)}")
