"""
Application Configuration Management
Supports multi-environment configuration: development, testing, production
"""
import os
from datetime import timedelta
from typing import Dict, Type


class Config:
    """Base Configuration Class"""

    # Flask core configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://user:pass@localhost:3306/arcana_cloud'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'

    # OAuth2 configuration
    OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 3600  # 1 hour
    OAUTH2_REFRESH_TOKEN_EXPIRES_IN = 2592000  # 30 days

    # Celery configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Taipei'
    CELERY_ENABLE_UTC = True

    # Distributed service configuration
    DEPLOYMENT_LAYER = os.getenv('DEPLOYMENT_LAYER', 'monolithic')  # monolithic, controller, service, repository
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'arcana-cloud')
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5000'))

    # Service discovery configuration
    USER_SERVICE_URLS = os.getenv('USER_SERVICE_URLS', 'http://localhost:5001').split(',')
    AUTH_SERVICE_URLS = os.getenv('AUTH_SERVICE_URLS', 'http://localhost:5003').split(',')
    USER_REPO_URLS = os.getenv('USER_REPO_URLS', 'http://localhost:5002').split(',')

    # API rate limiting configuration
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = 'json'  # Structured logging

    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/var/uploads')  # nosec B108


class DevelopmentConfig(Config):
    """Development Environment Configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'

    # Use DATABASE_URL from environment, with fallback to default
    # os.getenv() is evaluated at import time, so this will pick up
    # environment variables set before Python starts
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///arcana_dev.db'
    )


class TestingConfig(Config):
    """Testing Environment Configuration"""
    TESTING = True
    DEBUG = True
    # Use MySQL for testing (K8s tests require MySQL)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud'
    )
    # Disable Redis for tests (use in-memory mock if needed)
    REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production Environment Configuration"""
    DEBUG = False
    TESTING = False

    # Environment variables must be set in production
    SECRET_KEY = os.getenv('SECRET_KEY') or None
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or SECRET_KEY

    # Production environment log level
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')

    # Rate limiting can be controlled via environment variable
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() in ('true', '1', 'yes')

    @classmethod
    def validate(cls):
        """Validate production configuration"""
        if not cls.SECRET_KEY:
            raise ValueError("Production SECRET_KEY must be set")
        if not cls.JWT_SECRET_KEY:
            raise ValueError("Production JWT_SECRET_KEY must be set")


# Configuration mapping
config_map: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = 'development') -> Type[Config]:
    """
    Get configuration class

    Args:
        config_name: Configuration name

    Returns:
        Configuration class
    """
    return config_map.get(config_name, config_map['default'])
