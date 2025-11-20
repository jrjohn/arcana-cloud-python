"""
Flask Application Factory
Create Flask application using Factory Pattern
"""
from flask import Flask
from flask_cors import CORS

from app.Config import get_config
from app.Extensions import db, migrate, ma, limiter
from app.Container import Container


def create_app(config_name: str = 'development') -> Flask:
    """
    Application factory function

    Args:
        config_name: Configuration name ('development', 'testing', 'production')

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Initialize extensions
    initialize_extensions(app)

    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize dependency injection container
    container = Container()
    container.config.from_dict(app.config)
    app.container = container

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Health check endpoints
    register_health_checks(app)

    return app


def initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    limiter.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register blueprints"""
    from app.controllers import auth_bp, user_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers"""
    from app.utils.Exceptions import APIException
    from app.utils.Response import error_response

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        return error_response(error.message, error.status_code, error.error_code)

    @app.errorhandler(404)
    def handle_not_found(error):
        return error_response('Resource not found', 404, 'NOT_FOUND')

    @app.errorhandler(500)
    def handle_internal_error(error):
        return error_response('Internal server error', 500, 'INTERNAL_ERROR')


def register_health_checks(app: Flask) -> None:
    """Register health check endpoints"""
    from flask import jsonify

    @app.route('/health')
    def health():
        """Liveness check"""
        return jsonify({'status': 'healthy'}), 200

    @app.route('/ready')
    def ready():
        """Readiness check"""
        try:
            # Check database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return jsonify({'status': 'ready'}), 200
        except Exception as e:
            return jsonify({'status': 'not ready', 'error': str(e)}), 503
