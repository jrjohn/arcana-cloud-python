# Layered Deployment Mode

Separate containers for Controller, Service, and Repository layers - balanced approach for production.

## Overview

The layered mode deploys each architectural layer in its own container, providing:
- Clear separation of concerns
- Independent scaling of each layer
- Better resource optimization
- Easier debugging and monitoring
- Production-ready architecture

## Architecture

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │     (Nginx)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Controller    │
                    │  Layer (5003)   │
                    │   API Gateway   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    Service      │
                    │  Layer (5001)   │
                    │ Business Logic  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Repository    │
                    │  Layer (5002)   │
                    │  Data Access    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     MySQL       │
                    │   + Redis       │
                    └─────────────────┘
```

## Layer Responsibilities

### Controller Layer (Port 5003)
- HTTP request handling
- Input validation
- Authentication/Authorization
- Request routing
- Response formatting

**Optimizations**:
- 4 workers, 4 threads
- Short timeout (30s)
- High max requests (1000)

### Service Layer (Port 5001)
- Business logic processing
- Data transformation
- Business rule enforcement
- Transaction management
- Inter-service communication

**Optimizations**:
- 4 workers, 2 threads
- Medium timeout (60s)
- Medium max requests (500)

### Repository Layer (Port 5002)
- Database operations
- Data persistence
- Query execution
- Connection pooling
- Cache management

**Optimizations**:
- 3 workers, 4 threads
- Long timeout (90s)
- Lower max requests (300)
- Large connection pool

## Prerequisites

- Docker & Docker Compose installed
- Ports 5001, 5002, 5003 available
- Ports 3306 and 6379 available for MySQL and Redis

## Quick Start

### 1. Build Images

```bash
cd deployment/layered
docker-compose build
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Verify Deployment

```bash
./verify-layered-mode.sh
```

## Configuration

### Environment Variables

Create a `.env` file in the deployment directory:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database Configuration
DB_USER=arcana
DB_PASSWORD=arcana_pass
DB_NAME=arcana_cloud
DB_ROOT_PASSWORD=root_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO

# Version
VERSION=latest
```

### Service Ports

- **Controller Layer**: `http://localhost:5003`
- **Service Layer**: `http://localhost:5001`
- **Repository Layer**: `http://localhost:5002`
- **MySQL**: `localhost:3306`
- **Redis**: `localhost:6379`

## Services

### Application Layers

1. **Controller Layer** (`controller-layer`)
   - API Gateway
   - Port: 5003 (host) → 5000 (container)
   - Health check: `/health`

2. **Service Layer** (`service-layer`)
   - Business Logic
   - Port: 5001 (host) → 5001 (container)
   - Health check: `/health`

3. **Repository Layer** (`repository-layer`)
   - Data Access
   - Port: 5002 (host) → 5002 (container)
   - Health check: `/ready`

### Supporting Services

4. **Celery Worker** (`celery-worker`)
   - Background task processing
   - Uses service layer image

5. **MySQL Database** (`mysql`)
   - Persistent data storage
   - Version: 8.0

6. **Redis Cache** (`redis`)
   - Session storage
   - Message broker
   - Cache layer

7. **Nginx Load Balancer** (`nginx`) - Optional
   - Load balancing
   - SSL termination
   - Static file serving

## Health Checks

### Check All Layers

```bash
# Controller layer
curl http://localhost:5003/health

# Service layer
curl http://localhost:5001/health

# Repository layer
curl http://localhost:5002/ready
```

### Automated Verification

```bash
./verify-layered-mode.sh
```

## Scaling

### Horizontal Scaling

Scale individual layers:

```bash
# Scale controller layer
docker-compose up -d --scale controller-layer=3

# Scale service layer
docker-compose up -d --scale service-layer=3

# Scale repository layer
docker-compose up -d --scale repository-layer=2
```

**Note**: To use replicas, remove port mappings and use nginx for load balancing.

### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Inter-Layer Communication

Layers communicate via internal Docker network:

- **Controller → Service**: `http://service-layer:5001`
- **Service → Repository**: `http://repository-layer:5002`

Environment variables configure URLs:
```yaml
# Controller layer
USER_SERVICE_URLS: http://service-layer:5001
AUTH_SERVICE_URLS: http://service-layer:5001

# Service layer
USER_REPO_URLS: http://repository-layer:5002
```

## Container Management

### View Logs

```bash
# All services
docker-compose logs -f

# Specific layer
docker-compose logs -f controller-layer
docker-compose logs -f service-layer
docker-compose logs -f repository-layer
```

### Restart Layers

```bash
# Restart specific layer
docker-compose restart controller-layer

# Restart all
docker-compose restart
```

### Update Single Layer

```bash
# Rebuild and restart
docker-compose up -d --build controller-layer
```

## Monitoring

### Container Status

```bash
docker-compose ps
```

### Resource Usage

```bash
docker stats
```

### Layer-Specific Metrics

Each layer exposes metrics at:
- Controller: `http://localhost:5003/metrics`
- Service: `http://localhost:5001/metrics`
- Repository: `http://localhost:5002/metrics`

## Load Balancing with Nginx

### Enable Nginx

1. Create nginx configuration:
```bash
mkdir -p ../../nginx
# Create nginx-layered.conf
```

2. Uncomment nginx service in `docker-compose.yml`

3. Remove port mappings from layers

4. Restart:
```bash
docker-compose up -d
```

Access via Nginx:
- HTTP: `http://localhost:80`
- HTTPS: `https://localhost:443`

## Troubleshooting

### Layer Communication Issues

Check network connectivity:
```bash
docker-compose exec controller-layer curl http://service-layer:5001/health
docker-compose exec service-layer curl http://repository-layer:5002/ready
```

### Layer Won't Start

Check specific layer logs:
```bash
docker-compose logs controller-layer
docker-compose logs service-layer
docker-compose logs repository-layer
```

### Database Connection Issues

Verify repository layer can connect:
```bash
docker-compose exec repository-layer curl http://localhost:5002/ready
```

### Port Conflicts

macOS AirPlay uses port 5000. Controller is mapped to 5003.

To change ports, edit `docker-compose.yml`:
```yaml
ports:
  - "5010:5000"  # Custom port
```

## Performance Tuning

### Controller Layer
```yaml
# Optimized for request handling
--workers 4
--threads 4
--timeout 30
--max-requests 1000
```

### Service Layer
```yaml
# Balanced for business logic
--workers 4
--threads 2
--timeout 60
--max-requests 500
```

### Repository Layer
```yaml
# Optimized for database operations
--workers 3
--threads 4
--timeout 90
--max-requests 300
```

### Database Connection Pool

Configure in repository layer:
```yaml
SQLALCHEMY_POOL_SIZE: 20
SQLALCHEMY_MAX_OVERFLOW: 40
SQLALCHEMY_POOL_TIMEOUT: 30
SQLALCHEMY_POOL_RECYCLE: 3600
```

## Development

### Local Development

Run layers separately:

```bash
# Terminal 1 - Repository Layer
DEPLOYMENT_LAYER=repository python wsgi.py

# Terminal 2 - Service Layer
DEPLOYMENT_LAYER=service python wsgi.py

# Terminal 3 - Controller Layer
DEPLOYMENT_LAYER=controller python wsgi.py
```

### Debug Mode

Enable debug logging for specific layer:
```yaml
environment:
  LOG_LEVEL: DEBUG
```

## Migration

### From Monolithic to Layered

1. Backup data:
```bash
cd ../monolithic
docker-compose exec mysql mysqldump -u root -p arcana_cloud > backup.sql
```

2. Stop monolithic:
```bash
docker-compose down
```

3. Start layered:
```bash
cd ../layered
docker-compose up -d
```

4. Restore data:
```bash
docker-compose exec -T mysql mysql -u root -p arcana_cloud < backup.sql
```

### To Kubernetes

See [Kubernetes Deployment](../kubernetes/README.md)

## Best Practices

1. **Use Environment Variables**: Never hardcode secrets
2. **Enable Health Checks**: Monitor all layers
3. **Set Resource Limits**: Prevent resource exhaustion
4. **Use Logging**: Centralized logging for all layers
5. **Regular Backups**: Automated database backups
6. **SSL/TLS**: Enable HTTPS in production
7. **Network Policies**: Restrict inter-layer communication
8. **Version Control**: Tag images with versions

## See Also

- [Monolithic Deployment](../monolithic/README.md)
- [Kubernetes Deployment](../kubernetes/README.md)
- [Main Documentation](../../README.md)
