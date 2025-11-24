"""Service Layer HTTP API Routes"""
from app.services.routes.user_service_routes import user_service_bp
from app.services.routes.auth_service_routes import auth_service_bp

__all__ = ['user_service_bp', 'auth_service_bp']
