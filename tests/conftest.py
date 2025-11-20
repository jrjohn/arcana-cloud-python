"""
Pytest Configuration and Fixtures
pytest configuration and test fixtures
"""
import pytest
from flask import Flask
from app import create_app
from app.Extensions import db as _db
from app.models.User import User, UserRole
from app.models.OAuthToken import OAuthToken


@pytest.fixture(scope='session')
def app() -> Flask:
    """Create test application"""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Create test database"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def sample_user(db) -> User:
    """Create sample user"""
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
def admin_user(db) -> User:
    """Create admin user"""
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
def sample_token(db, sample_user) -> OAuthToken:
    """Create sample token"""
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

    token = token_repo.get_by_access_token(result['access_token'])
    return token


@pytest.fixture(scope='function')
def auth_headers(sample_token) -> dict:
    """Create authentication headers"""
    return {
        'Authorization': f'Bearer {sample_token.access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope='function')
def admin_auth_headers(db, admin_user) -> dict:
    """Create admin authentication headers"""
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
