# Monolithic Mode Deployment Guide

## Overview

Monolithic mode deploys all application layers (Controller, Service, Repository) in a single container. This is the simplest deployment model, ideal for:

- **Development environments**
- **Small deployments**
- **Testing and prototyping**
- **Single-server deployments**
- **Resource-constrained environments**

## Architecture

```
┌─────────────────────────────────────────┐
│     Monolithic Container (Port 5000)    │
│  ┌────────────────────────────────────┐ │
│  │      Controller Layer              │ │  ← HTTP Endpoints
│  ├────────────────────────────────────┤ │
│  │      Service Layer                 │ │  ← Business Logic
│  ├────────────────────────────────────┤ │
│  │      Repository Layer              │ │  ← Data Access
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
  ┌────▼─────┐        ┌─────▼────┐
  │  MySQL   │        │  Redis   │
  └──────────┘        └──────────┘
```

---

## Deployment Methods

### 1. Docker Compose (Recommended for Development)

The simplest way to deploy monolithic mode using Docker Compose.

#### Prerequisites
- Docker and Docker Compose installed
- Port 5000 available

#### Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

#### Configuration

The [docker-compose.yml](../docker-compose.yml) is pre-configured for monolithic mode:

```yaml
services:
  app:
    image: arcanacloud/arcana-cloud-monolithic:latest
    ports:
      - "5000:5000"
    environment:
      DEPLOYMENT_LAYER: monolithic  # Key configuration
      SERVICE_NAME: arcana-cloud-monolithic
      DATABASE_URL: mysql+pymysql://arcana:arcana_pass@mysql:3306/arcana_cloud
      REDIS_URL: redis://redis:6379/0
```

#### Verification

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test API endpoint
curl http://localhost:5000/api/v1/health

# Check container logs
docker-compose logs app

# Check container health
docker-compose ps app
```

**Expected Response:**
```json
{
  "status": "healthy",
  "mode": "monolithic",
  "timestamp": "2025-11-20T10:00:00Z"
}
```

---

### 2. Kubernetes

Deploy monolithic mode to Kubernetes cluster.

#### Note on K8s Manifests

The current `k8s/` directory contains manifests for **layered/microservices** mode (separate controller, service, repository deployments).

For monolithic mode in Kubernetes, you have two options:

**Option A: Use Single Deployment (Recommended)**

Create a single deployment that runs the monolithic container:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arcana-cloud-monolithic
  namespace: arcana-cloud
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arcana-cloud
      mode: monolithic
  template:
    metadata:
      labels:
        app: arcana-cloud
        mode: monolithic
    spec:
      containers:
      - name: app
        image: arcanacloud/arcana-cloud-monolithic:latest
        ports:
        - containerPort: 5000
        env:
        - name: DEPLOYMENT_LAYER
          value: "monolithic"
        - name: DATABASE_URL
          value: "mysql+pymysql://arcana:pass@mysql:3306/arcana_cloud"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
```

**Option B: Modify Existing Manifests**

Use the existing `k8s/` manifests but set `DEPLOYMENT_MODE=monolithic` environment variable and deploy only the controller:

```bash
# Deploy namespace and dependencies
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/services.yaml

# Deploy only controller (acts as monolith)
kubectl set env deployment/controller-layer DEPLOYMENT_MODE=monolithic -n arcana-cloud
kubectl apply -f k8s/controller-deployment.yaml

# Don't deploy service and repository layers
```

#### Quick Start (Option A - Recommended)

```bash
# 1. Create namespace
kubectl create namespace arcana-cloud

# 2. Create ConfigMap with monolithic configuration
kubectl create configmap arcana-cloud-config \
  --from-literal=DEPLOYMENT_MODE=monolithic \
  --from-literal=SERVICE_PORT=5000 \
  -n arcana-cloud

# 3. Deploy MySQL and Redis
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/services.yaml

# 4. Create monolithic deployment (see example above)
kubectl apply -f k8s/monolithic-deployment.yaml

# 5. Verify deployment
kubectl get pods -n arcana-cloud -l mode=monolithic
kubectl logs -n arcana-cloud -l mode=monolithic

# 6. Test the service
kubectl port-forward -n arcana-cloud svc/arcana-cloud-monolithic 5000:5000
curl http://localhost:5000/health
```

#### Creating k8s/monolithic/ Directory

For a cleaner setup, you can create a dedicated `k8s/monolithic/` directory:

```bash
mkdir -p k8s/monolithic
```

Create minimal manifests:
1. `k8s/monolithic/deployment.yaml` - Monolithic app deployment
2. `k8s/monolithic/service.yaml` - Service for the app
3. `k8s/monolithic/ingress.yaml` - Ingress for external access

Then deploy with:
```bash
kubectl apply -f k8s/monolithic/
```

---

### 3. Direct Python Execution

Run the application directly using Python for local development.

#### Prerequisites
- Python 3.14+ installed
- Virtual environment set up
- Dependencies installed

#### Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export DEPLOYMENT_LAYER=monolithic
export FLASK_ENV=development
export DATABASE_URL=mysql+pymysql://arcana:pass@localhost:3306/arcana_cloud
export REDIS_URL=redis://localhost:6379/0

# 4. Run the application
python wsgi.py
```

#### Alternative: Using Environment File

```bash
# 1. Create .env file
cat > .env << EOF
DEPLOYMENT_LAYER=monolithic
FLASK_ENV=development
DATABASE_URL=mysql+pymysql://arcana:pass@localhost:3306/arcana_cloud
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret
EOF

# 2. Load environment and run
source .env
python wsgi.py
```

#### Verification

```bash
# In another terminal, test the endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/v1/health
```

---

## Configuration

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `DEPLOYMENT_LAYER` | `monolithic` | Enables monolithic mode |
| `DEPLOYMENT_MODE` | `monolithic` | Alternative variable name |
| `SERVICE_NAME` | `arcana-cloud-monolithic` | Service identifier |
| `SERVICE_PORT` | `5000` | Application port |
| `DATABASE_URL` | MySQL connection string | Database connection |
| `REDIS_URL` | Redis connection string | Cache connection |
| `FLASK_ENV` | `development` / `production` | Flask environment |

### wsgi.py Configuration

The [wsgi.py](../wsgi.py) file should check for monolithic mode:

```python
import os
from app import create_app

# Check deployment mode
deployment_layer = os.getenv('DEPLOYMENT_LAYER', 'monolithic')
deployment_mode = os.getenv('DEPLOYMENT_MODE', deployment_layer)

# Create appropriate app
if deployment_mode == 'monolithic':
    # Load all layers
    app = create_app(mode='monolithic')
else:
    # Load specific layer
    app = create_app(mode=deployment_layer)

if __name__ == '__main__':
    port = int(os.getenv('SERVICE_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=(os.getenv('FLASK_ENV') == 'development'))
```

---

## Testing

### Automated Verification

Run the verification script to test all deployment methods:

```bash
./scripts/verify-monolithic-mode.sh
```

This script tests:
1. Docker Compose deployment
2. Kubernetes configuration
3. Direct Python execution
4. Configuration files
5. Documentation

### Manual Testing

#### Test Health Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Readiness check
curl http://localhost:5000/ready

# API health
curl http://localhost:5000/api/v1/health
```

#### Test Application Functionality

```bash
# Test user endpoints (example)
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test123"}'

# Test login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

#### Check Logs

**Docker Compose:**
```bash
docker-compose logs -f app
```

**Kubernetes:**
```bash
kubectl logs -n arcana-cloud -l mode=monolithic -f
```

**Direct:**
Check console output where `python wsgi.py` is running

---

## Advantages

### Development Benefits
- ✅ **Simple Setup** - Single container, minimal configuration
- ✅ **Fast Startup** - No inter-service communication overhead
- ✅ **Easy Debugging** - All code in one process
- ✅ **Local Development** - Can run directly with Python
- ✅ **Lower Resource Usage** - Single process, lower memory footprint

### Small Deployment Benefits
- ✅ **Cost Effective** - Fewer containers/pods to manage
- ✅ **Simple Monitoring** - One service to monitor
- ✅ **Easier Updates** - Deploy once, update all layers
- ✅ **No Network Latency** - Internal function calls instead of HTTP

---

## Disadvantages

### Scaling Limitations
- ❌ **All-or-Nothing Scaling** - Can't scale individual layers
- ❌ **Resource Inefficiency** - Can't allocate resources per layer
- ❌ **Single Point of Failure** - If container fails, entire app is down

### Development Limitations
- ❌ **Monolithic Codebase** - Harder to separate concerns
- ❌ **No Layer Independence** - Can't deploy layers separately
- ❌ **Limited Team Parallelization** - One team per deployment

---

## Comparison: Monolithic vs Layered vs Microservices

| Feature | Monolithic | Layered | Microservices |
|---------|-----------|---------|---------------|
| **Containers** | 1 | 3 | 5+ |
| **Scalability** | Limited | Good | Excellent |
| **Complexity** | Low | Medium | High |
| **Resource Usage** | Low | Medium | High |
| **Development Speed** | Fast | Medium | Slow |
| **Debugging** | Easy | Medium | Hard |
| **Best For** | Dev/Small | Production | Enterprise |

---

## Troubleshooting

### Issue 1: Container Won't Start

**Check logs:**
```bash
docker-compose logs app
```

**Common causes:**
- Database not ready → Check MySQL container
- Redis not available → Check Redis container
- Port 5000 already in use → Check with `lsof -i :5000`

### Issue 2: Health Endpoint Returns 503

**Check:**
```bash
# Verify database connection
docker-compose exec app python -c "from app import db; db.engine.connect()"

# Verify Redis connection
docker-compose exec app python -c "from app import redis_client; redis_client.ping()"
```

### Issue 3: Application Slow

**Monolithic mode limitations:**
- All layers share resources
- No horizontal scaling of individual layers
- Consider migrating to layered mode for better performance

**Workaround:**
```bash
# Increase container resources in docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Issue 4: Can't Connect to Database

**Check network:**
```bash
docker-compose exec app ping mysql
docker-compose exec app ping redis
```

**Verify environment variables:**
```bash
docker-compose exec app env | grep DATABASE_URL
docker-compose exec app env | grep REDIS_URL
```

---

## Migration Path

### From Monolithic to Layered

When your application grows, migrate to layered mode:

```bash
# 1. Stop monolithic deployment
docker-compose down

# 2. Switch to layered mode
docker-compose -f docker-compose.layered.yml up -d

# 3. Verify all layers are running
docker-compose -f docker-compose.layered.yml ps
```

### From Monolithic to Microservices

For even more scalability:

```bash
# Switch to microservices mode
docker-compose -f docker-compose.microservices.yml up -d
```

---

## Additional Resources

- [README.md](../README.md) - Main project documentation
- [Docker Compose File](../docker-compose.yml) - Monolithic configuration
- [Deployment Guide](DEPLOYMENT.md) - Comprehensive deployment guide
- [Architecture Documentation](ARCHITECTURE.md) - System architecture details

---

**Last Updated:** 2025-11-20
