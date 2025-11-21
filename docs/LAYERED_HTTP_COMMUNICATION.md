# Layered HTTP/REST Communication Guide

## Overview

This guide explains how the HTTP/REST communication works between Controller and Service layers in layered deployment mode.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT REQUEST                           │
│                   (External HTTP/REST)                        │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  CONTROLLER LAYER (Port 5000/5003)                          │
│  Container: controller-layer                                 │
│  ENV: DEPLOYMENT_LAYER=controller                           │
│  ENV: USER_SERVICE_URLS=http://service-layer:5001          │
├─────────────────────────────────────────────────────────────┤
│  UserController (app/controllers/UserController.py)         │
│     ↓                                                        │
│  get_user_service() → LayeredUserService                    │
│     ↓                                                        │
│  ServiceClient (HTTP/REST Client)                           │
│     ↓ HTTP POST http://service-layer:5001/internal/users   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST over Docker network
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  SERVICE LAYER (Port 5001)                                  │
│  Container: service-layer                                    │
│  ENV: DEPLOYMENT_LAYER=service                              │
│  ENV: USER_REPO_URLS=http://repository-layer:5002          │
├─────────────────────────────────────────────────────────────┤
│  UserServiceRoutes (app/services/routes/UserServiceRoutes) │
│     ↓ Blueprint: /internal/users                            │
│  UserServiceImpl (Business Logic)                           │
│     ↓                                                        │
│  UserRepositoryImpl (Direct call - same process)            │
│     ↓ SQL via SQLAlchemy                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  REPOSITORY LAYER (Port 5002) - Future                     │
│  Container: repository-layer                                 │
│  ENV: DEPLOYMENT_LAYER=repository                           │
│                                                              │
│  (Not yet implemented - Services call Repository directly)  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  MYSQL DATABASE (Port 3306)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Components

### 1. Service Layer HTTP API

**File**: `app/services/routes/UserServiceRoutes.py`

Exposes UserService business logic as HTTP/REST endpoints:

```python
# Blueprint for internal service API
user_service_bp = Blueprint('user_service', __name__, url_prefix='/internal/users')

# Endpoints:
# GET    /internal/users              - List users
# GET    /internal/users/<id>         - Get single user
# POST   /internal/users              - Create user
# PUT    /internal/users/<id>         - Update user
# DELETE /internal/users/<id>         - Delete user
# PUT    /internal/users/<id>/password - Change password
# POST   /internal/users/<id>/verify   - Verify user
# PUT    /internal/users/<id>/status   - Update user status
```

### 2. Service Adapter

**File**: `app/services/adapters/UserServiceAdapter.py`

Provides a unified interface that automatically switches between:

- **MonolithicUserService**: Direct in-process calls (for monolithic mode)
- **LayeredUserService**: HTTP/REST calls via ServiceClient (for layered mode)

```python
def get_user_service() -> UserServiceInterface:
    """
    Factory function based on DEPLOYMENT_LAYER environment variable

    Returns:
        - LayeredUserService: if DEPLOYMENT_LAYER=controller
        - MonolithicUserService: otherwise
    """
    deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic')

    if deployment_layer == 'controller':
        return LayeredUserService()  # Uses HTTP client
    else:
        return MonolithicUserService()  # Uses direct calls
```

### 3. ServiceClient (HTTP Client)

**File**: `app/services/clients/ServiceClient.py`

HTTP/REST client with:
- ✅ Connection pooling
- ✅ Automatic retry with exponential backoff
- ✅ Load balancing (round-robin)
- ✅ Circuit breaker pattern
- ✅ Health checking

```python
# Example: LayeredUserService making HTTP call
class LayeredUserService:
    def getUserById(self, user_id: int) -> User:
        # HTTP GET http://service-layer:5001/internal/users/{user_id}
        response = self.client.get(f'/internal/users/{user_id}')

        if not response.get('success'):
            raise NotFoundError(response.get('error'))

        user_data = response['data']
        return User(**user_data)
```

### 4. Updated UserController

**File**: `app/controllers/UserController.py`

Now uses the adapter instead of direct service calls:

```python
# OLD (Monolithic only):
from app.services.implementations.UserServiceImpl import UserServiceImpl

def get_user_service() -> UserServiceImpl:
    user_repo = UserRepositoryImpl(db.session)
    return UserServiceImpl(user_repo)

# NEW (Works in both modes):
from app.services.adapters import get_user_service

# Automatically uses:
# - MonolithicUserService (monolithic mode)
# - LayeredUserService (layered mode via HTTP)
```

### 5. Dynamic Blueprint Registration

**File**: `app/__init__.py`

Registers different blueprints based on `DEPLOYMENT_LAYER`:

```python
def register_blueprints(app: Flask) -> None:
    deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic')

    # Controller layer: External API endpoints
    if deployment_layer in ['monolithic', 'controller']:
        app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
        app.register_blueprint(user_bp, url_prefix='/api/v1/users')
        app.register_blueprint(public_user_bp)

    # Service layer: Internal API endpoints
    if deployment_layer in ['monolithic', 'service']:
        app.register_blueprint(user_service_bp)  # /internal/users
```

## How It Works

### Monolithic Mode

```
Client Request
    ↓ HTTP
UserController.create_user()
    ↓ Direct call (same process)
MonolithicUserService.createUser()
    ↓ Direct call (same process)
UserServiceImpl.createUser()
    ↓ Direct call (same process)
UserRepositoryImpl.create()
    ↓ SQL
MySQL Database
```

**Environment**:
```bash
DEPLOYMENT_LAYER=monolithic
```

### Layered Mode

```
Client Request
    ↓ HTTP
UserController.create_user()
    ↓ Direct call
LayeredUserService.createUser()
    ↓ HTTP POST http://service-layer:5001/internal/users
    ↓ (JSON: {"username": "john", "email": "john@example.com"})
────────────────────────────────────────────
Service Layer Container (Different process)
    ↓
user_service_bp.create_user()  # Route handler
    ↓ Direct call
UserServiceImpl.createUser()
    ↓ Direct call
UserRepositoryImpl.create()
    ↓ SQL
MySQL Database
```

**Environment (Controller)**:
```bash
DEPLOYMENT_LAYER=controller
USER_SERVICE_URLS=http://service-layer:5001
```

**Environment (Service)**:
```bash
DEPLOYMENT_LAYER=service
USER_REPO_URLS=http://repository-layer:5002
```

## Testing

### 1. Test Monolithic Mode (Current Default)

```bash
# Start monolithic mode
export DEPLOYMENT_LAYER=monolithic
python wsgi.py

# Test API
curl http://localhost:5000/api/v1/users
```

### 2. Test Layered Mode with Docker Compose

```bash
# Build and start layered deployment
cd deployment/layered
docker-compose up --build

# Controller layer: http://localhost:5003
# Service layer: http://localhost:5001

# Test external API (Controller → Service HTTP call)
curl http://localhost:5003/api/v1/users

# Test internal API directly (for debugging)
curl http://localhost:5001/internal/users
```

### 3. Verify HTTP Communication

Check logs to see HTTP requests:

```bash
# Controller layer logs (shows outgoing HTTP requests)
docker-compose logs -f controller-layer

# Service layer logs (shows incoming HTTP requests)
docker-compose logs -f service-layer
```

**Expected Controller Log**:
```
ServiceClient calling http://service-layer:5001/internal/users
```

**Expected Service Log**:
```
POST /internal/users HTTP/1.1" 201
```

## API Endpoints

### External API (Controller Layer)

Public-facing API endpoints:

```
GET    /api/v1/users              - List users (requires auth)
GET    /api/v1/users/<id>         - Get user (requires auth)
POST   /api/v1/users              - Create user (requires admin)
PUT    /api/v1/users/<id>         - Update user (requires auth)
DELETE /api/v1/users/<id>         - Delete user (requires admin)
```

### Internal API (Service Layer)

Internal HTTP endpoints (not exposed externally):

```
GET    /internal/users              - List users
GET    /internal/users/<id>         - Get user
POST   /internal/users              - Create user
PUT    /internal/users/<id>         - Update user
DELETE /internal/users/<id>         - Delete user
PUT    /internal/users/<id>/password - Change password
POST   /internal/users/<id>/verify   - Verify user
PUT    /internal/users/<id>/status   - Update status
```

## Request/Response Format

### Internal API Request Example

**HTTP Request**:
```http
POST http://service-layer:5001/internal/users HTTP/1.1
Host: service-layer:5001
Content-Type: application/json
User-Agent: ServiceClient/user-service

{
  "username": "john",
  "email": "john@example.com",
  "password": "Pass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**HTTP Response**:
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "success": true,
  "data": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-11-20T10:00:00Z"
  }
}
```

## Benefits

### Monolithic Mode
- ✅ Simple deployment
- ✅ Lower latency (no HTTP overhead)
- ✅ Easier debugging
- ✅ Lower resource usage
- ❌ Cannot scale layers independently

### Layered Mode
- ✅ Independent scaling per layer
- ✅ Better resource utilization
- ✅ Clearer separation of concerns
- ✅ Can deploy to different servers
- ❌ Higher latency (HTTP overhead)
- ❌ More complex debugging

## Configuration

### Environment Variables

**Controller Layer**:
```bash
DEPLOYMENT_LAYER=controller
SERVICE_NAME=arcana-cloud-controller
SERVICE_PORT=5000
USER_SERVICE_URLS=http://service-layer:5001
AUTH_SERVICE_URLS=http://service-layer:5001
```

**Service Layer**:
```bash
DEPLOYMENT_LAYER=service
SERVICE_NAME=arcana-cloud-service
SERVICE_PORT=5001
USER_REPO_URLS=http://repository-layer:5002
```

**Repository Layer**:
```bash
DEPLOYMENT_LAYER=repository
SERVICE_NAME=arcana-cloud-repository
SERVICE_PORT=5002
DATABASE_URL=mysql+pymysql://user:pass@mysql:3306/arcana_cloud
```

## Troubleshooting

### 1. HTTP Connection Refused

**Error**: `ConnectionError: Cannot connect to service user-service`

**Solution**:
- Verify service layer is running: `docker-compose ps service-layer`
- Check USER_SERVICE_URLS environment variable
- Verify Docker network: `docker network inspect arcana-network`

### 2. Wrong Deployment Mode

**Error**: Controller still using direct calls instead of HTTP

**Solution**:
```bash
# Check environment variable
docker-compose exec controller-layer env | grep DEPLOYMENT_LAYER

# Should output: DEPLOYMENT_LAYER=controller
```

### 3. Service Not Responding

**Error**: HTTP timeout after 30 seconds

**Solution**:
- Check service layer logs: `docker-compose logs service-layer`
- Verify service is healthy: `curl http://localhost:5001/health`
- Check service layer blueprint is registered

## Files Created/Modified

### New Files:
1. `app/services/routes/UserServiceRoutes.py` - Service layer HTTP API
2. `app/services/routes/__init__.py` - Service routes package
3. `app/services/adapters/UserServiceAdapter.py` - Mode-aware adapter
4. `app/services/adapters/__init__.py` - Adapters package

### Modified Files:
1. `app/controllers/UserController.py` - Uses adapter instead of direct service
2. `app/__init__.py` - Dynamic blueprint registration based on deployment mode

## Next Steps

1. **Test in monolithic mode** - Verify backward compatibility
2. **Test in layered mode** - Deploy with docker-compose and test HTTP communication
3. **Add similar adapters for AuthService** - Extend pattern to other services
4. **Implement Repository Layer HTTP API** - Currently services call repositories directly
5. **Add monitoring and tracing** - Track HTTP requests across layers

## See Also

- [ServiceClient Implementation](../app/services/clients/ServiceClient.py)
- [Docker Compose Configuration](../deployment/layered/docker-compose.yml)
- [Layered Deployment Guide](../deployment/layered/README.md)
