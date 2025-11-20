# Kubernetes Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Common Kubernetes Commands](#common-kubernetes-commands)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Architecture](#architecture)

---

## Overview

This document explains the Kubernetes deployment process for the Arcana Cloud application, including common commands, troubleshooting steps, and real-world examples from our deployment journey.

### Application Architecture

The application uses a layered architecture deployed in Kubernetes:

```
┌─────────────────────────────────────┐
│     Controller Layer (Port 5000)    │  ← API Gateway / HTTP Endpoints
│         3 replicas                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer (Port 5001)      │  ← Business Logic
│         3 replicas                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Repository Layer (Port 5002)     │  ← Data Access / Database Operations
│         2 replicas                   │
└──────────────┬──────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼─────┐      ┌─────▼────┐
│  MySQL   │      │  Redis   │
│ Database │      │  Cache   │
└──────────┘      └──────────┘
```

---

## Prerequisites

1. **Docker Desktop** with Kubernetes enabled
2. **kubectl** CLI tool installed
3. **Docker** for building images

### Verify Prerequisites

```bash
# Check kubectl is installed
kubectl version --client

# Check Docker is running
docker ps

# Check Kubernetes cluster is accessible
kubectl cluster-info
```

**Example Output:**
```
Kubernetes control plane is running at https://kubernetes.docker.internal:6443
CoreDNS is running at https://kubernetes.docker.internal:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

---

## Quick Start

### 1. Build Docker Images

```bash
# Build all application layer images
./scripts/build-images.sh
```

**Why:** Creates Docker images for repository, service, and controller layers that Kubernetes pods will run.

**Example Output:**
```
========================================
Building Docker Images
========================================
Registry: arcanacloud
Version:  latest

✓ Successfully built arcanacloud/arcana-cloud-repository:latest
✓ Successfully built arcanacloud/arcana-cloud-service:latest
✓ Successfully built arcanacloud/arcana-cloud-controller:latest
```

### 2. Deploy to Kubernetes

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/
```

**Why:** Creates all resources (namespaces, secrets, configmaps, deployments, services, etc.) in Kubernetes.

### 3. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n arcana-cloud
```

**Expected Output:**
```
NAME                                READY   STATUS    RESTARTS   AGE
controller-layer-xxx                1/1     Running   0          2m
service-layer-xxx                   1/1     Running   0          2m
repository-layer-xxx                1/1     Running   0          2m
mysql-0                             1/1     Running   0          2m
redis-xxx                           1/1     Running   0          2m
```

### 4. Access the Application

```bash
# Forward local port 8080 to controller service port 5000
kubectl port-forward -n arcana-cloud svc/controller-layer 8080:5000
```

**Why:** Makes the controller service accessible on your local machine at `http://localhost:8080`.

**Test:**
```bash
curl http://localhost:8080/health
# Output: {"status":"healthy"}
```

---

## Common Kubernetes Commands

### 1. Viewing Resources

#### Get All Pods in a Namespace
```bash
kubectl get pods -n arcana-cloud
```

**Why:** Shows the status of all running pods in the arcana-cloud namespace.

**Use When:** You need to check if pods are running, crashing, or pending.

**Example Issue:**
```
NAME                                READY   STATUS              RESTARTS   AGE
repository-layer-xxx                0/1     ImagePullBackOff    0          2m
```

**What It Means:** Pod cannot pull the Docker image (image doesn't exist or wrong name).

---

#### Get Detailed Pod Information
```bash
kubectl describe pod <pod-name> -n arcana-cloud
```

**Why:** Provides detailed information about a pod including events, errors, and configuration.

**Use When:** A pod is failing and you need to understand why.

**Example:**
```bash
kubectl describe pod repository-layer-5fb9b5655c-pfwls -n arcana-cloud
```

**Example Output:**
```
Events:
  Type     Reason     Message
  ----     ------     -------
  Warning  Failed     Failed to pull image "arcanacloud/arcana-cloud-repository:latest":
                      Error response from daemon: pull access denied
```

**What This Tells You:** The image doesn't exist locally and Kubernetes tried to pull from a remote registry.

---

#### View Pod Logs
```bash
kubectl logs <pod-name> -n arcana-cloud
```

**Why:** Shows application logs from within the pod.

**Use When:** Checking application startup, errors, or debugging issues.

**Example:**
```bash
kubectl logs repository-layer-5fb9b5655c-pfwls -n arcana-cloud --tail=50
```

**Example Output:**
```
[2025-11-20 08:10:42] Starting gunicorn 23.0.0
[2025-11-20 08:10:42] Listening at: http://0.0.0.0:5002
10.1.0.1 - - "GET /health HTTP/1.1" 200
10.1.0.1 - - "GET /ready HTTP/1.1" 503
```

**What This Tells You:** The app started successfully but the `/ready` endpoint is failing (returning 503).

---

#### View Logs from Init Containers
```bash
kubectl logs <pod-name> -n arcana-cloud -c <init-container-name>
```

**Why:** Init containers run before the main container. If a pod is stuck in `Init:Error`, check their logs.

**Example:**
```bash
kubectl logs repository-layer-5fb9b5655c-pfwls -n arcana-cloud -c run-migrations
```

**Example Issue & Output:**
```
Traceback (most recent call last):
  File "/usr/local/bin/flask", line 7, in <module>
    sys.exit(main())
ImportError: Can't find Python file migrations/env.py
```

**What This Tells You:** The migrations directory is empty - migrations haven't been initialized.

**Solution:** Remove the migrations init container from the deployment.

---

### 2. Managing Pods

#### Restart Pods (by deleting them)
```bash
kubectl delete pods -l tier=repository -n arcana-cloud
```

**Why:** Kubernetes automatically recreates deleted pods. This forces pods to restart with new configuration or images.

**Use When:**
- You've updated deployment configuration
- You've built new Docker images with `imagePullPolicy: IfNotPresent`
- Pods are stuck in a bad state

**Example Issue:**
Pods are using old images even after rebuilding.

**Before Command:**
```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx                0/1     Running   0          30m  # Old image
```

**Execute:**
```bash
kubectl delete pods -l tier=repository -n arcana-cloud
```

**After Command:**
```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx                1/1     Running   0          10s  # New image, now ready!
```

---

#### Scale Deployment
```bash
kubectl scale deployment repository-layer --replicas=1 -n arcana-cloud
```

**Why:** Change the number of pod replicas (instances) for a deployment.

**Use When:**
- Debugging issues with multiple pods
- Reducing resource usage temporarily
- Scaling up for more traffic

**Example:**
```bash
# Scale down to 1 replica for easier debugging
kubectl scale deployment repository-layer --replicas=1 -n arcana-cloud

# Check the result
kubectl get pods -n arcana-cloud -l tier=repository
```

**Before:**
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx-1              0/1     Pending   0          2m
repository-layer-xxx-2              0/1     Pending   0          2m
```

**After:**
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx-1              1/1     Running   0          2m
```

---

#### Execute Commands Inside a Pod
```bash
kubectl exec -it <pod-name> -n arcana-cloud -- <command>
```

**Why:** Run commands inside a running pod for debugging.

**Use When:** Testing connectivity, checking files, or debugging application issues.

**Example 1: Test Database Connectivity**
```bash
kubectl exec -it repository-layer-5fb9b5655c-pfwls -n arcana-cloud -- nc -zv mysql-service 3306
```

**Output:**
```
mysql-service.arcana-cloud.svc.cluster.local [10.1.0.14] 3306 (mysql) open
```

**What This Tells You:** MySQL is reachable from the repository pod.

---

**Example 2: Test Application Endpoint**
```bash
kubectl exec repository-layer-5fb9b5655c-pfwls -n arcana-cloud -- curl -s http://localhost:5002/ready
```

**Output (Error Case):**
```json
{
  "error": "Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')",
  "status": "not ready"
}
```

**What This Tells You:** The `/ready` endpoint has a SQLAlchemy syntax error.

**Solution:** Update `app/__init__.py` to use `text('SELECT 1')` instead of `'SELECT 1'`.

---

### 3. Managing Deployments

#### Apply Updated Configuration
```bash
kubectl apply -f k8s/repository-deployment.yaml
```

**Why:** Updates a deployment with new configuration from a YAML file.

**Use When:** You've modified deployment configuration (env vars, image, probes, etc.).

**Example Issue:**
Pods can't pull images because `imagePullPolicy: Always` tries to pull from a remote registry, but images are only available locally.

**Change Made:**
```yaml
# k8s/repository-deployment.yaml
containers:
  - name: repository
    image: arcanacloud/arcana-cloud-repository:latest
    imagePullPolicy: IfNotPresent  # Changed from: Always
```

**Execute:**
```bash
kubectl apply -f k8s/repository-deployment.yaml
```

**Output:**
```
deployment.apps/repository-layer configured
```

**Verify:**
```bash
kubectl get deployment repository-layer -n arcana-cloud -o jsonpath='{.spec.template.spec.containers[0].imagePullPolicy}'
```

**Output:**
```
IfNotPresent
```

---

#### Rollout Restart
```bash
kubectl rollout restart deployment repository-layer -n arcana-cloud
```

**Why:** Gracefully restarts all pods in a deployment with zero downtime.

**Use When:**
- Configuration changed but pods didn't automatically restart
- Want to force pods to pull new images

**Example:**
```bash
kubectl rollout restart deployment repository-layer -n arcana-cloud
```

**Output:**
```
deployment.apps/repository-layer restarted
```

---

#### Check Rollout Status
```bash
kubectl rollout status deployment repository-layer -n arcana-cloud
```

**Why:** Monitor the progress of a deployment update.

**Example Output:**
```
Waiting for deployment "repository-layer" rollout to finish: 1 of 2 updated replicas are available...
deployment "repository-layer" successfully rolled out
```

---

### 4. Managing Services

#### List Services
```bash
kubectl get services -n arcana-cloud
```

**Why:** Shows all services (load balancers, ClusterIPs) that expose pods.

**Example Output:**
```
NAME               TYPE        CLUSTER-IP      PORT(S)    AGE
controller-layer   ClusterIP   10.96.100.10    5000/TCP   1h
service-layer      ClusterIP   10.96.100.11    5001/TCP   1h
repository-layer   ClusterIP   10.96.100.12    5002/TCP   1h
mysql-service      ClusterIP   10.96.100.13    3306/TCP   1h
```

---

#### Port Forwarding
```bash
kubectl port-forward -n arcana-cloud svc/controller-layer 8080:5000
```

**Why:** Forward local port to a service running in Kubernetes.

**Use When:** Accessing services running in Kubernetes from your local machine.

**Example Issue:**
```bash
kubectl port-forward -n arcana-cloud svc/controller-layer 8080:5000
```

**Error Output:**
```
error: unable to forward port because pod is not running. Current status=Pending
```

**What This Tells You:** No pods backing the service are in `Running` state.

**Check Pod Status:**
```bash
kubectl get pods -n arcana-cloud -l tier=controller
```

**Output:**
```
NAME                                READY   STATUS    RESTARTS   AGE
controller-layer-xxx                0/1     Init:0/1  0          2m
```

**What This Tells You:** Pod is stuck in init phase, waiting for dependencies.

---

**After Fixing (All Pods Running):**
```bash
kubectl port-forward -n arcana-cloud svc/controller-layer 8080:5000
```

**Output:**
```
Forwarding from 127.0.0.1:8080 -> 5000
Forwarding from [::1]:8080 -> 5000
```

**Test:**
```bash
curl http://localhost:8080/health
```

**Output:**
```json
{"status":"healthy"}
```

---

### 5. Debugging Commands

#### Check Events
```bash
kubectl get events -n arcana-cloud --sort-by='.lastTimestamp'
```

**Why:** Shows recent events in the namespace (pod starts, failures, errors).

**Use When:** Diagnosing cluster-level issues.

**Example Output:**
```
LAST SEEN   TYPE      REASON              OBJECT                          MESSAGE
2m          Warning   Failed              pod/repository-layer-xxx        Failed to pull image
1m          Normal    Pulled              pod/repository-layer-xxx        Container image already present on machine
30s         Normal    Started             pod/repository-layer-xxx        Started container
```

---

#### Check Resource Usage
```bash
kubectl top pods -n arcana-cloud
```

**Why:** Shows CPU and memory usage for pods.

**Use When:** Checking if pods are hitting resource limits.

**Example Output:**
```
NAME                                CPU(cores)   MEMORY(bytes)
repository-layer-xxx                100m         512Mi
service-layer-xxx                   50m          256Mi
controller-layer-xxx                30m          128Mi
```

---

#### Check Storage Classes
```bash
kubectl get storageclass
```

**Why:** Shows available storage classes for PersistentVolumeClaims.

**Use When:** PVCs are stuck in `Pending` state.

**Example Issue:**
```bash
kubectl get pvc -n arcana-cloud
```

**Output:**
```
NAME                     STATUS    VOLUME   CAPACITY   STORAGECLASS
mysql-data-pvc           Pending            0          standard
```

**Check Available Storage Classes:**
```bash
kubectl get storageclass
```

**Output:**
```
NAME                 PROVISIONER          AGE
hostpath (default)   docker.io/hostpath   5d
```

**What This Tells You:** The cluster uses `hostpath` storage class, but PVC requests `standard`.

**Solution:** Update `k8s/pvc.yaml`:
```yaml
storageClassName: hostpath  # Changed from: standard
```

**Apply Fix:**
```bash
kubectl delete pvc mysql-data-pvc -n arcana-cloud
kubectl apply -f k8s/pvc.yaml
```

**Verify:**
```bash
kubectl get pvc -n arcana-cloud
```

**Output:**
```
NAME                     STATUS   VOLUME                                     CAPACITY
mysql-data-pvc           Bound    pvc-xxx-xxx-xxx                            10Gi
```

---

#### Wait for Pod Readiness
```bash
kubectl wait --for=condition=ready pod -l tier=repository -n arcana-cloud --timeout=120s
```

**Why:** Blocks until pods matching the label selector are ready, or timeout.

**Use When:** Waiting for pods to become ready in scripts or CI/CD pipelines.

**Example Success:**
```bash
kubectl wait --for=condition=ready pod -l tier=repository -n arcana-cloud --timeout=120s
```

**Output:**
```
pod/repository-layer-5fb9b5655c-ls5cx condition met
pod/repository-layer-5fb9b5655c-wr6xd condition met
```

---

**Example Failure:**
```bash
kubectl wait --for=condition=ready pod -l tier=repository -n arcana-cloud --timeout=120s
```

**Output:**
```
error: timed out waiting for the condition on pods/repository-layer-5fb9b5655c-pfwls
```

**What This Tells You:** Pods didn't become ready within 120 seconds. Check logs and describe pod for errors.

---

## Troubleshooting Guide

### Issue 1: ImagePullBackOff

**Symptom:**
```bash
kubectl get pods -n arcana-cloud
```
```
NAME                                READY   STATUS             RESTARTS   AGE
repository-layer-xxx                0/1     ImagePullBackOff   0          2m
```

**Check Details:**
```bash
kubectl describe pod repository-layer-xxx -n arcana-cloud | grep -A 10 "Events:"
```

**Output:**
```
Events:
  Type     Reason     Message
  ----     ------     -------
  Warning  Failed     Failed to pull image "arcanacloud/arcana-cloud-repository:latest":
                      Error response from daemon: pull access denied for arcanacloud/arcana-cloud-repository,
                      repository does not exist or may require 'docker login'
```

**Root Cause:** Image doesn't exist locally and `imagePullPolicy: Always` tries to pull from remote registry.

**Solution:**

1. **Verify Image Exists Locally:**
```bash
docker images | grep arcana-cloud
```

**If Missing, Build It:**
```bash
./scripts/build-images.sh
```

2. **Update Deployment to Use Local Images:**
```yaml
# k8s/repository-deployment.yaml
containers:
  - name: repository
    image: arcanacloud/arcana-cloud-repository:latest
    imagePullPolicy: IfNotPresent  # Use local image if available
```

3. **Apply and Restart:**
```bash
kubectl apply -f k8s/repository-deployment.yaml
kubectl delete pods -l tier=repository -n arcana-cloud
```

4. **Verify:**
```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx                1/1     Running   0          30s
```

---

### Issue 2: Pod Stuck in Init Phase

**Symptom:**
```bash
kubectl get pods -n arcana-cloud
```
```
NAME                                READY   STATUS        RESTARTS   AGE
repository-layer-xxx                0/1     Init:Error    3          5m
```

**Check Init Container Logs:**
```bash
kubectl logs repository-layer-xxx -n arcana-cloud -c run-migrations
```

**Output:**
```
ImportError: Can't find Python file migrations/env.py
```

**Root Cause:** Init container `run-migrations` is trying to run database migrations, but migrations haven't been initialized.

**Solution:**

Remove the failing init container from deployment:

```yaml
# k8s/repository-deployment.yaml - BEFORE
initContainers:
  - name: wait-for-mysql
    image: busybox:1.35
    # ... wait for mysql ...

  - name: run-migrations  # ← Remove this
    image: arcanacloud/arcana-cloud-repository:latest
    command: ['flask', 'db', 'upgrade']
    # ...
```

```yaml
# k8s/repository-deployment.yaml - AFTER
initContainers:
  - name: wait-for-mysql
    image: busybox:1.35
    # ... wait for mysql ...

# removed run-migrations init container
```

**Apply and Restart:**
```bash
kubectl apply -f k8s/repository-deployment.yaml
kubectl delete pods -l tier=repository -n arcana-cloud
```

**Verify:**
```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx                1/1     Running   0          20s
```

---

### Issue 3: Readiness Probe Failing (503 Error)

**Symptom:**
```bash
kubectl get pods -n arcana-cloud
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx                0/1     Running   0          2m
```

**Check Logs:**
```bash
kubectl logs repository-layer-xxx -n arcana-cloud --tail=20
```

**Output:**
```
10.1.0.1 - - "GET /health HTTP/1.1" 200
10.1.0.1 - - "GET /ready HTTP/1.1" 503
10.1.0.1 - - "GET /ready HTTP/1.1" 503
```

**Test Endpoint Directly:**
```bash
kubectl exec repository-layer-xxx -n arcana-cloud -- curl -s http://localhost:5002/ready
```

**Output:**
```json
{
  "error": "Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')",
  "status": "not ready"
}
```

**Root Cause:** SQLAlchemy 2.0 requires explicit `text()` wrapper for raw SQL strings.

**Solution:**

Update `app/__init__.py`:

```python
# BEFORE
@app.route('/ready')
def ready():
    try:
        db.session.execute('SELECT 1')  # ❌ SQLAlchemy 2.0 error
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503
```

```python
# AFTER
@app.route('/ready')
def ready():
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))  # ✅ Correct for SQLAlchemy 2.0
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503
```

**Rebuild and Restart:**
```bash
# Rebuild images
./scripts/build-images.sh

# Restart pods to use new image
kubectl delete pods -l tier=repository -n arcana-cloud
```

**Verify:**
```bash
kubectl exec repository-layer-xxx -n arcana-cloud -- curl -s http://localhost:5002/ready
```

**Output:**
```json
{"status":"ready"}
```

```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-xxx                1/1     Running   0          1m
```

---

### Issue 4: PVC Stuck in Pending

**Symptom:**
```bash
kubectl get pvc -n arcana-cloud
```
```
NAME                     STATUS    VOLUME   CAPACITY   STORAGECLASS
mysql-data-pvc           Pending            0          standard
```

**Check Pod Events:**
```bash
kubectl describe pod repository-layer-xxx -n arcana-cloud
```

**Output:**
```
Events:
  Type     Reason            Message
  ----     ------            -------
  Warning  FailedScheduling  pod has unbound immediate PersistentVolumeClaims
```

**Check Available Storage Classes:**
```bash
kubectl get storageclass
```

**Output:**
```
NAME                 PROVISIONER          AGE
hostpath (default)   docker.io/hostpath   5d
```

**Root Cause:** PVC requests `storageClassName: standard` but cluster only has `hostpath`.

**Solution:**

Update `k8s/pvc.yaml`:

```yaml
# BEFORE
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-data-pvc
spec:
  storageClassName: standard  # ❌ Not available
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

```yaml
# AFTER
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-data-pvc
spec:
  storageClassName: hostpath  # ✅ Correct for Docker Desktop
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

**Apply Fix:**
```bash
# Delete old PVC
kubectl delete pvc mysql-data-pvc -n arcana-cloud

# Create new PVC
kubectl apply -f k8s/pvc.yaml
```

**Verify:**
```bash
kubectl get pvc -n arcana-cloud
```
```
NAME                     STATUS   VOLUME                                     CAPACITY
mysql-data-pvc           Bound    pvc-abc123-def456                          10Gi
```

---

### Issue 5: Multiple Old ReplicaSets Creating Pods

**Symptom:**
```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS             RESTARTS   AGE
repository-layer-545c9f6688-xxx     0/1     ImagePullBackOff   0          5m
repository-layer-7fc4499d4d-xxx     0/1     ImagePullBackOff   0          5m
repository-layer-5fb9b5655c-xxx     1/1     Running            0          1m
```

**Check ReplicaSets:**
```bash
kubectl get replicasets -n arcana-cloud -l tier=repository
```

**Output:**
```
NAME                          DESIRED   CURRENT   READY   AGE
repository-layer-545c9f6688   1         1         0       5m
repository-layer-7fc4499d4d   1         1         0       5m
repository-layer-5fb9b5655c   1         1         1       1m
```

**Root Cause:** Multiple old ReplicaSets still have desired replicas > 0.

**Solution:**

Scale down old ReplicaSets and delete orphaned pods:

```bash
# Delete old replicasets (this won't delete pods)
kubectl delete replicaset repository-layer-545c9f6688 repository-layer-7fc4499d4d -n arcana-cloud

# Delete old pods
kubectl delete pod repository-layer-545c9f6688-xxx repository-layer-7fc4499d4d-xxx -n arcana-cloud
```

**Or scale the deployment to reset:**
```bash
# Scale to 0
kubectl scale deployment repository-layer --replicas=0 -n arcana-cloud

# Wait for pods to terminate
sleep 5

# Scale back to desired count
kubectl scale deployment repository-layer --replicas=2 -n arcana-cloud
```

**Verify:**
```bash
kubectl get pods -n arcana-cloud -l tier=repository
```
```
NAME                                READY   STATUS    RESTARTS   AGE
repository-layer-5fb9b5655c-xxx     1/1     Running   0          30s
repository-layer-5fb9b5655c-yyy     1/1     Running   0          30s
```

---

## Architecture

### Deployment Strategy

- **Rolling Update**: Zero-downtime deployments with `maxSurge: 1` and `maxUnavailable: 0`
- **Health Checks**: Liveness, readiness, and startup probes for each layer
- **Init Containers**: Ensure dependencies (MySQL, Repository layer, Service layer) are ready before starting

### Resource Allocation

| Layer        | CPU Request | Memory Request | CPU Limit | Memory Limit |
|--------------|-------------|----------------|-----------|--------------|
| Repository   | 400m        | 512Mi          | 1000m     | 1Gi          |
| Service      | 300m        | 384Mi          | 750m      | 768Mi        |
| Controller   | 250m        | 256Mi          | 500m      | 512Mi        |

### Service Discovery

All layers communicate using Kubernetes DNS:
- `mysql-service.arcana-cloud.svc.cluster.local:3306`
- `redis-service.arcana-cloud.svc.cluster.local:6379`
- `repository-layer.arcana-cloud.svc.cluster.local:5002`
- `service-layer.arcana-cloud.svc.cluster.local:5001`

---

## Additional Resources

### Kubernetes Documentation
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Debugging Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

### Project-Specific Files
- [Build Script](../scripts/build-images.sh)
- [Kubernetes Manifests](../k8s/)
- [Application Configuration](../app/__init__.py)

---

## Summary of Key Learnings

1. **imagePullPolicy Matters**: Use `IfNotPresent` for local development to avoid pulling from remote registries
2. **Init Containers Block Pod Startup**: If init containers fail, pods won't start. Remove or fix them.
3. **SQLAlchemy 2.0 Requires text()**: Raw SQL strings must be wrapped in `text()` function
4. **Storage Classes Vary by Cluster**: Docker Desktop uses `hostpath`, cloud providers use different classes
5. **Readiness Probes Affect Service Routing**: Pods not passing readiness checks won't receive traffic
6. **Labels Are Powerful**: Use labels to select and manage groups of pods efficiently

---

**Generated:** 2025-11-20
**Kubernetes Version:** 1.34
**Docker Desktop Version:** Latest
