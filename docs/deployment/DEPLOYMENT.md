# Arcana Cloud - Deployment Guide

Comprehensive guide for deploying the Arcana Cloud application in different modes and environments.

## Table of Contents

- [Overview](#overview)
- [Deployment Modes](#deployment-modes)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
  - [Docker Compose](#docker-compose-deployment)
  - [Kubernetes](#kubernetes-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

The Arcana Cloud deployment system supports three distinct deployment architectures:

1. **Monolithic**: All components in a single container
2. **Layered**: Separate containers for Controller, Service, and Repository layers
3. **Microservices**: Fine-grained services per domain (Auth, User, etc.)

## Deployment Modes

### Monolithic Mode

```
┌─────────────────────────────┐
│   Monolithic Container      │
│  ┌────────────────────────┐ │
│  │    Controllers         │ │
│  ├────────────────────────┤ │
│  │    Services            │ │
│  ├────────────────────────┤ │
│  │    Repositories        │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
```

**Use Cases:**
- Small to medium applications
- Development and testing
- Simple deployment requirements
- Limited scaling needs

**Pros:**
- Simple deployment
- Lower resource overhead
- Easy debugging

**Cons:**
- Harder to scale individual components
- All-or-nothing deployment updates

### Layered Mode

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Controller  │────▶│  Service    │────▶│ Repository  │
│   Layer     │     │   Layer     │     │   Layer     │
│  (API GW)   │     │  (Business) │     │   (Data)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Use Cases:**
- Medium to large applications
- Need to scale layers independently
- Clear separation of concerns
- Better resource optimization

**Pros:**
- Independent scaling per layer
- Better resource utilization
- Clearer architecture boundaries
- Can update layers independently

**Cons:**
- More complex deployment
- Network latency between layers
- Requires service discovery

### Microservices Mode

```
┌─────────────┐     ┌─────────────┐
│    Auth     │     │    User     │
│ Microservice│     │ Microservice│
└─────────────┘     └─────────────┘
        │                   │
        └──────┬───────────┘
               │
        ┌──────▼──────┐
        │  API Gateway│
        └─────────────┘
```

**Use Cases:**
- Large, complex applications
- High scalability requirements
- Independent team ownership
- Polyglot architecture needs

**Pros:**
- Maximum flexibility
- Independent deployment per service
- Technology diversity
- Fault isolation

**Cons:**
- Most complex deployment
- Requires robust service mesh
- Higher operational overhead
- More moving parts

## Prerequisites

### For Docker Compose

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

### For Kubernetes

- Kubernetes 1.24+
- kubectl CLI configured
- 8GB+ RAM across cluster
- 20GB+ disk space
- Helm 3.0+ (optional)

### For Build Scripts

- Python 3.14+
- PyYAML (`pip install pyyaml`)
- Git (for version tracking)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd arcana-cloud-python

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
vim .env
```

### 2. Build Images

```bash
# Build all images
./scripts/build.sh

# Build specific mode
./scripts/build.sh --mode monolithic

# Build and push to registry
./scripts/build.sh --mode layered --push --version 1.0.0
```

### 3. Deploy

#### Docker Compose (Monolithic)

```bash
docker-compose up -d
```

#### Docker Compose (Layered)

```bash
docker-compose -f docker-compose.layered.yml up -d
```

#### Kubernetes

```bash
# Using Python script
python scripts/deploy.py deploy --target kubernetes --mode layered

# Or manually
kubectl apply -f k8s/
```

## Deployment Methods

### Docker Compose Deployment

#### Monolithic Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### Layered Deployment

```bash
# Start layered architecture
docker-compose -f docker-compose.layered.yml up -d

# Scale specific layer
docker-compose -f docker-compose.layered.yml up -d --scale controller-layer=5

# View specific service logs
docker-compose -f docker-compose.layered.yml logs -f controller-layer
```

#### Microservices Deployment

```bash
# Start microservices
docker-compose -f docker-compose.microservices.yml up -d

# Scale specific microservice
docker-compose -f docker-compose.microservices.yml up -d --scale auth-service=3
```

### Kubernetes Deployment

#### Using Automated Script

```bash
# Deploy layered mode
python scripts/deploy.py deploy --target kubernetes --mode layered --environment production

# Check status
python scripts/deploy.py status --target kubernetes

# Cleanup
python scripts/deploy.py cleanup --target kubernetes
```

#### Manual Deployment

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create RBAC
kubectl apply -f k8s/rbac.yaml

# Create ConfigMaps and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Create PVCs
kubectl apply -f k8s/pvc.yaml

# Deploy application layers
kubectl apply -f k8s/controller-deployment.yaml
kubectl apply -f k8s/service-deployment.yaml
kubectl apply -f k8s/repository-deployment.yaml

# Create services
kubectl apply -f k8s/services.yaml

# Enable auto-scaling
kubectl apply -f k8s/hpa.yaml

# Create ingress
kubectl apply -f k8s/ingress.yaml
```

#### Verify Deployment

```bash
# Check all resources
kubectl get all -n arcana-cloud

# Check pod status
kubectl get pods -n arcana-cloud

# View logs
kubectl logs -f deployment/controller-layer -n arcana-cloud

# Check HPA status
kubectl get hpa -n arcana-cloud

# Check ingress
kubectl get ingress -n arcana-cloud
```

## Configuration

### Deployment Configuration File

The main configuration file is `deployment-config.yaml`. Key sections:

```yaml
global:
  project_name: arcana-cloud
  version: "1.0.0"
  registry: docker.io/arcanacloud

deployment_modes:
  monolithic:
    containers:
      app:
        replicas: 3
        resources:
          limits:
            cpu: "1000m"
            memory: "1Gi"
```

### Environment-Specific Overrides

```yaml
environments:
  production:
    global:
      environment:
        LOG_LEVEL: WARNING
    deployment_modes:
      monolithic:
        containers:
          app:
            replicas: 5
```

### Kubernetes Secrets

**Important:** Never commit secrets to version control!

```bash
# Create secrets from file
kubectl create secret generic arcana-cloud-secrets \
  --from-literal=SECRET_KEY=your-secret-key \
  --from-literal=JWT_SECRET_KEY=your-jwt-key \
  --from-literal=DB_PASSWORD=your-db-password \
  -n arcana-cloud

# Create TLS certificate
kubectl create secret tls arcana-cloud-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n arcana-cloud
```

## Monitoring

### Health Checks

All deployments include health check endpoints:

- `/health` - Liveness probe (basic health)
- `/ready` - Readiness probe (includes dependency checks)
- `/metrics` - Prometheus metrics (port 9090)

```bash
# Check health (Docker)
curl http://localhost:5000/health

# Check health (Kubernetes)
kubectl port-forward -n arcana-cloud svc/controller-layer 5000:5000
curl http://localhost:5000/health
```

### Prometheus Metrics

```bash
# Port forward to Prometheus (if using microservices mode)
kubectl port-forward -n arcana-cloud svc/prometheus 9090:9090

# Access Prometheus UI
open http://localhost:9090
```

### Grafana Dashboards

```bash
# Port forward to Grafana (if using microservices mode)
kubectl port-forward -n arcana-cloud svc/grafana 3000:3000

# Access Grafana UI (default: admin/admin)
open http://localhost:3000
```

### Logging

```bash
# Docker Compose logs
docker-compose logs -f --tail=100

# Kubernetes logs
kubectl logs -f -l app=arcana-cloud -n arcana-cloud --all-containers=true

# Specific pod logs
kubectl logs -f deployment/controller-layer -n arcana-cloud
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n arcana-cloud

# Check events
kubectl get events -n arcana-cloud --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n arcana-cloud
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=mysql:8.0 --restart=Never -n arcana-cloud -- \
  mysql -h mysql-service -u arcana -p

# Check database service
kubectl get svc mysql-service -n arcana-cloud
kubectl get endpoints mysql-service -n arcana-cloud
```

#### 3. Service Discovery Issues

```bash
# Check service endpoints
kubectl get endpoints -n arcana-cloud

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -n arcana-cloud -- \
  nc -zv service-layer 5001
```

#### 4. Image Pull Errors

```bash
# Check image pull secrets
kubectl get secrets -n arcana-cloud

# Create Docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n arcana-cloud
```

### Debug Mode

Enable debug mode by setting environment variables:

```bash
# Docker Compose
FLASK_ENV=development LOG_LEVEL=DEBUG docker-compose up

# Kubernetes
kubectl set env deployment/controller-layer LOG_LEVEL=DEBUG -n arcana-cloud
```

## Advanced Topics

### Custom Scaling Policies

Modify HPA configuration in `k8s/hpa.yaml`:

```yaml
spec:
  minReplicas: 5
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

### Blue-Green Deployment

```bash
# Create new deployment with different version
kubectl apply -f k8s/controller-deployment-v2.yaml

# Switch traffic
kubectl patch service controller-layer -n arcana-cloud -p \
  '{"spec":{"selector":{"version":"v2"}}}'

# Rollback if needed
kubectl patch service controller-layer -n arcana-cloud -p \
  '{"spec":{"selector":{"version":"v1"}}}'
```

### Canary Deployment

```bash
# Deploy canary version (10% traffic)
kubectl apply -f k8s/controller-deployment-canary.yaml

# Monitor metrics
# If successful, increase canary replicas and decrease stable replicas
kubectl scale deployment controller-layer --replicas=5 -n arcana-cloud
kubectl scale deployment controller-layer-canary --replicas=2 -n arcana-cloud
```

### Service Mesh Integration

For production environments, consider using a service mesh like Istio:

```bash
# Install Istio
istioctl install --set profile=demo -y

# Enable sidecar injection
kubectl label namespace arcana-cloud istio-injection=enabled

# Apply virtual services and destination rules
kubectl apply -f k8s/istio/
```

### Backup and Restore

#### Database Backup

```bash
# Create backup
kubectl exec -n arcana-cloud deployment/mysql -- \
  mysqldump -u root -p${MYSQL_ROOT_PASSWORD} arcana_cloud > backup.sql

# Restore backup
kubectl exec -i -n arcana-cloud deployment/mysql -- \
  mysql -u root -p${MYSQL_ROOT_PASSWORD} arcana_cloud < backup.sql
```

#### Persistent Volume Backup

```bash
# Create snapshot (cloud provider specific)
# AWS EBS
aws ec2 create-snapshot --volume-id <volume-id> --description "Backup"

# GCP Persistent Disk
gcloud compute disks snapshot <disk-name> --snapshot-names=<snapshot-name>
```

## Production Checklist

Before deploying to production:

- [ ] Update all secrets in `k8s/secrets.yaml`
- [ ] Configure TLS certificates
- [ ] Set up external database (not in-cluster)
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Review resource limits and requests
- [ ] Test disaster recovery procedures
- [ ] Configure network policies
- [ ] Set up CI/CD pipeline
- [ ] Review security policies
- [ ] Configure auto-scaling thresholds
- [ ] Set up health check alerts
- [ ] Document runbooks
- [ ] Test rollback procedures

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review application logs
- Open an issue on GitHub
- Contact the DevOps team

## License

Copyright (c) 2025 Arcana Cloud Team
