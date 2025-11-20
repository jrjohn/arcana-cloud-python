# Deployment Directory Structure

This directory contains all deployment configurations organized by deployment mode.

## 📁 Directory Layout

```
deployment/
├── README.md                      # Deployment modes overview & comparison
│
├── monolithic/                    # Monolithic Deployment (Development)
│   ├── README.md                  # Complete monolithic mode guide
│   ├── docker-compose.yml         # Single container configuration
│   ├── build-images.sh            # Image build automation
│   └── verify-monolithic-mode.sh  # Health check & verification
│
├── layered/                       # Layered Deployment (Production)
│   ├── README.md                  # Complete layered mode guide
│   ├── docker-compose.yml         # 3-layer configuration
│   └── verify-layered-mode.sh     # Health check & verification
│
└── kubernetes/                    # Kubernetes Deployment (Enterprise)
    ├── README.md                  # Complete K8s deployment guide
    ├── namespace.yaml             # K8s namespace
    ├── configmap.yaml             # Configuration data
    ├── secrets.yaml               # Secrets template
    ├── *-deployment.yaml          # Deployment manifests
    ├── services.yaml              # K8s services
    ├── ingress.yaml               # Ingress configuration
    └── hpa.yaml                   # Auto-scaling rules
```

## 🚀 Quick Start by Mode

### Monolithic Mode
```bash
cd deployment/monolithic
./build-images.sh
docker-compose up -d
./verify-monolithic-mode.sh
# Access: http://localhost:5001
```

### Layered Mode
```bash
cd deployment/layered
docker-compose build
docker-compose up -d
./verify-layered-mode.sh
# Access:
# - Controller: http://localhost:5003
# - Service: http://localhost:5001
# - Repository: http://localhost:5002
```

### Kubernetes Mode
```bash
cd deployment/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml  # Update with real values first!
kubectl apply -f .
# Access via kubectl port-forward or Ingress
```

## 📖 Documentation

Each mode has its own comprehensive README:

1. **[deployment/README.md](README.md)** - Overview and comparison of all modes
2. **[monolithic/README.md](monolithic/README.md)** - Monolithic deployment guide
3. **[layered/README.md](layered/README.md)** - Layered deployment guide
4. **[kubernetes/README.md](kubernetes/README.md)** - Kubernetes deployment guide

## 🔄 Migration Between Modes

### Monolithic → Layered
```bash
# 1. Backup data
cd monolithic
docker-compose exec mysql mysqldump -u root -p arcana_cloud > backup.sql

# 2. Stop monolithic
docker-compose down

# 3. Start layered
cd ../layered
docker-compose up -d

# 4. Restore data
docker-compose exec -T mysql mysql -u root -p arcana_cloud < ../backup.sql
```

### Layered → Kubernetes
```bash
# 1. Build and tag images
cd ../../
docker build -t myregistry.io/arcana-cloud-controller:1.0 -f docker/Dockerfile.controller .
docker push myregistry.io/arcana-cloud-controller:1.0

# 2. Deploy to Kubernetes
cd deployment/kubernetes
kubectl apply -f .
```

## 📊 Files by Mode

### Monolithic Mode Files
- **docker-compose.yml**: Single container + MySQL + Redis + Celery
- **build-images.sh**: Automated image building
- **verify-monolithic-mode.sh**: Health check script
- **README.md**: Detailed documentation (5,801 bytes)

### Layered Mode Files
- **docker-compose.yml**: 3 layer containers + infrastructure
- **verify-layered-mode.sh**: Multi-layer health check
- **README.md**: Detailed documentation (9,832 bytes)

### Kubernetes Mode Files
- **namespace.yaml**: Isolated namespace
- **secrets.yaml**: Secrets template (needs customization)
- **configmap.yaml**: Environment configuration
- **controller-deployment.yaml**: Controller pods
- **service-deployment.yaml**: Service pods
- **repository-deployment.yaml**: Repository pods
- **mysql-deployment.yaml**: Database StatefulSet
- **redis-deployment.yaml**: Cache Deployment
- **services.yaml**: K8s services (ClusterIP, LoadBalancer)
- **ingress.yaml**: Nginx ingress with TLS
- **hpa.yaml**: Horizontal Pod Autoscaler
- **pvc.yaml**: Persistent volume claims
- **rbac.yaml**: Role-based access control
- **README.md**: Detailed documentation

## 🎯 Choosing the Right Mode

| Criteria | Monolithic | Layered | Kubernetes |
|----------|-----------|---------|------------|
| **Users** | < 100 | 100-10K | > 10K |
| **Setup Time** | 2 min | 5 min | 15 min |
| **Complexity** | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Scaling** | Vertical | Per-Layer | Auto |
| **HA** | ❌ | Manual | ✅ |
| **Best For** | Dev/Test | Production | Enterprise |

## 🔧 Verification Scripts

All modes include verification scripts to test deployment health:

- **monolithic/verify-monolithic-mode.sh**: Tests single container health
- **layered/verify-layered-mode.sh**: Tests all 3 layers independently

These scripts check:
- ✅ Container status
- ✅ Health endpoints
- ✅ Service dependencies
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ Inter-layer communication (layered mode)

## 📝 Configuration Files

### Docker Compose Files
Located in each mode's directory:
- `monolithic/docker-compose.yml` - Single container setup
- `layered/docker-compose.yml` - 3-layer setup

### Kubernetes Manifests
Located in `kubernetes/` directory:
- Deployments: `*-deployment.yaml`
- Services: `services.yaml`
- Configuration: `configmap.yaml`, `secrets.yaml`
- Scaling: `hpa.yaml`
- Ingress: `ingress.yaml`

## 🔗 Related Documentation

- **[Main README](../README.md)** - Project overview
- **[Docker Directory](../docker/)** - Dockerfile configurations
- **[Scripts Directory](../scripts/)** - Build automation scripts
- **[K8s Directory](../k8s/)** - Legacy Kubernetes manifests

---

**Need help choosing? See [deployment/README.md](README.md) for detailed comparison!**
