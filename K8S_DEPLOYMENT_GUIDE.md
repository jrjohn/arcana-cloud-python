# Kubernetes Deployment Guide

## Prerequisites

- `kubectl` CLI installed and configured
- Access to a Kubernetes cluster (local or cloud)
- Docker images built and pushed to registry

## Quick Start

### Option 1: Test Manifests (Dry Run)

```bash
# Validate all manifests without deploying
./scripts/test-k8s-manifests.sh
```

### Option 2: Deploy All at Once

```bash
# Deploy everything in correct order
kubectl apply -f k8s/
```

### Option 3: Step-by-Step Deployment (Recommended for First Time)

Follow the steps below for controlled deployment.

---

## Step-by-Step Deployment

### Step 1: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

**Verify:**
```bash
kubectl get namespace arcana-cloud
```

Expected output:
```
NAME           STATUS   AGE
arcana-cloud   Active   5s
```

---

### Step 2: Create Secrets

**IMPORTANT:** Update secrets before deploying to production!

```bash
# For development/testing (uses default test values)
kubectl apply -f k8s/secrets.yaml

# For production (create from environment variables)
kubectl create secret generic arcana-cloud-secrets \
  --from-literal=SECRET_KEY="${SECRET_KEY}" \
  --from-literal=JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
  --from-literal=DB_PASSWORD="${DB_PASSWORD}" \
  --from-literal=REDIS_PASSWORD="${REDIS_PASSWORD}" \
  -n arcana-cloud
```

**Verify:**
```bash
kubectl get secrets -n arcana-cloud
```

---

### Step 3: Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

**Verify:**
```bash
kubectl get configmap -n arcana-cloud
kubectl describe configmap arcana-cloud-config -n arcana-cloud
```

---

### Step 4: Create Persistent Volume Claims

```bash
kubectl apply -f k8s/pvc.yaml
```

**Verify:**
```bash
kubectl get pvc -n arcana-cloud
```

Expected output:
```
NAME              STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
mysql-data-pvc    Pending   -        10Gi       RWO            standard
redis-data-pvc    Pending   -        5Gi        RWO            standard
```

Status will change to `Bound` after deployment.

---

### Step 5: Deploy Databases

#### MySQL

```bash
kubectl apply -f k8s/mysql-deployment.yaml
```

**Verify:**
```bash
# Check StatefulSet
kubectl get statefulset mysql -n arcana-cloud

# Check pods
kubectl get pods -n arcana-cloud -l app=mysql

# Check logs
kubectl logs -n arcana-cloud mysql-0

# Wait for ready state
kubectl wait --for=condition=ready pod -l app=mysql -n arcana-cloud --timeout=300s
```

#### Redis

```bash
kubectl apply -f k8s/redis-deployment.yaml
```

**Verify:**
```bash
# Check deployment
kubectl get deployment redis -n arcana-cloud

# Check pods
kubectl get pods -n arcana-cloud -l app=redis

# Check logs
kubectl logs -n arcana-cloud -l app=redis

# Wait for ready state
kubectl wait --for=condition=ready pod -l app=redis -n arcana-cloud --timeout=300s
```

---

### Step 6: Deploy Application Layers

#### Repository Layer

```bash
kubectl apply -f k8s/repository-deployment.yaml
```

**Verify:**
```bash
kubectl get deployment repository-layer -n arcana-cloud
kubectl get pods -n arcana-cloud -l tier=repository
kubectl logs -n arcana-cloud -l tier=repository --tail=50
```

#### Service Layer

```bash
kubectl apply -f k8s/service-deployment.yaml
```

**Verify:**
```bash
kubectl get deployment service-layer -n arcana-cloud
kubectl get pods -n arcana-cloud -l tier=service
kubectl logs -n arcana-cloud -l tier=service --tail=50
```

#### Controller Layer

```bash
kubectl apply -f k8s/controller-deployment.yaml
```

**Verify:**
```bash
kubectl get deployment controller-layer -n arcana-cloud
kubectl get pods -n arcana-cloud -l tier=controller
kubectl logs -n arcana-cloud -l tier=controller --tail=50
```

---

### Step 7: Create Services

```bash
kubectl apply -f k8s/services.yaml
```

**Verify:**
```bash
kubectl get svc -n arcana-cloud
```

Expected output should include:
- `controller-layer` (ClusterIP)
- `service-layer` (ClusterIP)
- `repository-layer` (ClusterIP)
- `mysql-service` (ClusterIP)
- `redis-service` (ClusterIP)
- `arcana-cloud-external` (LoadBalancer)

---

### Step 8: Create Ingress

```bash
kubectl apply -f k8s/ingress.yaml
```

**Verify:**
```bash
kubectl get ingress -n arcana-cloud
kubectl describe ingress arcana-cloud-ingress -n arcana-cloud
```

---

### Step 9: Enable Autoscaling (Optional)

```bash
kubectl apply -f k8s/hpa.yaml
```

**Verify:**
```bash
kubectl get hpa -n arcana-cloud
kubectl describe hpa controller-layer-hpa -n arcana-cloud
```

---

### Step 10: Apply RBAC (Optional but Recommended)

```bash
kubectl apply -f k8s/rbac.yaml
```

**Verify:**
```bash
kubectl get serviceaccount -n arcana-cloud
kubectl get role -n arcana-cloud
kubectl get rolebinding -n arcana-cloud
```

---

## Verification Commands

### Check Overall Status

```bash
# All resources
kubectl get all -n arcana-cloud

# Pods with more details
kubectl get pods -n arcana-cloud -o wide

# Check pod status
kubectl get pods -n arcana-cloud --watch
```

### Check Logs

```bash
# Controller layer logs
kubectl logs -f deployment/controller-layer -n arcana-cloud

# Service layer logs
kubectl logs -f deployment/service-layer -n arcana-cloud

# Repository layer logs
kubectl logs -f deployment/repository-layer -n arcana-cloud

# MySQL logs
kubectl logs -f mysql-0 -n arcana-cloud

# Redis logs
kubectl logs -f -l app=redis -n arcana-cloud
```

### Shell into Pods

```bash
# Controller pod
POD_NAME=$(kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -n arcana-cloud -c controller -- /bin/bash

# MySQL pod
kubectl exec -it mysql-0 -n arcana-cloud -- mysql -u root -p

# Redis pod
kubectl exec -it -n arcana-cloud $(kubectl get pods -n arcana-cloud -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli
```

### Check Resource Usage

```bash
# CPU and memory usage
kubectl top pods -n arcana-cloud

# Node resources
kubectl top nodes
```

---

## Scaling

### Manual Scaling

```bash
# Scale controller layer
kubectl scale deployment controller-layer --replicas=5 -n arcana-cloud

# Scale service layer
kubectl scale deployment service-layer --replicas=3 -n arcana-cloud
```

### Check Autoscaling

```bash
# HPA status
kubectl get hpa -n arcana-cloud

# HPA events
kubectl describe hpa controller-layer-hpa -n arcana-cloud
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n arcana-cloud

# Check init container logs
kubectl logs <pod-name> -n arcana-cloud -c <init-container-name>
```

### Database Connection Issues

```bash
# Test MySQL connection from controller pod
POD_NAME=$(kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -n arcana-cloud -c controller -- nc -zv mysql-service 3306

# Test Redis connection
kubectl exec -it $POD_NAME -n arcana-cloud -c controller -- nc -zv redis-service 6379
```

### Service Discovery Issues

```bash
# Check DNS resolution
POD_NAME=$(kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -n arcana-cloud -c controller -- nslookup service-layer
kubectl exec -it $POD_NAME -n arcana-cloud -c controller -- nslookup mysql-service
```

### View Events

```bash
# All events in namespace
kubectl get events -n arcana-cloud --sort-by='.lastTimestamp'

# Watch events
kubectl get events -n arcana-cloud --watch
```

---

## Cleanup

### Delete Everything

```bash
# Delete all resources in namespace
kubectl delete namespace arcana-cloud

# Or delete specific resources
kubectl delete -f k8s/
```

### Delete Specific Components

```bash
# Delete application only (keep databases)
kubectl delete deployment controller-layer service-layer repository-layer -n arcana-cloud

# Delete databases only
kubectl delete statefulset mysql -n arcana-cloud
kubectl delete deployment redis -n arcana-cloud
```

---

## Production Checklist

Before deploying to production:

- [ ] Update secrets with strong random values
- [ ] Configure TLS certificates for ingress
- [ ] Set up proper persistent storage (not local storage)
- [ ] Configure backup strategy for databases
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Review and adjust resource limits
- [ ] Set up network policies
- [ ] Configure pod security policies
- [ ] Set up disaster recovery plan
- [ ] Configure autoscaling thresholds
- [ ] Test rolling updates
- [ ] Configure health checks appropriately
- [ ] Set up CI/CD pipeline

---

## Quick Commands Reference

```bash
# Test manifests
./scripts/test-k8s-manifests.sh

# Deploy all
kubectl apply -f k8s/

# Check status
kubectl get all -n arcana-cloud

# View logs
kubectl logs -f deployment/controller-layer -n arcana-cloud

# Shell into pod
kubectl exec -it -n arcana-cloud $(kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[0].metadata.name}') -c controller -- /bin/bash

# Scale deployment
kubectl scale deployment controller-layer --replicas=5 -n arcana-cloud

# Delete all
kubectl delete namespace arcana-cloud
```

---

## 🌐 Testing API from Browser

After deployment, you can access the API from your browser using several methods:

### Option 1: Port Forward (Quickest for Testing)

```bash
# Forward local port 8080 to controller service port 5000
kubectl port-forward -n arcana-cloud svc/controller-layer 8080:5000

# Access in browser
open http://localhost:8080/health
open http://localhost:8080/api/v1/users
```

**Test endpoints:**
```bash
# Health check
curl http://localhost:8080/health

# API status
curl http://localhost:8080/api/v1/status

# Get users (may require auth)
curl http://localhost:8080/api/v1/users

# Register user
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"Test123!"}'
```

---

### Option 2: NodePort Service (Development)

The NodePort service exposes the API on port 30000 of any cluster node.

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Access API
echo "API available at: http://${NODE_IP}:30000"

# Test in browser
open "http://${NODE_IP}:30000/health"

# Or use curl
curl "http://${NODE_IP}:30000/health"
```

**For Minikube:**
```bash
# Get Minikube IP
minikube ip

# Access API
open "http://$(minikube ip):30000/health"
```

**For Docker Desktop Kubernetes:**
```bash
# Access via localhost
open "http://localhost:30000/health"
```

---

### Option 3: LoadBalancer Service (Production)

The LoadBalancer service provides an external IP for production access.

```bash
# Get external IP
kubectl get svc arcana-cloud-external -n arcana-cloud

# Wait for EXTERNAL-IP to be assigned (may take 1-2 minutes)
kubectl get svc arcana-cloud-external -n arcana-cloud --watch

# Once assigned, access API
EXTERNAL_IP=$(kubectl get svc arcana-cloud-external -n arcana-cloud -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API available at: http://${EXTERNAL_IP}"

# Test in browser
open "http://${EXTERNAL_IP}/health"
```

**Note:** LoadBalancer requires cloud provider support (AWS, GCP, Azure). For local clusters (Minikube, Docker Desktop), the EXTERNAL-IP will remain `<pending>`.

---

### Option 4: Ingress (Production with Domain)

For production with a domain name:

**Prerequisites:**
```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Verify installation
kubectl get pods -n ingress-nginx

# Get ingress IP
kubectl get ingress -n arcana-cloud
```

**Update /etc/hosts (for local testing):**
```bash
# Get ingress IP
INGRESS_IP=$(kubectl get ingress arcana-cloud-ingress -n arcana-cloud -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add to /etc/hosts
echo "${INGRESS_IP} api.arcana-cloud.com" | sudo tee -a /etc/hosts

# Test
open "http://api.arcana-cloud.com/health"
curl "http://api.arcana-cloud.com/api/v1/status"
```

**Production DNS Setup:**
- Point your domain (e.g., `api.arcana-cloud.com`) to the ingress IP
- Configure TLS/SSL certificates using cert-manager
- Access via HTTPS: `https://api.arcana-cloud.com/api/v1`

---

### API Endpoints to Test

Once you have access, try these endpoints:

#### **Health & Status**
```bash
# Health check
GET /health
Response: {"status": "healthy"}

# Readiness check
GET /ready
Response: {"status": "ready"}

# API status
GET /api/v1/status
Response: {"version": "1.0.0", "environment": "production"}
```

#### **Authentication**
```bash
# Register new user
POST /api/v1/auth/register
Body: {
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePass123!"
}

# Login
POST /api/v1/auth/login
Body: {
  "username": "testuser",
  "password": "SecurePass123!"
}
Response: {
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "expires_in": 3600
}

# Refresh token
POST /api/v1/auth/refresh
Headers: Authorization: Bearer <refresh_token>
```

#### **User Management**
```bash
# Get all users (requires auth)
GET /api/v1/users
Headers: Authorization: Bearer <access_token>

# Get user by ID
GET /api/v1/users/{user_id}
Headers: Authorization: Bearer <access_token>

# Update user
PUT /api/v1/users/{user_id}
Headers: Authorization: Bearer <access_token>
Body: {
  "email": "newemail@example.com"
}

# Delete user
DELETE /api/v1/users/{user_id}
Headers: Authorization: Bearer <access_token>
```

---

### Browser Testing Tools

**Chrome/Firefox Extensions:**
- **Postman** - Full-featured API testing
- **Thunder Client** (VS Code) - Lightweight REST client
- **REST Client** (VS Code extension) - Test APIs from .http files

**Example REST Client file** (`.http`):
```http
### Health Check
GET http://localhost:8080/health

### Register User
POST http://localhost:8080/api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Test123!"
}

### Login
POST http://localhost:8080/api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "Test123!"
}

### Get Users (with token)
GET http://localhost:8080/api/v1/users
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### Troubleshooting Browser Access

**Connection Refused:**
```bash
# Check if pods are running
kubectl get pods -n arcana-cloud

# Check service endpoints
kubectl get endpoints -n arcana-cloud

# Check service
kubectl describe svc controller-layer -n arcana-cloud
```

**404 Not Found:**
```bash
# Check ingress rules
kubectl describe ingress arcana-cloud-ingress -n arcana-cloud

# Check controller logs
kubectl logs -n arcana-cloud -l tier=controller --tail=50
```

**Timeout:**
```bash
# Check if controller is healthy
kubectl get pods -n arcana-cloud -l tier=controller

# Test internal connectivity
POD_NAME=$(kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -n arcana-cloud -c controller -- curl localhost:5000/health
```

**CORS Issues:**
```bash
# CORS is configured in ingress.yaml
# Check ingress annotations
kubectl get ingress arcana-cloud-ingress -n arcana-cloud -o yaml | grep cors
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/jrjohn/arcana-cloud-python/issues
- Documentation: [README.md](README.md)
