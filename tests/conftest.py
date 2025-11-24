"""
Pytest Configuration and Fixtures
pytest configuration and test fixtures
"""
import pytest
import os
from flask import Flask
from app import create_app
from app.Extensions import db as _db
from app.models.user import User, UserRole
from app.models.oauth_token import OAuthToken


@pytest.fixture(scope='session')
def app() -> Flask:
    """Create test application"""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode == 'microservices':
        # Use HTTP client for microservices mode (makes actual HTTP requests)
        from tests.http_client import HTTPTestClient
        return HTTPTestClient()

    # Use Flask test client for monolithic/layered modes
    return app.test_client()


@pytest.fixture(scope='session')
def db_session(app):
    """Create database session for the entire test session"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()


@pytest.fixture(scope='function')
def db(app, db_session):
    """Create test database per function"""
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    with app.app_context():
        yield db_session

        # Clean up test-created users after each test
        # Keep fixture users (testuser, admin) but delete all others
        try:
            # Delete all users except testuser and admin
            users_to_delete = db_session.session.query(User).filter(
                ~User.username.in_(['testuser', 'admin'])
            ).all()

            for user in users_to_delete:
                db_session.session.delete(user)

            db_session.session.commit()
        except Exception:
            db_session.session.rollback()

        # In layered/microservices mode, don't drop tables
        # The database is shared with external service processes
        # Only clean data in monolithic mode
        if deployment_mode == 'monolithic':
            db_session.session.rollback()


@pytest.fixture(scope='function')
def sample_user(app, db) -> User:
    """Create sample user (function-scoped to ensure availability for each test)"""
    from app.models.user import UserStatus

    with app.app_context():
        # Always check if user exists first
        existing_user = db.session.query(User).filter_by(username='testuser').first()
        if existing_user:
            # Reset user to active status and correct password in case previous test modified it
            existing_user.setPassword('TestPass123')  # Use setPassword() method to properly hash
            existing_user.status = UserStatus.ACTIVE  # Ensure active
            existing_user.is_active = True
            db.session.commit()
            db.session.refresh(existing_user)
            return existing_user

        # Create new user if doesn't exist
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123',
            role=UserRole.USER
        )

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture(scope='function')
def admin_user(app, db) -> User:
    """Create admin user (function-scoped to ensure availability for each test)"""
    from app.models.user import UserStatus

    with app.app_context():
        # Always check if user exists first
        existing_user = db.session.query(User).filter_by(username='admin').first()
        if existing_user:
            # Reset user to active status and correct password in case previous test modified it
            existing_user.setPassword('AdminPass123')  # Use setPassword() method to properly hash
            existing_user.status = UserStatus.ACTIVE  # Ensure active
            existing_user.is_active = True
            db.session.commit()
            db.session.refresh(existing_user)
            return existing_user

        # Create new user if doesn't exist
        user = User(
            username='admin',
            email='admin@example.com',
            password='AdminPass123',
            role=UserRole.ADMIN
        )

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture(scope='function')
def sample_token(db, sample_user, client) -> OAuthToken:
    """Create sample token"""
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode in ['layered', 'microservices']:
        # In layered/microservices mode, use API endpoint to login
        response = client.post('/api/v1/auth/login', json={
            'username_or_email': 'testuser',
            'password': 'TestPass123'
        })

        if response.status_code == 200:
            data = response.json
            # Create a mock token object for compatibility
            class MockToken:
                def __init__(self, access_token, refresh_token=None):
                    self.access_token = access_token
                    self.refresh_token = refresh_token
            return MockToken(
                data['data']['access_token'],
                data['data'].get('refresh_token')
            )

    # Monolithic mode: use direct service access
    from app.services.implementations.AuthServiceImpl import AuthServiceImpl
    from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
    from app.repositories.implementations.OAuthTokenRepositoryImpl import OAuthTokenRepositoryImpl

    user_repo = UserRepositoryImpl(db.session)
    token_repo = OAuthTokenRepositoryImpl(db.session)
    auth_service = AuthServiceImpl(user_repo, token_repo)

    result = auth_service.login(
        username_or_email='testuser',
        password='TestPass123'
    )

    token = token_repo.getByAccessToken(result['access_token'])
    return token


@pytest.fixture(scope='function')
def auth_headers(sample_token) -> dict:
    """Create authentication headers"""
    return {
        'Authorization': f'Bearer {sample_token.access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope='function')
def admin_auth_headers(db, admin_user, client) -> dict:
    """Create admin authentication headers"""
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode in ['layered', 'microservices']:
        # In layered/microservices mode, use API endpoint to login
        response = client.post('/api/v1/auth/login', json={
            'username_or_email': 'admin',
            'password': 'AdminPass123'
        })

        if response.status_code == 200:
            data = response.json
            return {
                'Authorization': f'Bearer {data["data"]["access_token"]}',
                'Content-Type': 'application/json'
            }

    # Monolithic mode: use direct service access
    from app.services.implementations.AuthServiceImpl import AuthServiceImpl
    from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
    from app.repositories.implementations.OAuthTokenRepositoryImpl import OAuthTokenRepositoryImpl

    user_repo = UserRepositoryImpl(db.session)
    token_repo = OAuthTokenRepositoryImpl(db.session)
    auth_service = AuthServiceImpl(user_repo, token_repo)

    result = auth_service.login(
        username_or_email='admin',
        password='AdminPass123'
    )

    return {
        'Authorization': f'Bearer {result["access_token"]}',
        'Content-Type': 'application/json'
    }
