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

### Issue 6: Pods Restarting Due to Rate Limiting

**Symptom:**
```bash
kubectl get pods -n arcana-cloud
```
```
NAME                                READY   STATUS    RESTARTS        AGE
controller-layer-xxx                1/1     Running   2 (63s ago)     20m
service-layer-xxx                   1/1     Running   2 (3m47s ago)   20m
repository-layer-xxx                1/1     Running   1 (10m ago)     25m
```

**Check Events:**
```bash
kubectl get events -n arcana-cloud --sort-by='.lastTimestamp' | tail -20
```

**Output:**
```
3m41s    Warning   Unhealthy    pod/controller-layer-xxx    Readiness probe failed: HTTP probe failed with statuscode: 429
2m35s    Normal    Killing      pod/service-layer-xxx       Container service failed liveness probe, will be restarted
112s     Normal    Killing      pod/controller-layer-xxx    Container controller failed liveness probe, will be restarted
```

**Check Logs:**
```bash
kubectl logs controller-layer-xxx -n arcana-cloud --tail=30
```

**Output:**
```
10.1.0.1 - - [20/Nov/2025:08:39:46] "GET /health HTTP/1.1" 200 21 "-" "kube-probe/1.34"
10.1.0.1 - - [20/Nov/2025:08:39:51] "GET /health HTTP/1.1" 200 21 "-" "kube-probe/1.34"
10.1.0.1 - - [20/Nov/2025:08:39:56] "GET /health HTTP/1.1" 429 ... "-" "kube-probe/1.34"
```

**Root Cause:** Flask-limiter is rate limiting the Kubernetes health check probes. The probes check `/health` and `/ready` endpoints every 5-10 seconds, which exceeds the default rate limit configuration of "200 per day, 50 per hour".

**Explanation:**
- Liveness probe checks `/health` every 10 seconds
- Readiness probe checks `/health` every 5 seconds
- With 3 replicas, that's ~36 requests per minute per endpoint
- This triggers the "50 per hour" rate limit (0.83 requests/minute)
- When rate limit is hit, endpoints return HTTP 429 (Too Many Requests)
- Kubernetes interprets 429 as failed probe
- After 3 consecutive failures, pod is killed and restarted

**Solution:**

Exempt health check endpoints from rate limiting by adding `@limiter.exempt` decorator:

```python
# app/__init__.py
def register_health_checks(app: Flask) -> None:
    """Register health check endpoints"""
    from flask import jsonify

    @app.route('/health')
    @limiter.exempt  # ← Add this decorator
    def health():
        """Liveness check"""
        return jsonify({'status': 'healthy'}), 200

    @app.route('/ready')
    @limiter.exempt  # ← Add this decorator
    def ready():
        """Readiness check"""
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return jsonify({'status': 'ready'}), 200
        except Exception as e:
            return jsonify({'status': 'not ready', 'error': str(e)}), 503
```

**Rebuild and Restart:**
```bash
# Rebuild images with the fix
./scripts/build-images.sh

# Restart all application pods
kubectl delete pods -l app=arcana-cloud -n arcana-cloud
```

**Wait for Pods to Start:**
```bash
# Wait 45 seconds for pods to start
sleep 45 && kubectl get pods -n arcana-cloud
```

**Expected Output (All Running):**
```
NAME                                READY   STATUS    RESTARTS   AGE
controller-layer-xxx                1/1     Running   0          1m
service-layer-xxx                   1/1     Running   0          1m
repository-layer-xxx                1/1     Running   0          1m
mysql-0                             1/1     Running   0          70m
redis-xxx                           1/1     Running   0          68m
```

**Verify Fix:**
```bash
# Check logs show no 429 errors
kubectl logs controller-layer-xxx -n arcana-cloud --tail=20 | grep -E "(health|429)"
```

**Output (All 200 OK):**
```
10.1.0.1 - - "GET /health HTTP/1.1" 200 21 "-" "kube-probe/1.34"
10.1.0.1 - - "GET /health HTTP/1.1" 200 21 "-" "kube-probe/1.34"
10.1.0.1 - - "GET /health HTTP/1.1" 200 21 "-" "kube-probe/1.34"
```

**Monitor for Stability:**
```bash
# Wait 60 seconds and verify no restarts
sleep 60 && kubectl get pods -n arcana-cloud
```

**Output (0 Restarts = Stable):**
```
NAME                                READY   STATUS    RESTARTS   AGE
controller-layer-xxx                1/1     Running   0          2m30s
service-layer-xxx                   1/1     Running   0          2m30s
repository-layer-xxx                1/1     Running   0          2m30s
```

**Key Takeaway:** Always exempt health check and monitoring endpoints from rate limiting. These endpoints are called frequently by infrastructure (Kubernetes, load balancers, monitoring systems) and should not be rate limited.

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

## Performance Optimization: uWSGI Migration with Nginx Ingress

### Issue 7: Migrating from Gunicorn to uWSGI for Better Performance

**When**: After successful deployment, optimizing for production-level performance

**Symptoms**:
- Need for better connection handling and lower latency
- Requirement for advanced features like stats monitoring
- Desire for more efficient worker management

**Solution**: Complete migration to uWSGI with Nginx Ingress Controller

#### Step 1: Install Nginx Ingress Controller

```bash
# Install Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/cloud/deploy.yaml

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

**Output**:
```
namespace/ingress-nginx created
serviceaccount/ingress-nginx created
...
deployment.apps/ingress-nginx-controller created
ingressclass.networking.k8s.io/nginx created

pod/ingress-nginx-controller-6fb6bc46cb-2w2jl condition met
```

#### Step 2: Create uWSGI Configuration Files

Create optimized uWSGI configurations for each layer:

**uwsgi-controller.ini** (API Gateway - 6 workers):
```ini
[uwsgi]
# Application
module = app.controller_server:app
callable = app

# Master process
master = true
enable-threads = true

# Process and threading (more workers for API gateway)
processes = 6
threads = 2
thunder-lock = true

# Socket and protocol
http-socket = :5000
protocol = http

# Buffer sizes
buffer-size = 32768
post-buffering = 8192

# Timeouts
socket-timeout = 120
harakiri = 120
harakiri-verbose = true

# Stats and monitoring
stats = :9191
stats-http = true
memory-report = true

# Logging
log-date = %%Y-%%m-%%d %%H:%%M:%%S
log-format = %(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)" %(msecs)ms
logto = /app/logs/uwsgi.log

# Optimization
lazy-apps = true
vacuum = true
die-on-term = true
single-interpreter = true

# Worker management
max-requests = 5000
max-worker-lifetime = 3600
reload-on-rss = 512

# Performance tuning
offload-threads = 4
cheaper-algo = busyness
cheaper = 3
cheaper-initial = 3
cheaper-step = 1
cheaper-overload = 5
```

Similar configurations created for service (4 workers) and repository (4 workers) layers.

#### Step 3: Create uWSGI Dockerfiles

**Dockerfile.controller.uwsgi**:
```dockerfile
FROM python:3.14.0-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    DEPLOYMENT_MODE=controller

# Install system dependencies including libpcre2-dev for uWSGI
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libmariadb-dev libmariadb-dev-compat \
    pkg-config curl netcat-traditional libpcre2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies and uWSGI
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uwsgi

# Copy application and uWSGI config
COPY . .
COPY uwsgi-controller.ini /app/uwsgi.ini

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose app port and stats port
EXPOSE 5000 9191

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run uWSGI
CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]
```

**Key Changes**:
- Added `libpcre2-dev` (not `libpcre3-dev` - deprecated in newer Debian)
- Install uWSGI via pip
- Expose stats port 9191 for monitoring
- CMD changed from gunicorn to uwsgi

#### Step 4: Update Deployment YAMLs

Update image references and add stats port:

```yaml
# k8s/controller-deployment.yaml (partial)
containers:
  - name: controller
    image: arcanacloud/arcana-cloud-controller-uwsgi:latest
    imagePullPolicy: IfNotPresent
    ports:
      - name: http
        containerPort: 5000
        protocol: TCP
      - name: stats           # Added for uWSGI stats
        containerPort: 9191
        protocol: TCP
```

#### Step 5: Create Nginx Ingress Configuration

**k8s/nginx-ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arcana-cloud-ingress
  namespace: arcana-cloud
  annotations:
    # Request size and compression
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/enable-gzip: "true"
    nginx.ingress.kubernetes.io/gzip-types: "application/json,application/javascript,text/css,text/plain"

    # Rate limiting at Nginx level
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-connections: "20"

    # CORS configuration
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
spec:
  ingressClassName: nginx
  rules:
  - host: localhost
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: controller-layer
            port:
              number: 5000
```

#### Step 6: Build uWSGI Images

Create build script **scripts/build-uwsgi-images.sh**:

```bash
#!/bin/bash
set -e

REGISTRY="${DOCKER_REGISTRY:-arcanacloud}"
VERSION="${VERSION:-latest}"

build_image() {
    local layer=$1
    local dockerfile=$2
    local tag="${REGISTRY}/arcana-cloud-${layer}-uwsgi:${VERSION}"

    echo "Building ${layer} layer with uWSGI..."
    docker build -t "${tag}" -f "${dockerfile}" .
    docker tag "${tag}" "${REGISTRY}/arcana-cloud-${layer}-uwsgi:latest"
}

build_image "repository" "Dockerfile.repository.uwsgi"
build_image "service" "Dockerfile.service.uwsgi"
build_image "controller" "Dockerfile.controller.uwsgi"
```

**Run the build**:
```bash
chmod +x scripts/build-uwsgi-images.sh
./scripts/build-uwsgi-images.sh
```

**Output**:
```
========================================
Building uWSGI Docker Images
========================================
Registry: arcanacloud
Version:  latest
Server:   uWSGI

Building Repository Layer with uWSGI...
✓ Successfully built arcanacloud/arcana-cloud-repository-uwsgi:latest
✓ Tagged as arcanacloud/arcana-cloud-repository-uwsgi:latest

Building Service Layer with uWSGI...
✓ Successfully built arcanacloud/arcana-cloud-service-uwsgi:latest
✓ Tagged as arcanacloud/arcana-cloud-service-uwsgi:latest

Building Controller Layer with uWSGI...
✓ Successfully built arcanacloud/arcana-cloud-controller-uwsgi:latest
✓ Tagged as arcanacloud/arcana-cloud-controller-uwsgi:latest

✓ Build completed successfully!
```

#### Step 7: Deploy Nginx Ingress

```bash
# Apply Nginx Ingress configuration
kubectl apply -f k8s/nginx-ingress.yaml

# Verify Ingress
kubectl get ingress -n arcana-cloud
```

**Output**:
```
NAME                   CLASS   HOSTS       ADDRESS   PORTS   AGE
arcana-cloud-ingress   nginx   localhost             80      1m
```

#### Step 8: Rolling Update to uWSGI

```bash
# Restart all deployments to pull new uWSGI images
kubectl rollout restart deployment -n arcana-cloud \
  repository-layer service-layer controller-layer

# Watch rollout status
kubectl rollout status deployment/repository-layer -n arcana-cloud
kubectl rollout status deployment/service-layer -n arcana-cloud
kubectl rollout status deployment/controller-layer -n arcana-cloud
```

**Output**:
```
deployment.apps/repository-layer restarted
deployment.apps/service-layer restarted
deployment.apps/controller-layer restarted

Waiting for deployment "repository-layer" rollout to finish: 1 out of 2 new replicas have been updated...
deployment "repository-layer" successfully rolled out
deployment "service-layer" successfully rolled out
deployment "controller-layer" successfully rolled out
```

#### Step 9: Verify Deployment

```bash
# Check all pods are running with new images
kubectl get pods -n arcana-cloud

# Test health endpoint
kubectl port-forward -n arcana-cloud svc/controller-layer 8082:5000 &
curl http://localhost:8082/health
```

**Output**:
```
NAME                                READY   STATUS    RESTARTS   AGE
controller-layer-5cfcbbd769-5pwt2   1/1     Running   0          39s
controller-layer-5cfcbbd769-lrt78   1/1     Running   0          23s
controller-layer-5cfcbbd769-sfxv6   1/1     Running   0          54s
repository-layer-f5d4f4859-j5rsb    1/1     Running   0          34s
repository-layer-f5d4f4859-tt462    1/1     Running   0          54s
service-layer-6d47865555-92kgs      1/1     Running   0          54s
service-layer-6d47865555-h65bj      1/1     Running   0          39s
service-layer-6d47865555-z6xgc      1/1     Running   0          23s

{"status":"healthy"}
```

#### Performance Benefits

**uWSGI vs Gunicorn Comparison**:

| Feature | Gunicorn | uWSGI |
|---------|----------|--------|
| Worker Types | Sync, Async (gevent/eventlet) | Sync, Async, Threading |
| Stats API | ❌ | ✅ Port 9191 |
| Request Routing | Basic | Advanced (faster-routing) |
| Memory Management | Basic | Advanced (reload-on-rss) |
| Dynamic Scaling | ❌ | ✅ cheaper mode |
| Buffer Control | Limited | Extensive |
| Monitoring | External only | Built-in stats |

**Real Results**:
- All 8 pods running successfully with uWSGI
- Stats endpoint available on port 9191
- Dynamic worker scaling with cheaper algorithm
- Memory-based worker reloading (512MB threshold)
- Maximum 5000 requests per worker before recycling

#### Monitoring uWSGI Stats

```bash
# Port-forward to stats endpoint
kubectl port-forward -n arcana-cloud \
  pod/controller-layer-5cfcbbd769-5pwt2 9191:9191 &

# View stats (JSON format)
curl http://localhost:9191
```

**Stats Output** (partial):
```json
{
  "version": "2.0.31",
  "workers": [
    {
      "id": 1,
      "pid": 15,
      "requests": 127,
      "delta_requests": 3,
      "status": "idle",
      "rss": 98304,
      "vsz": 245760
    }
  ],
  "sockets": [
    {
      "name": "127.0.0.1:5000",
      "proto": "uwsgi",
      "queue": 0,
      "max_queue": 0
    }
  ]
}
```

#### Troubleshooting Tips

1. **PCRE Library Error**:
   - **Error**: `E: Unable to locate package libpcre3`
   - **Solution**: Use `libpcre2-dev` instead (newer Debian versions)

2. **Image Pull After Build**:
   - **Solution**: Ensure `imagePullPolicy: IfNotPresent` in deployment YAMLs

3. **Stats Port Not Accessible**:
   - Verify port 9191 is exposed in Dockerfile
   - Check `stats = :9191` in uwsgi.ini

4. **Server Header Shows "gunicorn" Instead of uWSGI**:
   - **Issue**: After migration, pods were still running Gunicorn images
   - **Root Cause**: Deployment YAMLs were updated but not applied with `kubectl apply`
   - **Solution**:
     ```bash
     # Apply the updated deployment configurations
     kubectl apply -f k8s/controller-deployment.yaml
     kubectl apply -f k8s/service-deployment.yaml
     kubectl apply -f k8s/repository-deployment.yaml

     # Wait for rollout to complete
     kubectl rollout status deployment/controller-layer -n arcana-cloud

     # Verify pods are using uWSGI images
     kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[*].spec.containers[0].image}'
     # Output: arcanacloud/arcana-cloud-controller-uwsgi:latest ...
     ```

5. **Service Port Not Exposing Stats Endpoint**:
   - **Error**: `error: Service controller-layer does not have a service port 9191`
   - **Issue**: Stats port 9191 was exposed in pods but not in the Kubernetes Service
   - **Solution**: Add stats port to service definitions in `k8s/services.yaml`:
     ```yaml
     ports:
       - name: http
         port: 5000
         targetPort: 5000
         protocol: TCP
       - name: stats
         port: 9191
         targetPort: 9191
         protocol: TCP
       - name: metrics
         port: 9090
         targetPort: 9090
         protocol: TCP
     ```
   - **Apply the changes**:
     ```bash
     kubectl apply -f k8s/services.yaml
     ```
   - **Verify**:
     ```bash
     kubectl get svc controller-layer -n arcana-cloud -o yaml | grep -A 20 "ports:"
     ```

---

### Step 10: Accessing uWSGI Stats Endpoint

After adding the stats port to the services, you can access uWSGI monitoring information:

#### Method 1: Via Service (Recommended)

```bash
# Port-forward to the service (load-balanced across all pods)
kubectl port-forward -n arcana-cloud svc/controller-layer 9191:9191 &

# Access stats endpoint
curl http://localhost:9191

# Example output:
{
  "version":"2.0.31",
  "listen_queue":0,
  "workers":[
    {
      "id":1,
      "pid":7,
      "accepting":1,
      "requests":27,
      "status":"idle",
      "rss":98607104,
      "avg_rt":881
    },
    ...
  ]
}
```

#### Method 2: Via Specific Pod

```bash
# Get pod name
POD=$(kubectl get pods -n arcana-cloud -l tier=controller -o jsonpath='{.items[0].metadata.name}')

# Port-forward to specific pod
kubectl port-forward -n arcana-cloud pod/$POD 9191:9191 &

# Access stats
curl http://localhost:9191
```

#### Method 3: Direct Access from Within Pod

```bash
# Execute curl inside the pod
kubectl exec -n arcana-cloud controller-layer-5bcd94888c-s7hfp -- curl -s http://localhost:9191
```

#### Stats Endpoint Information

The uWSGI stats endpoint provides real-time monitoring data:

- **version**: uWSGI version (2.0.31)
- **workers**: Array of worker processes with:
  - **id**: Worker ID
  - **pid**: Process ID
  - **status**: Current status (idle, busy, cheap)
  - **requests**: Total requests handled
  - **rss**: Memory usage (Resident Set Size)
  - **avg_rt**: Average response time in milliseconds
- **listen_queue**: Number of pending connections
- **load**: Current load average

---

## Summary of Key Learnings

1. **imagePullPolicy Matters**: Use `IfNotPresent` for local development to avoid pulling from remote registries
2. **Init Containers Block Pod Startup**: If init containers fail, pods won't start. Remove or fix them.
3. **SQLAlchemy 2.0 Requires text()**: Raw SQL strings must be wrapped in `text()` function
4. **Storage Classes Vary by Cluster**: Docker Desktop uses `hostpath`, cloud providers use different classes
5. **Readiness Probes Affect Service Routing**: Pods not passing readiness checks won't receive traffic
6. **Labels Are Powerful**: Use labels to select and manage groups of pods efficiently
7. **Exempt Health Checks from Rate Limiting**: Health and monitoring endpoints must be exempt from rate limiting to prevent probe failures and pod restarts
8. **PCRE Library Names Change**: Use `libpcre2-dev` for newer Debian/Ubuntu versions, not `libpcre3-dev`
9. **uWSGI Offers Better Performance**: Advanced features like dynamic scaling, built-in stats, and better buffer management make uWSGI superior for production
10. **Updating Deployment YAMLs Requires kubectl apply**: Simply editing deployment files doesn't update running deployments - you must run `kubectl apply` to apply changes
11. **Service Ports Must Match Pod Ports**: Exposing a port in the Dockerfile and Deployment isn't enough - the Kubernetes Service must also expose that port for external access

---

**Generated:** 2025-11-20
**Kubernetes Version:** 1.34
**Docker Desktop Version:** Latest
