# Plan to Achieve 100% K8s + gRPC Pass Rate

## Current Status (Auth API Tests)
- **Passing**: 17/27 tests (63%)
- **Failing**: 10/27 tests (37%)

## Failure Analysis

### 1. Rate Limiting Issues (5 failures) - HIGHEST PRIORITY
**Tests affected:**
- `test_login_success` - 429
- `test_login_invalid_password` - 429
- `test_login_with_email` - 429
- `test_sql_injection_in_login` - 429
- `test_case_sensitivity_in_login` - 429

**Root Cause:** Rate limiting is still enabled in K8s pods despite config fix.

**Fix Applied:**
- ✅ [app/config.py](app/config.py#L103) - Added `RATELIMIT_ENABLED = False` to TestingConfig
- ✅ [app/__init__.py](app/__init__.py#L64-L68) - Conditional limiter initialization

**Action Required:**
1. ✅ Rebuild Docker images with updated code
2. ⏳ Deploy to K8s cluster
3. ⏳ Restart deployments

**Expected Impact:** +5 tests passing → 22/27 (81.5%)

---

### 2. Test Isolation / Duplicate Users (3 failures)
**Tests affected:**
- `test_register_success` - 409 (user already exists)
- `test_unicode_in_credentials` - 409
- `test_null_byte_in_password` - 409

**Root Cause:** Fixture users exist, but tests try to register with same usernames.

**Fix Applied:**
- ✅ [scripts/benchmark-k8s-protocols.sh](scripts/benchmark-k8s-protocols.sh#L37-L52) - Protected fixture users during cleanup
- ✅ [scripts/populate-test-fixtures.py](scripts/populate-test-fixtures.py) - Properly deletes and recreates fixtures

**Additional Fix Needed:**
Tests that create new users with predictable usernames need unique names:

```python
# Option A: Use UUID for unique usernames
import uuid
username = f"testuser_{uuid.uuid4().hex[:8]}"

# Option B: Use timestamp
import time
username = f"testuser_{int(time.time())}"
```

**Expected Impact:** +3 tests passing → 25/27 (92.6%)

---

### 3. Auth Token Issues (2 failures)
**Tests affected:**
- `test_logout_success` - 401 (Unauthorized)
- `test_refresh_token_success` - 401 (Unauthorized)

**Root Cause:** Token fixtures may not be getting proper tokens, or auth flow differs in gRPC mode.

**Investigation Required:**
- Check if `sample_token` fixture works correctly in microservices mode
- Verify `/api/v1/auth/logout` and `/api/v1/auth/refresh` endpoints exist and work
- Compare gRPC vs HTTP auth flow

**Expected Impact:** +2 tests passing → 27/27 (100%)

---

## Deployment Steps

### Step 1: Deploy Rate Limiting Fix ✅ IN PROGRESS

```bash
# 1. Build new images
cd deployment/kubernetes
export DOCKER_BUILDKIT=0
bash build-images.sh

# 2. Deploy to K8s
kubectl set image deployment/controller-layer controller-layer=arcanacloud/arcana-cloud-controller:latest -n arcana-cloud
kubectl set image deployment/service-layer service-layer=arcanacloud/arcana-cloud-service:latest -n arcana-cloud
kubectl set image deployment/repository-layer repository-layer=arcanacloud/arcana-cloud-repository:latest -n arcana-cloud

# 3. Wait for rollout
kubectl rollout status deployment/controller-layer -n arcana-cloud
kubectl rollout status deployment/service-layer -n arcana-cloud
kubectl rollout status deployment/repository-layer -n arcana-cloud

# 4. Verify rate limiting is disabled
kubectl logs -n arcana-cloud deployment/controller-layer | grep -i "rate"
```

### Step 2: Fix Test Isolation

**Modify tests to use unique usernames:**

Files to update:
- [tests/integration/test_api/test_auth_api.py](tests/integration/test_api/test_auth_api.py)
- [tests/integration/test_workflows/test_complete_user_flow.py](tests/integration/test_workflows/test_complete_user_flow.py)

```python
# Add helper function at top of test file
import uuid

def generate_unique_username(base="testuser"):
    """Generate unique username for test isolation"""
    return f"{base}_{uuid.uuid4().hex[:8]}"

# Use in tests:
def test_register_success(self, client, db):
    payload = {
        'username': generate_unique_username(),  # Instead of hardcoded 'newuser'
        'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
        'password': 'NewPass123'
    }
```

### Step 3: Fix Auth Token Issues

**Investigate and fix:**
1. Check if logout endpoint exists in controller
2. Check if refresh endpoint exists in controller
3. Verify token fixtures provide valid tokens
4. Check error code mappings in gRPC vs HTTP

---

## Validation

After each step, run targeted tests:

```bash
# Test rate limiting fix
DEPLOYMENT_MODE=microservices COMMUNICATION_PROTOCOL=grpc \
SERVICE_URL=http://localhost:8080 \
REPOSITORY_URL=http://localhost:8080 \
CONTROLLER_URL=http://localhost:8080 \
DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud" \
TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud" \
venv/bin/python -m pytest tests/integration/test_api/test_auth_api.py::TestAuthAPI::test_login_success -v

# Test full auth API
venv/bin/python -m pytest tests/integration/test_api/test_auth_api.py -v

# Full benchmark
./scripts/benchmark-k8s-protocols.sh
```

---

## Timeline

1. **Rate Limiting Fix (20 min)**
   - ✅ Build images (10 min)
   - ⏳ Deploy to K8s (5 min)
   - ⏳ Validate (5 min)

2. **Test Isolation Fix (15 min)**
   - ⏳ Modify test files (10 min)
   - ⏳ Validate (5 min)

3. **Auth Token Fix (30 min)**
   - ⏳ Investigate (15 min)
   - ⏳ Fix (10 min)
   - ⏳ Validate (5 min)

**Total Estimated Time:** ~65 minutes

---

## Success Criteria

- ✅ All K8s + gRPC integration tests passing (93/93 = 100%)
- ✅ All K8s + HTTP integration tests passing (93/93 = 100%)
- ✅ Benchmark comparison report shows stable results
- ✅ No test flakiness or intermittent failures

---

## Files Modified

1. ✅ [app/config.py](app/config.py) - Rate limiting config
2. ✅ [app/__init__.py](app/__init__.py) - Conditional limiter init
3. ✅ [scripts/benchmark-k8s-protocols.sh](scripts/benchmark-k8s-protocols.sh) - Protected fixtures
4. ✅ [scripts/populate-test-fixtures.py](scripts/populate-test-fixtures.py) - Fixture population
5. ✅ [GRPC-404-FIX-ANALYSIS.md](GRPC-404-FIX-ANALYSIS.md) - Root cause analysis
6. ⏳ tests/integration/test_api/test_auth_api.py - Unique usernames (pending)
7. ⏳ tests/integration/test_workflows/test_complete_user_flow.py - Unique usernames (pending)

---

**Next Action:** Complete Docker image build, deploy to K8s, and validate rate limiting fix.
