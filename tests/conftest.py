"""
Pytest Configuration and Fixtures
pytest configuration and test fixtures
"""
import pytest
import os
from flask import Flask
from app import create_app
from app.extensions import db as _db
from app.models.user import User, UserRole
from app.models.oauth_token import OAuthToken

# Test constants (SonarQube S1192 - avoid string literal duplication)
LOGIN_ENDPOINT = LOGIN_ENDPOINT
REGISTER_ENDPOINT = REGISTER_ENDPOINT
AUTH_ME_ENDPOINT = AUTH_ME_ENDPOINT
TEST_USER_EMAIL = TEST_USER_EMAIL
ADMIN_USER_EMAIL = ADMIN_USER_EMAIL
CONTENT_TYPE_JSON = CONTENT_TYPE_JSON


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
            if deployment_mode == 'monolithic':
                # Direct database cleanup for monolithic mode
                users_to_delete = db_session.session.query(User).filter(
                    ~User.username.in_(['testuser', 'admin'])
                ).all()

                for user in users_to_delete:
                    db_session.session.delete(user)

                db_session.session.commit()
            # For microservices/layered mode, cleanup happens between test runs
            # via the benchmark script, not per-test (to avoid API overhead)
        except Exception:
            db_session.session.rollback()

        # In layered/microservices mode, don't drop tables
        # The database is shared with external service processes
        # Only clean data in monolithic mode
        if deployment_mode == 'monolithic':
            db_session.session.rollback()


@pytest.fixture(scope='function')
def sample_user(app, db, client) -> User:
    """Create sample user (function-scoped to ensure availability for each test)"""
    import logging
    from app.models.user import UserStatus
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode == 'microservices':
        # In microservices mode, try to log in first
        # If login fails, recreate the user via registration endpoint
        logging.info("[FIXTURE] sample_user: Attempting login in microservices mode")
        login_response = client.post(LOGIN_ENDPOINT, json={
            'username_or_email': 'testuser',
            'password': 'TestPass123'
        })

        logging.info(f"[FIXTURE] Login response status: {login_response.status_code}")

        # If login fails, recreate the user via registration
        if login_response.status_code != 200:
            logging.warning(f"[FIXTURE] Login failed, attempting to recreate user via registration")
            register_response = client.post(REGISTER_ENDPOINT, json={
                'username': 'testuser',
                'email': TEST_USER_EMAIL,
                'password': 'TestPass123',
                'first_name': 'Test',
                'last_name': 'User'
            })
            logging.info(f"[FIXTURE] Registration response status: {register_response.status_code}")

            if register_response.status_code == 201:
                logging.info("[FIXTURE] User recreated successfully, attempting login again")
                login_response = client.post(LOGIN_ENDPOINT, json={
                    'username_or_email': 'testuser',
                    'password': 'TestPass123'
                })
                logging.info(f"[FIXTURE] Second login response status: {login_response.status_code}")
            else:
                logging.error(f"[FIXTURE] Registration failed: {register_response.json}")

        if login_response.status_code == 200:
            logging.info(f"[FIXTURE] Login response data: {login_response.json}")
            access_token = login_response.json['data']['access_token']
            logging.info(f"[FIXTURE] Access token obtained: {access_token[:50]}...")

            # Get current user to fetch the ID
            logging.info("[FIXTURE] Fetching current user via /api/v1/auth/me")
            me_response = client.get(AUTH_ME_ENDPOINT, headers={
                'Authorization': f'Bearer {access_token}'
            })

            logging.info(f"[FIXTURE] /auth/me response status: {me_response.status_code}")
            logging.info(f"[FIXTURE] /auth/me response data: {me_response.json}")

            if me_response.status_code == 200:
                user_data = me_response.json['data']
                user_id = user_data['id']
                logging.info(f"[FIXTURE] Successfully got user ID: {user_id}")

                # Create a mock user object with the actual ID
                class MockUser:
                    def __init__(self, user_id):
                        self.id = user_id
                        self.username = 'testuser'
                        self.email = TEST_USER_EMAIL
                        self.password = 'TestPass123'
                        self.role = UserRole.USER
                        self.first_name = 'Test'
                        self.last_name = 'User'

                return MockUser(user_id)
            else:
                logging.error(f"[FIXTURE] /auth/me failed with status {me_response.status_code}")
        else:
            logging.error(f"[FIXTURE] All attempts to get user failed")

        # Fallback: create mock user without ID
        logging.warning("[FIXTURE] Falling back to MockUser with id=None")
        class MockUser:
            def __init__(self):
                self.id = None
                self.username = 'testuser'
                self.email = TEST_USER_EMAIL
                self.password = 'TestPass123'
                self.role = UserRole.USER
                self.first_name = 'Test'
                self.last_name = 'User'

        return MockUser()

    # Monolithic/layered mode: use direct database access
    with app.app_context():
        # Always check if user exists first
        existing_user = db.session.query(User).filter_by(username='testuser').first()
        if existing_user:
            # Reset user to active status and correct password in case previous test modified it
            existing_user.setPassword('TestPass123')  # Use setPassword() method to properly hash
            existing_user.status = UserStatus.ACTIVE  # Ensure active
            existing_user.is_active = True
            existing_user.first_name = 'Test'
            existing_user.last_name = 'User'
            db.session.commit()
            db.session.refresh(existing_user)
            return existing_user

        # Create new user if doesn't exist
        user = User(
            username='testuser',
            email=TEST_USER_EMAIL,
            password='TestPass123',
            role=UserRole.USER,
            first_name='Test',
            last_name='User'
        )

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture(scope='function')
def admin_user(app, db, client) -> User:
    """Create admin user (function-scoped to ensure availability for each test)"""
    from app.models.user import UserStatus
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode == 'microservices':
        # In microservices mode, admin user already exists from fixture population
        # Get user ID by logging in and fetching current user info
        login_response = client.post(LOGIN_ENDPOINT, json={
            'username_or_email': 'admin',
            'password': 'AdminPass123'
        })

        if login_response.status_code == 200:
            access_token = login_response.json['data']['access_token']

            # Get current user to fetch the ID
            me_response = client.get(AUTH_ME_ENDPOINT, headers={
                'Authorization': f'Bearer {access_token}'
            })

            if me_response.status_code == 200:
                user_data = me_response.json['data']

                # Create a mock user object with the actual ID
                class MockUser:
                    def __init__(self, user_id):
                        self.id = user_id
                        self.username = 'admin'
                        self.email = ADMIN_USER_EMAIL
                        self.password = 'AdminPass123'
                        self.role = UserRole.ADMIN
                        self.first_name = 'Admin'
                        self.last_name = 'User'

                return MockUser(user_data['id'])

        # Fallback: create mock user without ID
        class MockUser:
            def __init__(self):
                self.id = None
                self.username = 'admin'
                self.email = ADMIN_USER_EMAIL
                self.password = 'AdminPass123'
                self.role = UserRole.ADMIN
                self.first_name = 'Admin'
                self.last_name = 'User'

        return MockUser()

    # Monolithic/layered mode: use direct database access
    with app.app_context():
        # Always check if user exists first
        existing_user = db.session.query(User).filter_by(username='admin').first()
        if existing_user:
            # Reset user to active status and correct password in case previous test modified it
            existing_user.setPassword('AdminPass123')  # Use setPassword() method to properly hash
            existing_user.status = UserStatus.ACTIVE  # Ensure active
            existing_user.is_active = True
            existing_user.first_name = 'Admin'
            existing_user.last_name = 'User'
            db.session.commit()
            db.session.refresh(existing_user)
            return existing_user

        # Create new user if doesn't exist
        user = User(
            username='admin',
            email=ADMIN_USER_EMAIL,
            password='AdminPass123',
            role=UserRole.ADMIN,
            first_name='Admin',
            last_name='User'
        )

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture(scope='function')
def sample_token(db, sample_user, client) -> OAuthToken:
    """Create sample token"""
    import logging
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode in ['layered', 'microservices']:
        # In layered/microservices mode, use API endpoint to login
        logging.info("[FIXTURE] sample_token: Attempting login in layered/microservices mode")
        response = client.post(LOGIN_ENDPOINT, json={
            'username_or_email': 'testuser',
            'password': 'TestPass123'
        })

        logging.info(f"[FIXTURE] sample_token: Login response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json
            logging.info(f"[FIXTURE] sample_token: Login successful, got access token: {data['data']['access_token'][:50]}...")
            # Create a mock token object for compatibility
            class MockToken:
                def __init__(self, access_token, refresh_token=None):
                    self.access_token = access_token
                    self.refresh_token = refresh_token
            mock_token = MockToken(
                data['data']['access_token'],
                data['data'].get('refresh_token')
            )
            logging.info(f"[FIXTURE] sample_token: Created MockToken with access_token: {mock_token.access_token[:50]}...")
            return mock_token
        else:
            logging.error(f"[FIXTURE] sample_token: Login failed with status {response.status_code}: {response.json}")
            return None

    # Monolithic mode: use direct service access
    from app.services.implementations.auth_service_impl import AuthServiceImpl
    from app.repositories.implementations.user_repository_impl import UserRepositoryImpl
    from app.repositories.implementations.oauth_token_repository_impl import OAuthTokenRepositoryImpl

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
    import logging
    if sample_token is None:
        logging.error("[FIXTURE] auth_headers: sample_token is None!")
        return {
            'Content-Type': CONTENT_TYPE_JSON
        }

    logging.info(f"[FIXTURE] auth_headers: Creating headers with token: {sample_token.access_token[:50]}...")
    headers = {
        'Authorization': f'Bearer {sample_token.access_token}',
        'Content-Type': CONTENT_TYPE_JSON
    }
    logging.info(f"[FIXTURE] auth_headers: Headers created successfully")
    return headers


@pytest.fixture(scope='function')
def admin_auth_headers(db, admin_user, client) -> dict:
    """Create admin authentication headers"""
    import logging
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'monolithic')

    if deployment_mode in ['layered', 'microservices']:
        # In layered/microservices mode, use API endpoint to login
        logging.info("[FIXTURE] admin_auth_headers: Attempting admin login in layered/microservices mode")
        response = client.post(LOGIN_ENDPOINT, json={
            'username_or_email': 'admin',
            'password': 'AdminPass123'
        })

        logging.info(f"[FIXTURE] admin_auth_headers: Login response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json
            access_token = data["data"]["access_token"]
            logging.info(f"[FIXTURE] admin_auth_headers: Got admin access token: {access_token[:50]}...")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': CONTENT_TYPE_JSON
            }
            logging.info(f"[FIXTURE] admin_auth_headers: Headers created successfully")
            return headers
        else:
            logging.error(f"[FIXTURE] admin_auth_headers: Login failed with status {response.status_code}: {response.json}")
            return {
                'Content-Type': CONTENT_TYPE_JSON
            }

    # Monolithic mode: use direct service access
    from app.services.implementations.auth_service_impl import AuthServiceImpl
    from app.repositories.implementations.user_repository_impl import UserRepositoryImpl
    from app.repositories.implementations.oauth_token_repository_impl import OAuthTokenRepositoryImpl

    user_repo = UserRepositoryImpl(db.session)
    token_repo = OAuthTokenRepositoryImpl(db.session)
    auth_service = AuthServiceImpl(user_repo, token_repo)

    result = auth_service.login(
        username_or_email='admin',
        password='AdminPass123'
    )

    return {
        'Authorization': f'Bearer {result["access_token"]}',
        'Content-Type': CONTENT_TYPE_JSON
    }
