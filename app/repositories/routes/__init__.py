"""
Repository Layer HTTP Routes
Expose repository operations as HTTP endpoints for Service Layer in microservices mode
"""
from app.repositories.routes.user_repository_routes import user_repository_bp

__all__ = ['user_repository_bp']
