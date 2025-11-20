# Configuration-Driven Deployment System

## Overview

This deployment system provides a flexible, configuration-driven approach to deploying the Arcana Cloud Flask application across different architectures and environments.

## System Architecture

```
deployment-config.yaml (Configuration Source)
        │
        ├──▶ Docker Compose Deployments
        │    ├── Monolithic (docker-compose.yml)
        │    ├── Layered (docker-compose.layered.yml)
        │    └── Microservices (docker-compose.microservices.yml)
        │
        └──▶ Kubernetes Deployments
             ├── Namespace & RBAC (k8s/namespace.yaml, k8s/rbac.yaml)
             ├── Configuration (k8s/configmap.yaml, k8s/secrets.yaml)
             ├── Storage (k8s/pvc.yaml)
             ├── Deployments (k8s/*-deployment.yaml)
             ├── Services (k8s/services.yaml)
             ├── Auto-scaling (k8s/hpa.yaml)
             └── Ingress (k8s/ingress.yaml)
```

## Directory Structure

```
arcana-cloud-python/
├── deployment-config.yaml          # Main configuration file
├── .env.example                    # Environment variables template
├── Makefile                        # Convenience commands
│
├── docker/                         # Docker configurations
│   ├── Dockerfile.base            # Base image
│   ├── Dockerfile.monolithic      # Monolithic deployment
│   ├── Dockerfile.controller      # Controller layer
│   ├── Dockerfile.service         # Service layer
│   ├── Dockerfile.repository      # Repository layer
│   ├── healthcheck.sh             # Health check script
│   ├── entrypoint-controller.sh   # Controller entrypoint
│   ├── entrypoint-service.sh      # Service entrypoint
│   └── entrypoint-repository.sh   # Repository entrypoint
│
├── docker-compose.yml              # Monolithic mode
├── docker-compose.layered.yml      # Layered mode
├── docker-compose.microservices.yml # Microservices mode
│
├── k8s/                            # Kubernetes manifests
│   ├── namespace.yaml             # Namespace definition
│   ├── rbac.yaml                  # RBAC configuration
│   ├── configmap.yaml             # ConfigMaps
│   ├── secrets.yaml               # Secrets (template)
│   ├── pvc.yaml                   # Persistent volume claims
│   ├── controller-deployment.yaml # Controller deployment
│   ├── service-deployment.yaml    # Service deployment
│   ├── repository-deployment.yaml # Repository deployment
│   ├── services.yaml              # Service definitions
│   ├── hpa.yaml                   # Horizontal Pod Autoscaler
│   └── ingress.yaml               # Ingress configuration
│
├── scripts/                        # Automation scripts
│   ├── deploy.py                  # Main deployment script
│   └── build.sh                   # Docker build script
│
└── DEPLOYMENT.md                   # Deployment guide
```

## Key Features

### 1. Configuration-Driven

All deployment parameters are defined in `deployment-config.yaml`:

- **Deployment Modes**: Monolithic, Layered, Microservices
- **Component Mapping**: Define which components go into which containers
- **Resource Allocation**: CPU/Memory limits per container
- **Scaling Policies**: Min/max replicas, auto-scaling thresholds
- **Environment Overrides**: Development, Staging, Production settings

### 2. Multi-Mode Deployment

#### Monolithic Mode
- **Single container** with all components
- **Best for**: Development, small deployments
- **Scaling**: Vertical and horizontal scaling of entire app
- **Complexity**: Low

#### Layered Mode
- **Three containers**: Controller, Service, Repository
- **Best for**: Medium to large applications
- **Scaling**: Independent scaling per layer
- **Complexity**: Medium

#### Microservices Mode
- **Multiple containers**: One per domain (Auth, User, etc.)
- **Best for**: Large, complex applications
- **Scaling**: Fine-grained, per-service scaling
- **Complexity**: High

### 3. Health Checks

Each layer includes comprehensive health checks:

```bash
# Liveness Probe
GET /health
Returns: 200 if service is alive

# Readiness Probe
GET /ready
Returns: 200 if service is ready (includes dependency checks)

# Metrics
GET /metrics (port 9090)
Returns: Prometheus-format metrics
```

### 4. Service Discovery

Built-in service discovery for inter-layer communication:

```yaml
# Controller → Service
USER_SERVICE_URLS: http://service-layer:5001

# Service → Repository
USER_REPO_URLS: http://repository-layer:5002
```

### 5. Auto-Scaling

Horizontal Pod Autoscaler (HPA) configuration:

```yaml
minReplicas: 2
maxReplicas: 10
metrics:
  - CPU utilization: 70%
  - Memory utilization: 80%
```

### 6. Load Balancing

Multiple load balancing strategies:
- **Round Robin** (default)
- **Least Connections**
- **IP Hash** (session affinity)

## Quick Start Guide

### 1. Build Docker Images

```bash
# Build all images
make build-all

# Or build specific mode
make build-monolithic
make build-layered
make build-microservices

# Build and push to registry
make build-push VERSION=1.0.0
```

### 2. Deploy with Docker Compose

```bash
# Monolithic
make compose-up

# Layered
make compose-up-layered

# Microservices
make compose-up-microservices
```

### 3. Deploy to Kubernetes

```bash
# Deploy layered mode
make k8s-deploy MODE=layered ENVIRONMENT=production

# Check status
make k8s-status

# View logs
make k8s-logs
```

## Configuration Examples

### Customizing Resource Limits

Edit `deployment-config.yaml`:

```yaml
deployment_modes:
  layered:
    containers:
      controller:
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
```

### Environment-Specific Settings

```yaml
environments:
  production:
    deployment_modes:
      monolithic:
        containers:
          app:
            replicas: 5
            autoscaling:
              max_replicas: 20
```

### Custom Health Check Configuration

```yaml
health_checks:
  liveness:
    path: /health
    port: 5000
    initial_delay: 30
    period: 10
    timeout: 5
    failure_threshold: 3
```

## Deployment Workflows

### Development Workflow

```bash
# 1. Make code changes
vim app/controllers/UserController.py

# 2. Run tests
make test

# 3. Build and deploy locally
make build-monolithic
make compose-up

# 4. Check logs
make logs-app

# 5. Test endpoints
curl http://localhost:5000/api/v1/users
```

### Staging Deployment

```bash
# 1. Build images with version tag
make build-all VERSION=1.2.3-rc1

# 2. Push to registry
./scripts/build.sh --version 1.2.3-rc1 --push

# 3. Deploy to staging Kubernetes
python scripts/deploy.py deploy \
  --target kubernetes \
  --mode layered \
  --environment staging

# 4. Verify deployment
make k8s-status
make k8s-logs
```

### Production Deployment

```bash
# 1. Tag release version
git tag v1.2.3

# 2. Build production images
make build-all VERSION=1.2.3
./scripts/build.sh --version 1.2.3 --push

# 3. Deploy with blue-green strategy
# (See DEPLOYMENT.md for blue-green deployment)

# 4. Monitor deployment
make k8s-status
make k8s-hpa

# 5. Check health
make health
```

## Monitoring and Observability

### Metrics Collection

Prometheus scrapes metrics from:
- Application pods (port 9090)
- System metrics (CPU, Memory, Network)
- Custom application metrics

### Logging

Structured JSON logging to:
- Container stdout/stderr
- Persistent volumes (optional)
- External aggregators (Fluentd, Logstash)

### Tracing

Distributed tracing support (optional):
- Jaeger
- Zipkin
- Datadog APM

## Security Features

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

### Network Policies

```yaml
security:
  network_policies:
    enabled: true
    default_deny: true
```

### RBAC

Role-Based Access Control with least privilege:
- Service accounts per deployment
- Namespace-scoped roles
- Minimal required permissions

## Troubleshooting

### Common Issues

**Issue**: Pods stuck in Pending state
```bash
kubectl describe pod <pod-name> -n arcana-cloud
# Check: Resource constraints, PVC availability, node capacity
```

**Issue**: Service not accessible
```bash
kubectl get svc -n arcana-cloud
kubectl get endpoints -n arcana-cloud
# Check: Service selectors, pod labels, network policies
```

**Issue**: Database connection failures
```bash
kubectl logs deployment/repository-layer -n arcana-cloud
# Check: DATABASE_URL, secrets, network connectivity
```

### Debug Mode

Enable debug logging:
```bash
kubectl set env deployment/controller-layer \
  LOG_LEVEL=DEBUG \
  -n arcana-cloud
```

### Access Pod Shell

```bash
# Docker Compose
make shell-app

# Kubernetes
make k8s-shell
```

## Performance Tuning

### Database Connection Pool

```yaml
SQLALCHEMY_POOL_SIZE: 20
SQLALCHEMY_MAX_OVERFLOW: 40
SQLALCHEMY_POOL_TIMEOUT: 30
```

### Gunicorn Workers

```dockerfile
CMD ["gunicorn", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "60"]
```

### Redis Connection Pool

```python
REDIS_CONNECTION_POOL_SIZE=50
REDIS_CONNECTION_POOL_TIMEOUT=20
```

## Backup and Disaster Recovery

### Database Backup

```bash
# Automated daily backups
kubectl create cronjob mysql-backup \
  --image=mysql:8.0 \
  --schedule="0 2 * * *" \
  -- mysqldump ...
```

### Persistent Volume Snapshots

```bash
# Create snapshot
kubectl create volumesnapshot pvc-snapshot \
  --volume-snapshot-class=csi-snapshot-class \
  --source=arcana-cloud-uploads-pvc
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and Push
        run: |
          ./scripts/build.sh --push --version ${{ github.sha }}
      - name: Deploy
        run: |
          python scripts/deploy.py deploy \
            --target kubernetes \
            --mode layered \
            --environment production
```

## Best Practices

1. **Version Control**: Always tag images with version numbers
2. **Secrets Management**: Use external secret managers in production
3. **Resource Limits**: Always set CPU/memory limits
4. **Health Checks**: Configure appropriate timeouts and thresholds
5. **Monitoring**: Enable Prometheus metrics and alerting
6. **Logging**: Use structured JSON logging
7. **Backups**: Implement automated backup strategies
8. **Testing**: Test deployments in staging before production
9. **Rollback Plan**: Document and test rollback procedures
10. **Documentation**: Keep deployment docs up-to-date

## Support and Contributions

For issues, questions, or contributions:
- Review the documentation
- Check existing issues
- Create detailed bug reports
- Submit pull requests with tests

## License

Copyright (c) 2025 Arcana Cloud Team
