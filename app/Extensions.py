"""
Flask Extension Initialization
Centralized management of all Flask extension instances
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis

# Database ORM
db = SQLAlchemy()

# Database migration
migrate = Migrate()

# Serialization/Deserialization
ma = Marshmallow()

# API rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Redis client (lazy initialization)
redis_client: Redis = None


def init_redis(app) -> Redis:
    """
    Initialize Redis client

    Args:
        app: Flask application instance

    Returns:
        Redis client instance
    """
    global redis_client
    redis_url = app.config.get('REDIS_URL')
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    return redis_client
