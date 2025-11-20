# Monolithic Deployment Mode

Single container deployment with all application layers combined.

## Overview

The monolithic mode deploys all application components (Controllers, Services, Repositories) in a single container, making it ideal for:
- Development environments
- Small-scale deployments
- Quick testing and prototyping
- Simple deployment scenarios

## Architecture

```
┌─────────────────────────────────────┐
│     Monolithic Application          │
│  ┌───────────────────────────────┐  │
│  │      Controllers (API)        │  │
│  ├───────────────────────────────┤  │
│  │    Services (Business Logic)  │  │
│  ├───────────────────────────────┤  │
│  │  Repositories (Data Access)   │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │              │
    ┌────▼────┐    ┌───▼────┐
    │  MySQL  │    │  Redis │
    └─────────┘    └────────┘
```

## Prerequisites

- Docker & Docker Compose installed
- Port 5001 available (mapped from container port 5000)
- Ports 3306 and 6379 available for MySQL and Redis (optional, can be commented out)

## Quick Start

### 1. Build Images

```bash
cd deployment/monolithic
./build-images.sh
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Verify Deployment

```bash
./verify-monolithic-mode.sh
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
```

### Service Ports

- **Application**: `http://localhost:5001` (mapped from container port 5000)
- **MySQL**: `localhost:3306` (if exposed)
- **Redis**: `localhost:6379` (if exposed)

## Services

The monolithic deployment includes:

1. **Application Container** (`arcana-cloud-app`)
   - All application layers in one container
   - Port 5001 (host) → 5000 (container)
   - Health check: `/health` endpoint

2. **Celery Worker** (`arcana-cloud-celery-worker`)
   - Background task processing
   - Handles async operations

3. **Celery Beat** (`arcana-cloud-celery-beat`)
   - Scheduled task execution
   - Cron-like scheduling

4. **MySQL Database** (`arcana-cloud-mysql`)
   - Persistent data storage
   - Version: 8.0

5. **Redis Cache** (`arcana-cloud-redis`)
   - Session storage
   - Celery message broker
   - Caching layer

## Health Checks

Check application health:

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

## Container Management

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f celery-worker
```

### Restart Services

```bash
docker-compose restart
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

## Scaling

Monolithic mode runs a single instance. For horizontal scaling, use the [layered deployment mode](../layered/README.md) instead.

## Resource Limits

Default resource limits (can be adjusted in docker-compose.yml):

- **CPU**: 1.0 cores (limit), 0.5 cores (reservation)
- **Memory**: 1GB (limit), 512MB (reservation)

## Troubleshooting

### Port 5000 Conflict (macOS)

Port 5000 is used by macOS AirPlay Receiver. The application is mapped to port 5001 to avoid conflicts.

### Container Won't Start

Check logs:
```bash
docker-compose logs app
```

### Database Connection Issues

Ensure MySQL is healthy:
```bash
docker-compose ps mysql
```

### Redis Connection Issues

Verify Redis is running:
```bash
docker-compose ps redis
docker-compose exec redis redis-cli ping
```

## Migration to Layered Mode

To migrate from monolithic to layered deployment:

1. Export database:
   ```bash
   docker-compose exec mysql mysqldump -u root -p arcana_cloud > backup.sql
   ```

2. Stop monolithic deployment:
   ```bash
   docker-compose down
   ```

3. Switch to layered mode:
   ```bash
   cd ../layered
   docker-compose up -d
   ```

4. Import database:
   ```bash
   docker-compose exec -T mysql mysql -u root -p arcana_cloud < backup.sql
   ```

## Performance Tuning

### Gunicorn Workers

Adjust in `docker/Dockerfile.monolithic`:
- Workers: `--workers 4` (default)
- Threads: `--threads 2` (default)
- Worker class: `gthread` (threading support)

### Database Connection Pool

Set in environment variables:
```bash
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
```

## Development

### Local Development

For local development without Docker:

```bash
# Set environment
export FLASK_ENV=development
export DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/arcana_cloud

# Run application
python wsgi.py
```

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG docker-compose up
```

## See Also

- [Layered Deployment](../layered/README.md)
- [Kubernetes Deployment](../kubernetes/README.md)
- [Main Documentation](../../README.md)
