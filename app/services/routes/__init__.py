"""Service Layer HTTP API Routes"""
from app.services.routes.UserServiceRoutes import user_service_bp
from app.services.routes.AuthServiceRoutes import auth_service_bp

__all__ = ['user_service_bp', 'auth_service_bp']
