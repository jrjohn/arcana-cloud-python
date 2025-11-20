# Docker SSL Deployment Testing Guide

This guide provides comprehensive instructions for testing and verifying the Docker Compose SSL deployment with Nginx reverse proxy and uWSGI.

## Table of Contents
- [Quick Verification](#quick-verification)
- [Comprehensive Testing](#comprehensive-testing)
- [Manual Testing Steps](#manual-testing-steps)
- [Expected Results](#expected-results)
- [Troubleshooting](#troubleshooting)

---

## Quick Verification

For a quick verification of the SSL deployment:

```bash
# Run the quick verification script
./scripts/verify-docker-ssl.sh
```

This script will:
1. Generate SSL certificates (if needed)
2. Build uWSGI Docker images
3. Start all services with Docker Compose
4. Verify SSL/TLS configuration
5. Test HTTPS endpoints
6. Check security headers

**Expected Output:**
```
========================================
Docker SSL Deployment Quick Verification
========================================

Step 1: Generating SSL Certificates...
✓ SSL certificates already exist

Step 2: Building uWSGI Images...
✓ Images built successfully

Step 3: Starting Docker Compose Services...
✓ Services started

Step 4: Waiting for services to be ready (30s)...
✓ Wait complete

Step 5: Verifying Services...

→ Checking container status...
NAME                         STATUS
arcana-nginx-ssl            Up
arcana-controller-uwsgi     Up (healthy)
arcana-service-uwsgi        Up (healthy)
arcana-repository-uwsgi     Up (healthy)
arcana-mysql                Up (healthy)
arcana-redis                Up (healthy)

→ Testing HTTPS health endpoint...
{"status":"healthy","timestamp":"2025-11-20T10:00:00Z"}

→ Testing HTTPS API endpoint...
{"status":"ok","version":"1.0.0"}

→ Checking SSL certificate...
subject=C = US, ST = California, L = San Francisco, O = Arcana Cloud, CN = localhost

→ Verifying HSTS header...
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload

→ Testing HTTP → HTTPS redirect...
HTTP response code: 301 (should be 301 or 302)

========================================
Verification Complete!
========================================
```

---

## Comprehensive Testing

For a comprehensive test suite with 12 test categories:

```bash
# Run the comprehensive test script
./scripts/test-docker-ssl.sh
```

This script tests:

### Test Categories

1. **Prerequisites**
   - Docker is running
   - docker-compose is installed
   - Compose file exists

2. **SSL Certificates**
   - SSL directory exists
   - Certificate files exist (cert.pem, key.pem)
   - Certificate is valid
   - Private key is valid
   - Certificate and key match

3. **Build Images**
   - uWSGI images build successfully
   - Controller, service, and repository images exist

4. **Start Services**
   - Previous containers cleaned up
   - Services start successfully

5. **Container Health**
   - All containers are running
   - No errors in recent logs

6. **Network Connectivity**
   - Nginx → Controller
   - Controller → Service
   - Service → Repository
   - Repository → MySQL
   - Services → Redis

7. **SSL/TLS Configuration**
   - HTTP redirects to HTTPS
   - HTTPS endpoints are accessible
   - TLSv1.2 is supported
   - TLSv1.3 is supported
   - HSTS header is present
   - Security headers are present

8. **Application Endpoints**
   - Health endpoint responds
   - API v1 health endpoint responds
   - Response content type is JSON

9. **uWSGI Stats**
   - Controller stats endpoint
   - Service stats endpoint
   - Repository stats endpoint

10. **Performance and Rate Limiting**
    - Response time is acceptable
    - Gzip compression is enabled
    - CORS headers are present

11. **Database Connectivity**
    - MySQL is accessible
    - Database exists
    - Redis is accessible

12. **Container Logs**
    - No critical errors in logs

**Expected Output:**
```
========================================
Test Summary
========================================
Total Tests: 45
Passed: 45
Failed: 0

========================================
All Tests Passed! ✓
========================================

SSL/TLS deployment is working correctly!
```

---

## Manual Testing Steps

If you prefer to test manually, follow these steps:

### Step 1: Generate SSL Certificates

```bash
# Generate self-signed certificates
./scripts/generate-ssl-certs.sh

# Verify certificate was created
ls -la nginx/ssl/
# Should show: cert.pem, key.pem, csr.pem

# Check certificate details
openssl x509 -in nginx/ssl/cert.pem -noout -text
```

### Step 2: Build uWSGI Images

```bash
# Build all uWSGI images
./scripts/build-uwsgi-images.sh

# Verify images were created
docker images | grep uwsgi
# Should show:
# arcanacloud/arcana-cloud-controller-uwsgi
# arcanacloud/arcana-cloud-service-uwsgi
# arcanacloud/arcana-cloud-repository-uwsgi
```

### Step 3: Start Docker Compose Services

```bash
# Start all services
docker-compose -f docker-compose-nginx-ssl.yml up -d

# Check service status
docker-compose -f docker-compose-nginx-ssl.yml ps

# Wait for services to be healthy
sleep 30
```

### Step 4: Verify Container Health

```bash
# Check all containers are running
docker-compose -f docker-compose-nginx-ssl.yml ps

# Check logs for errors
docker-compose -f docker-compose-nginx-ssl.yml logs --tail=50

# Check specific container
docker-compose -f docker-compose-nginx-ssl.yml logs nginx-proxy
```

### Step 5: Test SSL/TLS Configuration

```bash
# Test HTTPS endpoint (skip certificate verification)
curl -k https://localhost/health

# Check SSL certificate
echo | openssl s_client -connect localhost:443 -servername localhost

# Test TLSv1.2
curl --tlsv1.2 -k https://localhost/health

# Test TLSv1.3
curl --tlsv1.3 -k https://localhost/health

# Verify HSTS header
curl -k -I https://localhost/health | grep -i "Strict-Transport-Security"
```

### Step 6: Test Security Headers

```bash
# Check all security headers
curl -k -I https://localhost/health

# Should include:
# Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
# X-Frame-Options: SAMEORIGIN
# X-Content-Type-Options: nosniff
# Content-Security-Policy: default-src 'self'
```

### Step 7: Test HTTP to HTTPS Redirect

```bash
# Test HTTP redirect
curl -I http://localhost/health

# Should return 301 or 302 with Location: https://...
```

### Step 8: Test Application Endpoints

```bash
# Test health endpoint
curl -k https://localhost/health

# Test API v1 endpoint
curl -k https://localhost/api/v1/health

# Test with verbose output
curl -kv https://localhost/api/v1/health
```

### Step 9: Test uWSGI Stats

```bash
# Access controller stats
docker-compose -f docker-compose-nginx-ssl.yml exec controller-layer curl -s http://localhost:9191

# Access service stats
docker-compose -f docker-compose-nginx-ssl.yml exec service-layer curl -s http://localhost:9191

# Access repository stats
docker-compose -f docker-compose-nginx-ssl.yml exec repository-layer curl -s http://localhost:9191
```

### Step 10: Test Database Connectivity

```bash
# Test MySQL
docker-compose -f docker-compose-nginx-ssl.yml exec mysql-db mysqladmin ping -h localhost -u root -proot_password

# Test Redis
docker-compose -f docker-compose-nginx-ssl.yml exec redis-cache redis-cli ping
```

### Step 11: Test Network Connectivity

```bash
# Test Nginx → Controller
docker-compose -f docker-compose-nginx-ssl.yml exec nginx-proxy wget -q -O- http://controller-layer:5000/health

# Test Controller → Service
docker-compose -f docker-compose-nginx-ssl.yml exec controller-layer wget -q -O- http://service-layer:5001/health

# Test Service → Repository
docker-compose -f docker-compose-nginx-ssl.yml exec service-layer wget -q -O- http://repository-layer:5002/health
```

### Step 12: Performance Testing

```bash
# Measure response time
curl -k -s -o /dev/null -w "%{time_total}\n" https://localhost/health

# Test with multiple requests
for i in {1..10}; do curl -k -s -o /dev/null -w "%{time_total}\n" https://localhost/health; done

# Test gzip compression
curl -k -I -H "Accept-Encoding: gzip" https://localhost/api/v1/health
```

---

## Expected Results

### Container Status
All containers should be in "Up" state with "(healthy)" status:
```
NAME                         STATUS
arcana-nginx-ssl            Up
arcana-controller-uwsgi     Up (healthy)
arcana-service-uwsgi        Up (healthy)
arcana-repository-uwsgi     Up (healthy)
arcana-mysql                Up (healthy)
arcana-redis                Up (healthy)
```

### SSL Certificate
Certificate should be valid and match the private key:
```
subject=C = US, ST = California, L = San Francisco, O = Arcana Cloud, CN = localhost
issuer=C = US, ST = California, L = San Francisco, O = Arcana Cloud, CN = localhost
Validity
    Not Before: Nov 20 10:00:00 2025 GMT
    Not After : Nov 20 10:00:00 2026 GMT
```

### Security Headers
All security headers should be present:
```
HTTP/1.1 200 OK
Server: nginx/1.25.3
Date: Wed, 20 Nov 2025 10:00:00 GMT
Content-Type: application/json
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
```

### Health Endpoint Response
```json
{
  "status": "healthy",
  "timestamp": "2025-11-20T10:00:00Z"
}
```

### uWSGI Stats Response
```json
{
  "version": "2.0.31",
  "listen_queue": 0,
  "load": 0,
  "workers": [
    {
      "id": 1,
      "pid": 7,
      "accepting": 1,
      "requests": 27,
      "status": "idle",
      "rss": 98607104,
      "avg_rt": 881
    }
  ]
}
```

### Performance
- Response time: < 2 seconds
- HTTP → HTTPS redirect: 301/302
- TLSv1.2 and TLSv1.3 supported
- Gzip compression enabled

---

## Troubleshooting

### Issue 1: Containers Not Starting

**Symptom:** Containers exit immediately or fail to start

**Check:**
```bash
# Check logs
docker-compose -f docker-compose-nginx-ssl.yml logs

# Check specific container
docker-compose -f docker-compose-nginx-ssl.yml logs nginx-proxy
docker-compose -f docker-compose-nginx-ssl.yml logs controller-layer
```

**Common Causes:**
- SSL certificates missing → Run `./scripts/generate-ssl-certs.sh`
- Images not built → Run `./scripts/build-uwsgi-images.sh`
- Port already in use → Check with `lsof -i :80` and `lsof -i :443`

### Issue 2: SSL Certificate Errors

**Symptom:** Browser shows "Your connection is not private"

**Solution:**
```bash
# For development testing, use -k flag
curl -k https://localhost/health

# Or add certificate to system trust store (macOS)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain nginx/ssl/cert.pem
```

### Issue 3: 502 Bad Gateway

**Symptom:** Nginx returns 502 error

**Check:**
```bash
# Check backend services are running
docker-compose -f docker-compose-nginx-ssl.yml ps

# Check network connectivity
docker-compose -f docker-compose-nginx-ssl.yml exec nginx-proxy ping controller-layer

# Check backend logs
docker-compose -f docker-compose-nginx-ssl.yml logs controller-layer
```

### Issue 4: Health Checks Failing

**Symptom:** Containers show "unhealthy" status

**Check:**
```bash
# Check health endpoint directly
docker-compose -f docker-compose-nginx-ssl.yml exec controller-layer curl -f http://localhost:5000/health

# Inspect container health
docker inspect arcana-controller-uwsgi | grep -A 10 Health
```

### Issue 5: Database Connection Errors

**Symptom:** Application logs show database connection errors

**Check:**
```bash
# Check MySQL is running
docker-compose -f docker-compose-nginx-ssl.yml exec mysql-db mysqladmin ping -h localhost -u root -proot_password

# Check database exists
docker-compose -f docker-compose-nginx-ssl.yml exec mysql-db mysql -u root -proot_password -e "SHOW DATABASES;"

# Check Redis is running
docker-compose -f docker-compose-nginx-ssl.yml exec redis-cache redis-cli ping
```

### Issue 6: Slow Performance

**Symptom:** Response times > 2 seconds

**Check:**
```bash
# Check container resources
docker stats

# Check uWSGI stats
docker-compose -f docker-compose-nginx-ssl.yml exec controller-layer curl -s http://localhost:9191

# Increase uWSGI workers if needed
# Edit docker-compose-nginx-ssl.yml:
#   environment:
#     - UWSGI_PROCESSES=8  # Increase from 4
```

### Issue 7: Port Conflicts

**Symptom:** Port already in use error

**Check:**
```bash
# Check what's using ports 80 and 443
lsof -i :80
lsof -i :443

# Stop conflicting services
# macOS: sudo apachectl stop
# Linux: sudo systemctl stop apache2 / nginx
```

---

## Cleanup

After testing, you can stop and remove all containers:

```bash
# Stop services
docker-compose -f docker-compose-nginx-ssl.yml down

# Stop and remove volumes (database data will be lost)
docker-compose -f docker-compose-nginx-ssl.yml down -v

# Remove images
docker rmi arcanacloud/arcana-cloud-controller-uwsgi:latest
docker rmi arcanacloud/arcana-cloud-service-uwsgi:latest
docker rmi arcanacloud/arcana-cloud-repository-uwsgi:latest
```

---

## Additional Resources

- [SSL Setup Guide](SSL_SETUP.md) - Comprehensive SSL/TLS configuration
- [README.md](../README.md) - Project overview and quick start
- [Docker Compose File](../docker-compose-nginx-ssl.yml) - Service configuration
- [Nginx SSL Config](../nginx/nginx-uwsgi-ssl.conf) - Nginx reverse proxy configuration

---

**Last Updated:** 2025-11-20
