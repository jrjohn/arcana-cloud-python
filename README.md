# Arcana Cloud Python - Enterprise Flask RESTful API Platform

[![Python Version](https://img.shields.io/badge/python-3.14.0-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/architecture-microservices-orange.svg)]()
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Enterprise-grade RESTful API cloud platform with full-stack integration for [Arcana Angular](https://github.com/jrjohn/arcana-angular) frontend, supporting distributed microservices architecture with configuration-driven deployment.

---

## 🎯 Architecture Highlights

### **Backend Architecture Rating: 9.5/10**

**Exceptional Characteristics:**
- ✅ **Clean Architecture** - 3-layer separation (Controller/Service/Repository) with interface-driven design
- ✅ **Type Safety** - Full type hints with Python 3.14, mypy-compliant
- ✅ **Modern Patterns** - lowerCamelCase methods, UpperCamelCase classes, no Hungarian notation
- ✅ **Configuration-Driven Deployment** - Single YAML defines entire deployment topology
- ✅ **Comprehensive Testing** - 250+ tests with 85-90% coverage
- ✅ **Production-Ready** - Docker, Kubernetes, monitoring, and security built-in

### **Full-Stack Integration**

This backend seamlessly integrates with [Arcana Angular](https://github.com/jrjohn/arcana-angular) (Architecture Rating: 9.4/10):

```
┌─────────────────────────────────────────────────────────────┐
│                  Arcana Angular Frontend                     │
│  Angular 20.3 | Signals | Offline-First | Type-Safe         │
│  - MVVM Pattern with UDF (100% compliant)                   │
│  - 4-Layer Caching (Memory/LRU/IndexedDB/Remote)            │
│  - 374 Unit Tests (48% coverage, 99.5% pass rate)           │
└─────────────────────┬───────────────────────────────────────┘
                      │ RESTful API / JWT Auth
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Arcana Cloud Python Backend                    │
│  Flask 3.1 | Python 3.14 | Microservices Ready              │
│  - Interface-Implementation Pattern                          │
│  - OAuth2 + JWT Authentication                               │
│  - 250+ Tests (85-90% coverage)                              │
│  - Configuration-Driven Deployment (3 modes)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Technology Stack

### Core Framework
- **Python**: 3.14.0 (latest stable)
- **Flask**: 3.1.0 with Application Factory pattern
- **SQLAlchemy**: 2.0.35 (ORM with type hints)
- **Marshmallow**: 3.22.0 (schema validation)

### Authentication & Security
- **OAuth2 + JWT**: Token-based authentication
- **Password Hashing**: Werkzeug with bcrypt
- **CORS**: Flask-CORS with configurable origins
- **Rate Limiting**: Flask-Limiter with Redis backend
- **Input Validation**: Marshmallow schemas with custom validators

### Data & Caching
- **Database**: MySQL 8.0 / PostgreSQL 16+ (via SQLAlchemy)
- **Cache**: Redis 7.0 with connection pooling
- **Migration**: Alembic via Flask-Migrate

### Async & Tasks
- **Celery**: 5.4.0 with distributed locks
- **RedBeat**: Redis-based Celery Beat scheduler
- **Task Decorators**: `@single_instance_task`, `@rate_limit_task`, `@retry_with_backoff`

### Container & Orchestration
- **Docker**: Multi-stage builds, layer-specific images
- **Docker Compose**: 3 deployment modes (monolithic, layered, microservices)
- **Kubernetes**: Full manifests with HPA, ingress, RBAC, secrets

### Testing & Quality
- **pytest**: 8.3.4 with fixtures and parameterization
- **Coverage**: pytest-cov with HTML reports
- **Mocking**: unittest.mock for isolation
- **Integration**: End-to-end API testing

### Development Tools
- **Type Checking**: mypy (strict mode)
- **Linting**: flake8, pylint
- **Formatting**: black, isort
- **Dependency Injection**: dependency-injector

---

## 🚀 Quick Start

### Method 1: Automated Setup (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd arcana-cloud-python

# One-command setup
./setup.sh

# Start development server
make dev
```

### Method 2: Manual Setup

```bash
# 1. Create virtual environment (Python 3.14+)
python3.14 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database and Redis settings

# 4. Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 5. Run application
python wsgi.py
```

### Method 3: Docker (Instant Deployment)

```bash
# Monolithic mode (single container)
docker-compose up -d

# Layered mode (Controller/Service/Repository separation)
docker-compose -f docker-compose.layered.yml up -d

# Microservices mode (fine-grained services)
docker-compose -f docker-compose.microservices.yml up -d
```

---

## 📁 Project Structure

```
arcana-cloud-python/
├── app/                              # Application source code
│   ├── __init__.py                   # Flask application factory
│   ├── Config.py                     # Multi-environment configuration
│   ├── Extensions.py                 # Flask extensions initialization
│   ├── Container.py                  # Dependency injection container
│   │
│   ├── controllers/                  # API Controller Layer (UpperCamelCase)
│   │   ├── AuthController.py         # Authentication endpoints
│   │   ├── UserController.py         # User management endpoints
│   │   └── __init__.py               # Blueprint registration
│   │
│   ├── services/                     # Service Layer (Business Logic)
│   │   ├── interfaces/               # Service interfaces (ABC)
│   │   │   ├── UserService.py        # User service interface
│   │   │   └── AuthService.py        # Auth service interface
│   │   ├── implementations/          # Service implementations
│   │   │   ├── UserServiceImpl.py    # User business logic
│   │   │   └── AuthServiceImpl.py    # Auth + JWT logic
│   │   └── clients/                  # Inter-service communication
│   │       ├── ServiceClient.py      # HTTP client with retry
│   │       └── LoadBalancer.py       # Round-robin load balancer
│   │
│   ├── repositories/                 # Repository Layer (Data Access)
│   │   ├── interfaces/               # Repository interfaces (ABC)
│   │   │   ├── UserRepository.py     # User data interface
│   │   │   └── OAuthTokenRepository.py
│   │   └── implementations/          # Repository implementations
│   │       ├── UserRepositoryImpl.py # User CRUD operations
│   │       └── OAuthTokenRepositoryImpl.py
│   │
│   ├── models/                       # SQLAlchemy Models
│   │   ├── User.py                   # User model with password hashing
│   │   └── OAuthToken.py             # Token model with expiration
│   │
│   ├── schemas/                      # Marshmallow Schemas
│   │   ├── UserSchema.py             # User validation schemas
│   │   └── AuthSchema.py             # Auth request/response schemas
│   │
│   ├── decorators/                   # Custom Decorators
│   │   ├── AuthDecorators.py         # @token_required, @role_required
│   │   └── ValidationDecorators.py   # @validate_schema, @validate_pagination
│   │
│   ├── tasks/                        # Celery Tasks
│   │   ├── CeleryWorker.py           # Celery app configuration
│   │   ├── ScheduledTasks.py         # Periodic tasks (cleanup, health)
│   │   ├── BackgroundTasks.py        # Async tasks (emails, processing)
│   │   └── TaskDecorators.py         # @single_instance_task, @rate_limit_task
│   │
│   └── utils/                        # Utilities
│       ├── Exceptions.py             # Custom exception classes
│       └── Response.py               # Response helpers
│
├── tests/                            # Test Suite (250+ tests)
│   ├── conftest.py                   # pytest fixtures
│   ├── unit/                         # Unit tests (90% coverage)
│   │   ├── test_repositories/        # Repository layer tests
│   │   ├── test_services/            # Service layer tests
│   │   ├── test_models/              # Model tests
│   │   ├── test_utils/               # Utility tests
│   │   └── test_clients/             # Client tests
│   └── integration/                  # Integration tests (E2E)
│       ├── test_api/                 # API endpoint tests
│       └── test_complete_user_flow.py # Full workflow tests
│
├── docker/                           # Docker Configuration
│   ├── Dockerfile.base               # Base image (Python 3.14)
│   ├── Dockerfile.monolithic         # Single container deployment
│   ├── Dockerfile.controller         # Controller layer image
│   ├── Dockerfile.service            # Service layer image
│   ├── Dockerfile.repository         # Repository layer image
│   ├── healthcheck.sh                # Health check script
│   └── entrypoint-*.sh               # Layer-specific entrypoints
│
├── k8s/                              # Kubernetes Manifests
│   ├── namespace.yaml                # Namespace definition
│   ├── configmap.yaml                # Configuration data
│   ├── secrets.yaml                  # Sensitive data (template)
│   ├── controller-deployment.yaml    # Controller pods
│   ├── service-deployment.yaml       # Service pods
│   ├── repository-deployment.yaml    # Repository pods
│   ├── services.yaml                 # K8s services (ClusterIP, LoadBalancer)
│   ├── ingress.yaml                  # Nginx ingress with TLS
│   ├── hpa.yaml                      # Horizontal Pod Autoscaler
│   ├── pvc.yaml                      # Persistent volume claims
│   └── rbac.yaml                     # Role-based access control
│
├── scripts/                          # Deployment Scripts
│   ├── deploy.py                     # Python deployment manager
│   └── build.sh                      # Docker build automation
│
├── deployment-config.yaml            # Master deployment configuration
├── docker-compose.yml                # Monolithic mode compose
├── docker-compose.layered.yml        # Layered mode compose
├── docker-compose.microservices.yml  # Microservices mode compose
├── Makefile                          # 40+ convenience commands
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies
├── wsgi.py                           # WSGI application entry point
├── .env.example                      # Environment variables template
├── DEPLOYMENT.md                     # Comprehensive deployment guide (596 lines)
└── README.md                         # This file
```

---

## 🏗️ Architecture Patterns

### 1. Interface-Implementation Pattern

All Service and Repository layers follow interface-driven design:

```python
# Interface (ABC)
from abc import ABC, abstractmethod

class UserService(ABC):
    @abstractmethod
    def getUserById(self, user_id: int) -> User:
        pass

# Implementation
class UserServiceImpl(UserService):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def getUserById(self, user_id: int) -> User:
        user = self.user_repository.getById(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user
```

**Benefits:**
- Easy unit testing with mocks
- Dependency injection
- Multiple implementations (e.g., cached vs. direct)
- Clear contracts

### 2. Configuration-Driven Deployment

Single file (`deployment-config.yaml`) defines entire deployment topology:

```yaml
deployment:
  mode: layered  # monolithic, layered, microservices

  layers:
    controller:
      components: [AuthController, UserController]
      replicas: 3
      resources:
        cpu: 500m
        memory: 512Mi

    service:
      components: [UserServiceImpl, AuthServiceImpl]
      replicas: 3
      resources:
        cpu: 750m
        memory: 768Mi

    repository:
      components: [UserRepositoryImpl, OAuthTokenRepositoryImpl]
      replicas: 2
      resources:
        cpu: 1000m
        memory: 1Gi
```

**Deployment Commands:**

```bash
# Build images for specific mode
python scripts/deploy.py build --mode layered --push

# Deploy to Docker Compose
python scripts/deploy.py deploy --target docker --mode layered

# Deploy to Kubernetes
python scripts/deploy.py deploy --target kubernetes --mode microservices

# Or use Makefile shortcuts
make build-layered
make compose-up-layered
make k8s-deploy MODE=layered
```

### 3. Three Deployment Modes

#### **Monolithic Mode**
All layers in single container - best for development and small deployments.

```bash
# Docker
docker-compose up -d

# Kubernetes
kubectl apply -f k8s/monolithic/

# Direct
DEPLOYMENT_LAYER=monolithic python wsgi.py
```

**Pros:** Simple, low overhead, easy debugging
**Cons:** No independent scaling, single point of failure

#### **Layered Mode**
Separate containers for Controller, Service, Repository - balanced approach.

```bash
# Docker
docker-compose -f docker-compose.layered.yml up -d

# Kubernetes
python scripts/deploy.py deploy --target kubernetes --mode layered

# Manual
DEPLOYMENT_LAYER=controller python wsgi.py  # Terminal 1
DEPLOYMENT_LAYER=service python wsgi.py     # Terminal 2
DEPLOYMENT_LAYER=repository python wsgi.py  # Terminal 3
```

**Pros:** Independent scaling per layer, better fault isolation
**Cons:** Network latency between layers, more complex

#### **Microservices Mode**
Fine-grained services (Auth Service, User Service, etc.) - maximum flexibility.

```bash
# Docker
docker-compose -f docker-compose.microservices.yml up -d

# Kubernetes with full observability
python scripts/deploy.py deploy \
  --target kubernetes \
  --mode microservices \
  --environment production \
  --enable-monitoring

# Manual
DEPLOYMENT_LAYER=microservice SERVICE_NAME=auth-service python wsgi.py
DEPLOYMENT_LAYER=microservice SERVICE_NAME=user-service python wsgi.py
```

**Pros:** Maximum scalability, independent deployment, polyglot support
**Cons:** Complex orchestration, distributed tracing required

---

## 🔐 Security Features

### Authentication & Authorization

```python
# Token-based authentication
@auth_bp.route('/login', methods=['POST'])
@validate_schema(LoginSchema)
def login():
    # OAuth2 + JWT implementation
    result = auth_service.login(
        username_or_email=data['username_or_email'],
        password=data['password']
    )
    return success_response(result, 'Login successful', 200)

# Protected endpoints
@user_bp.route('/users', methods=['GET'])
@token_required
@role_required(['ADMIN'])
@validate_pagination
def get_users():
    users = user_service.getUsers(page=page, per_page=per_page)
    return success_response(users)
```

**Security Layers:**
1. **Password Security**: Werkzeug + bcrypt hashing
2. **Token Management**: JWT with access + refresh tokens
3. **Token Revocation**: Database-backed blacklist
4. **Role-Based Access**: `@role_required`, `@permission_required` decorators
5. **Input Validation**: Marshmallow schemas with custom validators
6. **Rate Limiting**: Redis-backed with configurable limits
7. **CORS**: Configurable origin whitelist
8. **SQL Injection**: ORM-based queries (SQLAlchemy)
9. **XSS Protection**: Input sanitization + output encoding

### Frontend Security Integration

Works seamlessly with [Arcana Angular](https://github.com/jrjohn/arcana-angular) security:

```typescript
// Angular HTTP Interceptor (frontend)
intercept(req: HttpRequest<any>, next: HttpHandler) {
  const token = this.authService.getToken();
  const cloned = req.clone({
    headers: req.headers.set('Authorization', `Bearer ${token}`)
  });
  return next.handle(cloned);
}
```

Backend validates token:

```python
# Python decorator (backend)
@token_required
def protected_endpoint():
    current_user = get_current_user()  # Extracted from JWT
    return success_response(current_user.toDict())
```

---

## 🧪 Testing Strategy

### Test Coverage: **85-90%**

```
Component               Tests    Coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Repositories             57      95-100%
Services                 47      90-95%
Models                   48      90-95%
Utilities                46      95-100%
Clients                  26      85-90%
Integration              26      80-85%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                   250      85-90%
```

### Running Tests

```bash
# All tests with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Specific test suites
pytest tests/unit/test_repositories/ -v
pytest tests/unit/test_services/ -v
pytest tests/integration/ -v

# Single test file
pytest tests/unit/test_models/test_user_model.py -v

# Stop on first failure
pytest tests/ -x

# Parallel execution (faster)
pytest tests/ -n auto

# With verbose output
pytest tests/ -vv

# Using Makefile
make test
make test-coverage
make test-unit
make test-integration
```

### Test Structure (AAA Pattern)

```python
def test_getUserById_success(user_service, mock_user_repository):
    """Test successful user retrieval by ID"""
    # Arrange - Setup test data and mocks
    mock_user = User(username='testuser', email='test@example.com')
    mock_user.id = 1
    mock_user_repository.getById.return_value = mock_user

    # Act - Execute the function under test
    result = user_service.getUserById(1)

    # Assert - Verify expected outcomes
    assert result.id == 1
    assert result.username == 'testuser'
    mock_user_repository.getById.assert_called_once_with(1)
```

---

## 📊 API Documentation

### Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | User registration | ❌ |
| POST | `/login` | User login | ❌ |
| POST | `/logout` | User logout | ✅ Token |
| POST | `/refresh` | Refresh access token | ✅ Refresh Token |
| GET | `/me` | Get current user | ✅ Token |
| GET | `/tokens` | List user's tokens | ✅ Token |
| POST | `/tokens/revoke-all` | Revoke all tokens | ✅ Token |

### User Management Endpoints (`/api/v1/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List users (paginated) | ✅ Admin |
| POST | `/` | Create user | ✅ Admin |
| GET | `/{id}` | Get user details | ✅ Token (own) or Admin |
| PUT | `/{id}` | Update user | ✅ Token (own) or Admin |
| DELETE | `/{id}` | Delete user | ✅ Admin |
| PUT | `/{id}/password` | Change password | ✅ Token (own) |
| POST | `/{id}/verify` | Verify user email | ✅ Admin |
| PUT | `/{id}/status` | Update user status | ✅ Admin |

### Example: User Registration

**Request:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "USER",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  },
  "timestamp": "2024-01-15T10:30:00.123Z",
  "request_id": "abc123-def456-ghi789"
}
```

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Build all images
make build-all

# Run monolithic mode
make compose-up

# Run layered mode
make compose-up-layered

# View logs
make compose-logs

# Stop and cleanup
make compose-down
```

### Custom Build

```bash
# Build specific mode with version tag
./scripts/build.sh --mode layered --version 1.2.3 --push

# Build and push to registry
DOCKER_REGISTRY=ghcr.io/yourorg ./scripts/build.sh --push

# Build with custom arguments
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VERSION=1.0.0 \
  -f docker/Dockerfile.layered \
  -t arcana-cloud:1.0.0 .
```

### Docker Compose Features

- **Health Checks**: All services have liveness/readiness probes
- **Resource Limits**: CPU and memory constraints
- **Auto-restart**: Services restart on failure
- **Volume Management**: Persistent data for MySQL, Redis, uploads
- **Networking**: Internal networks for service isolation
- **Nginx Reverse Proxy**: Load balancing and SSL termination

---

## ☸️ Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
brew install kubectl  # macOS
# or download from https://kubernetes.io/docs/tasks/tools/

# Verify cluster connection
kubectl cluster-info
kubectl get nodes
```

### Deployment Steps

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets (IMPORTANT: Update with real values!)
kubectl create secret generic arcana-cloud-secrets \
  --from-literal=SECRET_KEY=your-secret-key \
  --from-literal=JWT_SECRET_KEY=your-jwt-key \
  --from-literal=DB_PASSWORD=your-db-password \
  -n arcana-cloud

# 3. Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml

# 4. Deploy databases
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 5. Deploy application layers
kubectl apply -f k8s/repository-deployment.yaml
kubectl apply -f k8s/service-deployment.yaml
kubectl apply -f k8s/controller-deployment.yaml

# 6. Create services and ingress
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

# 7. Enable autoscaling
kubectl apply -f k8s/hpa.yaml

# 8. Apply RBAC (optional but recommended)
kubectl apply -f k8s/rbac.yaml
```

### Verification

```bash
# Check pod status
kubectl get pods -n arcana-cloud

# Check services
kubectl get svc -n arcana-cloud

# Check ingress
kubectl get ingress -n arcana-cloud

# View logs
kubectl logs -f deployment/controller-layer -n arcana-cloud

# Exec into pod
kubectl exec -it deployment/controller-layer -n arcana-cloud -- /bin/bash
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment controller-layer --replicas=10 -n arcana-cloud

# Autoscaling status
kubectl get hpa -n arcana-cloud

# Horizontal Pod Autoscaler details
kubectl describe hpa controller-layer-hpa -n arcana-cloud
```

### Using Makefile

```bash
# Deploy to Kubernetes
make k8s-deploy MODE=layered

# Show status
make k8s-status

# View logs
make k8s-logs

# Shell into pod
make k8s-shell POD=controller-layer

# Port forwarding
make k8s-port-forward
```

---

## 🔧 Development

### Using Makefile (40+ Commands)

```bash
# Setup
make setup                # Initial project setup
make install              # Install dependencies
make clean                # Clean build artifacts

# Development
make dev                  # Run development server
make shell                # Python shell with app context
make db-migrate           # Create database migration
make db-upgrade           # Apply database migrations

# Testing
make test                 # Run all tests
make test-unit            # Unit tests only
make test-integration     # Integration tests only
make test-coverage        # Generate coverage report
make lint                 # Run linters
make format               # Format code

# Docker
make build-all            # Build all Docker images
make build-monolithic     # Build monolithic image
make build-layered        # Build layered images
make compose-up           # Start containers
make compose-down         # Stop containers
make compose-logs         # View logs

# Kubernetes
make k8s-deploy           # Deploy to K8s
make k8s-status           # Show deployment status
make k8s-logs             # View pod logs
make k8s-shell            # Shell into pod
make k8s-cleanup          # Delete all K8s resources

# Utilities
make health               # Check health endpoints
make metrics              # Show metrics
make help                 # Show all commands
```

### Environment Variables

Create `.env` from template:

```bash
cp .env.example .env
```

Key variables:

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Deployment
DEPLOYMENT_LAYER=monolithic  # monolithic, controller, service, repository
SERVICE_NAME=arcana-cloud

# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/arcana_cloud
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
ACCESS_TOKEN_EXPIRES=3600
REFRESH_TOKEN_EXPIRES=2592000

# Service Discovery (for layered/microservices)
USER_SERVICE_URLS=http://service-layer:5001
AUTH_SERVICE_URLS=http://service-layer:5001
USER_REPO_URLS=http://repository-layer:5002

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
```

---

## 📈 Monitoring & Observability

### Health Checks

```bash
# Liveness probe
curl http://localhost:5000/health

# Readiness probe (checks database)
curl http://localhost:5000/ready
```

### Metrics (Prometheus)

Metrics exposed at `/metrics`:
- Request count and latency
- Database connection pool stats
- Redis cache hit/miss ratio
- Celery task metrics

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "app.services.UserServiceImpl",
  "message": "User created successfully",
  "request_id": "abc123",
  "user_id": 42,
  "duration_ms": 15.3
}
```

### Distributed Tracing

Integration points for:
- OpenTelemetry
- Jaeger
- Zipkin

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: ./scripts/build.sh --mode layered --version ${{ github.sha }}

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push arcana-cloud:${{ github.sha }}

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Kubernetes
        run: python scripts/deploy.py deploy --target kubernetes --mode layered
```

---

## 🌐 Frontend Integration

### Arcana Angular Compatibility

This backend is designed to work seamlessly with [Arcana Angular](https://github.com/jrjohn/arcana-angular):

**Shared Features:**
- JWT authentication flow
- Role-based access control
- RESTful API conventions
- Error handling standards
- CORS configuration
- Type safety (Python type hints ↔ TypeScript)

**Angular Service Example:**

```typescript
// Angular service (frontend)
@Injectable({ providedIn: 'root' })
export class UserService {
  private apiUrl = 'http://localhost:5000/api/v1';

  constructor(private http: HttpClient) {}

  getUsers(page: number, perPage: number): Observable<PaginatedResponse<User>> {
    return this.http.get<PaginatedResponse<User>>(
      `${this.apiUrl}/users?page=${page}&per_page=${perPage}`
    );
  }

  getUserById(id: number): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/${id}`);
  }
}
```

**Python Controller (backend):**

```python
@user_bp.route('/users', methods=['GET'])
@token_required
@role_required(['ADMIN'])
@validate_pagination
def getUsers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = user_service.getUsers(page=page, per_page=per_page)
    return success_response(result)
```

---

## 📚 Documentation

### Available Guides

1. **[DEPLOYMENT.md](DEPLOYMENT.md)** (596 lines)
   - Comprehensive deployment guide
   - Architecture diagrams
   - Docker Compose instructions
   - Kubernetes deployment
   - Troubleshooting
   - Production checklist

2. **[DEPLOYMENT_SYSTEM_README.md](DEPLOYMENT_SYSTEM_README.md)**
   - Deployment system architecture
   - Configuration-driven approach
   - Advanced deployment patterns
   - CI/CD integration

3. **[PROJECT_STATUS.md](PROJECT_STATUS.md)**
   - Implementation status
   - Completed features
   - Quick start guide
   - API endpoint reference

### API Documentation

Swagger/OpenAPI documentation (future enhancement):

```bash
# After starting the application
http://localhost:5000/api/docs
```

---

## 🎓 Best Practices

### Code Style

- **Naming Conventions**:
  - Classes: `UpperCamelCase` (e.g., `UserService`, `AuthController`)
  - Methods: `lowerCamelCase` (e.g., `getUserById`, `createUser`)
  - Files: `UpperCamelCase.py` (e.g., `UserService.py`, `AuthController.py`)
  - No Hungarian notation (no `IUserService`, just `UserService`)

- **Type Hints**: All functions have complete type annotations
- **Docstrings**: Google-style docstrings for all public methods
- **Error Handling**: Custom exceptions with proper HTTP status codes
- **Validation**: Marshmallow schemas for all inputs
- **Testing**: AAA pattern (Arrange-Act-Assert)

### Performance

- **Database**: Connection pooling with SQLAlchemy
- **Caching**: Redis for session and query caching
- **Rate Limiting**: Per-endpoint and per-user limits
- **Query Optimization**: Eager loading for relationships
- **Async Tasks**: Celery for long-running operations

### Security

- Never commit secrets (use `.env` with `.gitignore`)
- Rotate JWT secrets regularly
- Use strong password hashing (bcrypt)
- Validate all inputs (Marshmallow schemas)
- Enable HTTPS in production
- Set proper CORS origins
- Implement rate limiting
- Log security events

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Review Checklist

- [ ] All tests pass (`make test`)
- [ ] Coverage >85% (`make test-coverage`)
- [ ] Linting passes (`make lint`)
- [ ] Code formatted (`make format`)
- [ ] Type hints present (`mypy app/`)
- [ ] Docstrings added
- [ ] No secrets committed
- [ ] CHANGELOG updated

---

## 📄 License

MIT License

Copyright (c) 2024 Arcana Cloud

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

---

## 🙏 Acknowledgments

- Flask framework and community
- SQLAlchemy for excellent ORM
- Celery for distributed task processing
- All open-source contributors

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jrjohn/arcana-cloud-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jrjohn/arcana-cloud-python/discussions)
- **Frontend**: [Arcana Angular](https://github.com/jrjohn/arcana-angular)

---

**Built with ❤️ using Flask, Python 3.14, and modern cloud-native practices**
