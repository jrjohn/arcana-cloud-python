# SSL/TLS Setup Guide

This guide covers SSL/TLS setup for the Arcana Cloud project, including both development (self-signed certificates) and production (Let's Encrypt) configurations.

## Table of Contents
1. [Development Setup (Self-Signed Certificates)](#development-setup-self-signed-certificates)
2. [Docker Compose with SSL](#docker-compose-with-ssl)
3. [Kubernetes with SSL](#kubernetes-with-ssl)
4. [Production Setup (Let's Encrypt)](#production-setup-lets-encrypt)
5. [Troubleshooting](#troubleshooting)

---

## Development Setup (Self-Signed Certificates)

### Step 1: Generate SSL Certificates

Use the provided script to generate self-signed SSL certificates:

```bash
# Generate certificates for localhost (default)
./scripts/generate-ssl-certs.sh

# Generate certificates for a custom domain
./scripts/generate-ssl-certs.sh --domain api.arcana-cloud.com --days 365
```

This will create the following files in `nginx/ssl/`:
- `key.pem` - Private key
- `cert.pem` - SSL certificate
- `csr.pem` - Certificate signing request

### Step 2: Verify Certificate Generation

```bash
# Check certificate details
openssl x509 -in nginx/ssl/cert.pem -noout -text

# Verify certificate and key match
openssl x509 -noout -modulus -in nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in nginx/ssl/key.pem | openssl md5
```

### Step 3: Trust the Certificate (Optional for Development)

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain nginx/ssl/cert.pem
```

**Linux:**
```bash
sudo cp nginx/ssl/cert.pem /usr/local/share/ca-certificates/arcana-cloud.crt
sudo update-ca-certificates
```

**Windows:**
```powershell
certutil -addstore -f "ROOT" nginx\ssl\cert.pem
```

---

## Docker Compose with SSL

### Step 1: Build uWSGI Images

```bash
# Build all uWSGI images
./scripts/build-uwsgi-images.sh

# Or build individually
docker build -f dockerfiles/Dockerfile.controller.uwsgi -t arcana-cloud-controller-uwsgi:latest .
docker build -f dockerfiles/Dockerfile.service.uwsgi -t arcana-cloud-service-uwsgi:latest .
docker build -f dockerfiles/Dockerfile.repository.uwsgi -t arcana-cloud-repository-uwsgi:latest .
```

### Step 2: Start Services with SSL

```bash
# Start all services with Nginx SSL proxy
docker-compose -f docker-compose-nginx-ssl.yml up -d

# Check status
docker-compose -f docker-compose-nginx-ssl.yml ps

# View logs
docker-compose -f docker-compose-nginx-ssl.yml logs -f nginx-proxy
```

### Step 3: Test SSL Connection

```bash
# Test HTTPS endpoint
curl -k https://localhost/health

# Test with verbose output
curl -kv https://localhost/api/v1/health

# Check SSL certificate
openssl s_client -connect localhost:443 -servername localhost
```

### Step 4: Access uWSGI Stats

```bash
# Controller layer stats
curl http://localhost:9191

# Access through Nginx (internal endpoint)
docker exec arcana-nginx-ssl curl http://controller-layer:9191
```

### Step 5: Stop Services

```bash
# Stop all services
docker-compose -f docker-compose-nginx-ssl.yml down

# Stop and remove volumes
docker-compose -f docker-compose-nginx-ssl.yml down -v
```

---

## Kubernetes with SSL

### Step 1: Generate SSL Certificates

```bash
# Generate certificates for your domain
./scripts/generate-ssl-certs.sh --domain api.arcana-cloud.com
```

### Step 2: Create Kubernetes TLS Secret

```bash
# Create namespace if it doesn't exist
kubectl create namespace arcana-cloud

# Create TLS secret from certificate files
kubectl create secret tls arcana-cloud-tls \
  --cert=nginx/ssl/cert.pem \
  --key=nginx/ssl/key.pem \
  -n arcana-cloud

# Verify secret creation
kubectl get secret arcana-cloud-tls -n arcana-cloud -o yaml
```

### Step 3: Install Nginx Ingress Controller

```bash
# Install Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Verify installation
kubectl get pods -n ingress-nginx
```

### Step 4: Deploy Application with SSL

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mysql-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/services.yaml

# Deploy uWSGI application layers
kubectl apply -f k8s/controller-deployment.yaml
kubectl apply -f k8s/service-deployment.yaml
kubectl apply -f k8s/repository-deployment.yaml

# Apply Nginx Ingress with SSL
kubectl apply -f k8s/nginx-ingress.yaml

# Wait for deployments to be ready
kubectl rollout status deployment/controller-layer -n arcana-cloud
kubectl rollout status deployment/service-layer -n arcana-cloud
kubectl rollout status deployment/repository-layer -n arcana-cloud
```

### Step 5: Verify SSL Configuration

```bash
# Check Ingress configuration
kubectl describe ingress arcana-cloud-ingress -n arcana-cloud

# Test HTTPS through Ingress (if using LoadBalancer)
curl -k https://$(kubectl get ingress arcana-cloud-ingress -n arcana-cloud -o jsonpath='{.status.loadBalancer.ingress[0].ip}')/health

# Test locally with port forwarding
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8443:443
curl -k https://localhost:8443/health
```

### Step 6: Update TLS Secret (if needed)

```bash
# Delete existing secret
kubectl delete secret arcana-cloud-tls -n arcana-cloud

# Create new secret with updated certificates
kubectl create secret tls arcana-cloud-tls \
  --cert=nginx/ssl/cert.pem \
  --key=nginx/ssl/key.pem \
  -n arcana-cloud

# Restart Ingress controller to pick up changes
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
```

---

## Production Setup (Let's Encrypt)

### Prerequisites

1. **Domain name** pointing to your server/load balancer
2. **Cert-Manager** installed in Kubernetes cluster
3. **Valid email** for Let's Encrypt notifications

### Step 1: Install Cert-Manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Verify installation
kubectl get pods -n cert-manager

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=120s
```

### Step 2: Create ClusterIssuer for Let's Encrypt

Create `k8s/letsencrypt-issuer.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    # Production Let's Encrypt server
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    # Staging Let's Encrypt server (for testing)
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

Apply the ClusterIssuer:

```bash
kubectl apply -f k8s/letsencrypt-issuer.yaml
```

### Step 3: Update Ingress for Let's Encrypt

Modify `k8s/nginx-ingress.yaml` to use cert-manager:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arcana-cloud-ingress
  namespace: arcana-cloud
  annotations:
    # Cert-manager annotations
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    acme.cert-manager.io/http01-edit-in-place: "true"

    # Nginx annotations (keep existing ones)
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    # ... other annotations ...
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.arcana-cloud.com
    secretName: arcana-cloud-tls-prod  # Cert-manager will create this
  rules:
  - host: api.arcana-cloud.com
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

### Step 4: Apply and Verify

```bash
# Apply updated Ingress
kubectl apply -f k8s/nginx-ingress.yaml

# Watch certificate creation
kubectl get certificate -n arcana-cloud -w

# Check certificate details
kubectl describe certificate arcana-cloud-tls-prod -n arcana-cloud

# Verify certificate is ready
kubectl get secret arcana-cloud-tls-prod -n arcana-cloud
```

### Step 5: Test Production SSL

```bash
# Test HTTPS with valid certificate
curl https://api.arcana-cloud.com/health

# Check SSL certificate
openssl s_client -connect api.arcana-cloud.com:443 -servername api.arcana-cloud.com

# Verify certificate chain
curl -vI https://api.arcana-cloud.com/health
```

---

## Troubleshooting

### Issue 1: Certificate Not Trusted in Browser

**Problem:** Browser shows "Your connection is not private" error

**Solution:**
- **Development:** This is expected with self-signed certificates. Click "Advanced" → "Proceed to localhost (unsafe)"
- **Production:** Verify Let's Encrypt certificate was issued successfully:
  ```bash
  kubectl describe certificate arcana-cloud-tls-prod -n arcana-cloud
  kubectl get certificaterequest -n arcana-cloud
  ```

### Issue 2: Let's Encrypt Certificate Not Issuing

**Problem:** Certificate stuck in "Pending" state

**Solution:**
1. Check cert-manager logs:
   ```bash
   kubectl logs -n cert-manager deployment/cert-manager -f
   ```

2. Verify ACME challenge:
   ```bash
   kubectl get challenges -n arcana-cloud
   kubectl describe challenge <challenge-name> -n arcana-cloud
   ```

3. Ensure domain points to your cluster:
   ```bash
   nslookup api.arcana-cloud.com
   ```

4. Test ACME challenge endpoint:
   ```bash
   curl http://api.arcana-cloud.com/.well-known/acme-challenge/test
   ```

### Issue 3: Nginx Fails to Start with SSL

**Problem:** Nginx container crashes or shows SSL errors

**Solution:**
1. Verify certificate files exist:
   ```bash
   ls -la nginx/ssl/
   ```

2. Check certificate and key format:
   ```bash
   openssl x509 -in nginx/ssl/cert.pem -noout -text
   openssl rsa -in nginx/ssl/key.pem -check
   ```

3. Verify file permissions:
   ```bash
   chmod 644 nginx/ssl/cert.pem
   chmod 600 nginx/ssl/key.pem
   ```

4. Check Nginx configuration syntax:
   ```bash
   docker run --rm -v $(pwd)/nginx:/etc/nginx/conf.d nginx:1.25-alpine nginx -t
   ```

### Issue 4: SSL Handshake Failure

**Problem:** `SSL_ERROR_RX_RECORD_TOO_LONG` or handshake errors

**Solution:**
1. Verify SSL protocols and ciphers:
   ```bash
   openssl s_client -connect localhost:443 -tls1_2
   openssl s_client -connect localhost:443 -tls1_3
   ```

2. Check Nginx SSL configuration:
   ```bash
   docker exec arcana-nginx-ssl cat /etc/nginx/conf.d/default.conf | grep ssl_
   ```

3. Test with different TLS versions:
   ```bash
   curl --tlsv1.2 -k https://localhost/health
   curl --tlsv1.3 -k https://localhost/health
   ```

### Issue 5: Certificate Expired

**Problem:** Browser shows "NET::ERR_CERT_DATE_INVALID"

**Solution:**
1. Check certificate expiration:
   ```bash
   openssl x509 -in nginx/ssl/cert.pem -noout -dates
   ```

2. Regenerate self-signed certificate:
   ```bash
   ./scripts/generate-ssl-certs.sh --days 365
   ```

3. For Let's Encrypt, cert-manager auto-renews at 30 days before expiry. Check:
   ```bash
   kubectl describe certificate arcana-cloud-tls-prod -n arcana-cloud
   ```

### Issue 6: Mixed Content Warnings

**Problem:** Browser console shows mixed content warnings

**Solution:**
1. Ensure all resources use HTTPS
2. Verify `X-Forwarded-Proto` header is set:
   ```bash
   curl -H "X-Forwarded-Proto: https" http://localhost/api/v1/health
   ```

3. Add CSP header to allow HTTPS only:
   ```nginx
   add_header Content-Security-Policy "default-src 'self' https:;" always;
   ```

### Issue 7: HSTS Issues

**Problem:** Cannot access HTTP after enabling HSTS

**Solution:**
1. Clear HSTS cache in browser:
   - Chrome: `chrome://net-internals/#hsts` → Delete domain
   - Firefox: Clear history → Clear Active Logins

2. Reduce HSTS max-age during testing:
   ```nginx
   add_header Strict-Transport-Security "max-age=300" always;  # 5 minutes
   ```

### Issue 8: Rate Limiting Blocking Requests

**Problem:** Getting 429 or 503 errors from Nginx

**Solution:**
1. Check Nginx error logs:
   ```bash
   docker logs arcana-nginx-ssl 2>&1 | grep limit
   ```

2. Adjust rate limits in `nginx/nginx-uwsgi-ssl.conf`:
   ```nginx
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/s;  # Increase from 100
   ```

3. Increase burst size:
   ```nginx
   limit_req zone=api_limit burst=50 nodelay;  # Increase from 20
   ```

---

## SSL Configuration Reference

### Recommended SSL Settings

**Strong Security (Modern Clients Only):**
```nginx
ssl_protocols TLSv1.3;
ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
ssl_prefer_server_ciphers off;
```

**Balanced Security (Recommended):**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
```

**Maximum Compatibility:**
```nginx
ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
ssl_ciphers 'HIGH:!aNULL:!MD5';
ssl_prefer_server_ciphers on;
```

### Testing SSL Configuration

```bash
# Test with SSL Labs (production only)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.arcana-cloud.com

# Test with testssl.sh
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh https://localhost:443

# Test specific protocols
nmap --script ssl-enum-ciphers -p 443 localhost
```

---

## Additional Resources

- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Cert-Manager Documentation](https://cert-manager.io/docs/)
- [Nginx SSL Module](http://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)
