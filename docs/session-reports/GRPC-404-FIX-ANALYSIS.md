# gRPC 404 User ID Issue - Root Cause Analysis & Fix

## Executive Summary

**Issue**: 28 tests failing with 404 errors on `/api/v1/users/{id}` endpoints in K8s + gRPC mode.

**Root Cause**: Fixture user corruption due to test execution order and database state. NOT a gRPC routing issue.

**Status**: ✅ ROOT CAUSE IDENTIFIED - Ready for validation

---

## Investigation Results

### 1. gRPC Infrastructure Verification ✅

**All components exist and function correctly:**

- ✅ Service layer routes: `/internal/users/<int:user_id>` ([app/services/routes/user_service_routes.py:90-124](app/services/routes/user_service_routes.py#L90-L124))
- ✅ Controller registration: user_bp registered in microservices mode ([app/__init__.py:77-82](app/__init__.py#L77-L82))
- ✅ gRPC client: `get_user_by_id` method ([app/communication/implementations/grpc_impl.py:178-187](app/communication/implementations/grpc_impl.py#L178-L187))
- ✅ gRPC server: `GetUserById` RPC ([app/grpc_protos/servers/user_service_server.py:105-119](app/grpc_protos/servers/user_service_server.py#L105-L119))

**Manual Testing Confirms Everything Works:**
```bash
# Login works, returns user ID=44
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "testuser", "password": "TestPass123"}'
# Response: {..."user": {"id": 44, "email": "test@example.com"}...}

# /api/v1/auth/me works
curl -X GET http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Response: {..."data": {"id": 44, "email": "test@example.com"}...}

# /api/v1/users/{id} works
curl -X GET http://localhost:8080/api/v1/users/44 \
  -H "Authorization: Bearer $TOKEN"
# Response: {..."data": {"id": 44, "username": "testuser"}...}
```

---

## 2. Root Cause: Fixture User Corruption

### The Problem Flow:

1. **Benchmark starts** → `clean_database()` deletes ALL users
2. **Fixture population** → Creates testuser with `test@example.com` (ID varies)
3. **Tests execute** → Some tests create users with conflicting usernames
4. **Fixture user corruption** → Original fixture testuser gets replaced or deleted
5. **Subsequent tests fail** → Tests expect fixture user but find corrupted/wrong user
6. **404 errors occur** → Tests use wrong user IDs or None

### Evidence:

**Before manual fix:**
```sql
mysql> SELECT id, username, email FROM users WHERE username='testuser';
+----+----------+----------------------+
| id | username | email                |
+----+----------+----------------------+
| 42 | testuser | different@example.com|  # WRONG EMAIL!
+----+----------+----------------------+
```

**Culprit Test:**
[tests/integration/test_api/test_auth_api.py:40-58](tests/integration/test_api/test_auth_api.py#L40-L58)
```python
def test_register_duplicate_username(self, client, db, sample_user):
    """Test registering with duplicate username"""
    payload = {
        'username': 'testuser',  # Same as fixture!
        'email': 'different@example.com',  # Different email!
        'password': 'NewPass123'
    }
    response = client.post('/api/v1/auth/register', ...)
    assert response.status_code == 409  # Should fail, but may succeed
```

This test is SUPPOSED to get 409 (conflict), but if the fixture testuser was already deleted by cleanup, the registration succeeds and creates a NEW testuser with the wrong email.

**After manual fixture population:**
```sql
mysql> SELECT id, username, email FROM users WHERE username='testuser';
+----+----------+------------------+
| id | username | email            |
+----+----------+------------------+
| 44 | testuser | test@example.com |  # CORRECT!
+----+----------+------------------+
```

**Validation test passed:**
```bash
$ venv/bin/python3 test_fixture_debug.py
✓ Successfully got user ID: 44
Step 3: Test GET /api/v1/users/44...
Get user status: 200  # SUCCESS!
```

---

## 3. Why This Happens

### Database State Lifecycle:

1. **Benchmark script calls:**
   ```bash
   clean_database      # Deletes ALL users (including fixtures)
   populate_fixtures   # Creates testuser + admin
   run_tests           # Tests execute
   ```

2. **Test execution issues:**
   - Tests run in parallel or unpredictable order
   - Some tests expect fixture users to exist
   - Other tests try to create users with same usernames
   - Database cleanup happens at wrong times
   - Fixture users get deleted/corrupted mid-test-run

3. **Conftest fixture behavior:**
   - In microservices mode, per-test cleanup is skipped ([tests/conftest.py:65-66](tests/conftest.py#L65-L66))
   - Fixtures fetch user IDs via `/api/v1/auth/me` ([tests/conftest.py:83-113](tests/conftest.py#L83-L113))
   - If fixture user doesn't exist or has wrong email, ID fetching fails
   - Fallback returns MockUser with `id=None` → causes 404 errors

---

## 4. The Fix

### ✅ Immediate Solution (Applied):

Manually populated correct fixtures:
```bash
venv/bin/python3 scripts/populate-test-fixtures.py --namespace arcana-cloud
```

Result:
```
✓ Test fixtures populated successfully!
username	email	role	status
admin	admin@example.com	ADMIN	ACTIVE
testuser	test@example.com	USER	ACTIVE
```

### 🔧 Long-term Solutions:

#### Option A: Protected Fixture Users (RECOMMENDED)
Modify `clean_database()` to preserve fixture users:
```bash
# In scripts/benchmark-k8s-protocols.sh
clean_database() {
    echo "Cleaning test database (preserving fixture users)..."
    kubectl exec -n "$NAMESPACE" mysql-0 -- mysql -u arcana -parcana_pass arcana_cloud -e "
        SET FOREIGN_KEY_CHECKS=0;
        DELETE FROM oauth_tokens WHERE user_id NOT IN (
            SELECT id FROM users WHERE username IN ('testuser', 'admin')
        );
        DELETE FROM users WHERE username NOT IN ('testuser', 'admin');
        SET FOREIGN_KEY_CHECKS=1;
    " 2>&1 | grep -v "Warning: Using a password"
}
```

#### Option B: Unique Test Usernames
Modify tests to use unique usernames instead of colliding with fixtures:
```python
# Instead of:
payload = {'username': 'testuser', 'email': 'different@example.com'}

# Use:
payload = {'username': f'test_duplicate_{uuid.uuid4().hex[:8]}', 'email': 'different@example.com'}
```

#### Option C: Repopulate Before Each Test Run
Ensure fixtures are fresh before EVERY test execution:
```bash
# In benchmark script, before run_benchmark():
clean_database
populate_fixtures  # Ensure fresh fixtures
run_pytest_tests
```

---

## 5. Expected Impact

**With correct fixtures in place:**
- ✅ `/api/v1/auth/me` endpoint works → Fixtures can fetch correct user IDs
- ✅ `/api/v1/users/{id}` endpoints work → Tests use correct IDs (44, 45)
- ✅ Auth tests work → Login/logout use correct fixture credentials
- ✅ User CRUD tests work → Operations on correct user IDs

**Estimated improvement:**
- **+28 tests** should pass (all gRPC 404 user ID failures)
- **Current**: 60/93 passing (64.5%)
- **Expected**: 88/93 passing (94.6%)

---

## 6. Validation Plan

1. ✅ **Manual fixture population** - DONE
2. ✅ **Manual endpoint testing** - DONE (all endpoints work)
3. ⏳ **Run full benchmark** - PENDING
4. ⏳ **Verify pass rate improvement** - PENDING

### Commands to Run:

```bash
# Full benchmark (tests both gRPC and HTTP)
./scripts/benchmark-k8s-protocols.sh

# Or test gRPC only
DEPLOYMENT_MODE=microservices COMMUNICATION_PROTOCOL=grpc \
SERVICE_URL=http://localhost:8080 \
REPOSITORY_URL=http://localhost:8080 \
CONTROLLER_URL=http://localhost:8080 \
DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud" \
TEST_DATABASE_URL="mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud" \
venv/bin/python -m pytest tests/integration/ -v
```

---

## 7. Files Analyzed

- [scripts/benchmark-k8s-protocols.sh](scripts/benchmark-k8s-protocols.sh) - Benchmark orchestration
- [scripts/populate-test-fixtures.py](scripts/populate-test-fixtures.py) - Fixture population
- [tests/conftest.py](tests/conftest.py) - Pytest fixtures (sample_user, admin_user)
- [tests/http_client.py](tests/http_client.py) - HTTPTestClient for microservices mode
- [tests/integration/test_api/test_auth_api.py](tests/integration/test_api/test_auth_api.py) - Auth tests (includes duplicate username test)
- [app/controllers/auth_controller.py](app/controllers/auth_controller.py) - `/api/v1/auth/me` endpoint
- [app/decorators/auth_decorators.py](app/decorators/auth_decorators.py) - `@token_required` decorator
- [app/services/routes/user_service_routes.py](app/services/routes/user_service_routes.py) - Service layer routes
- [app/communication/implementations/grpc_impl.py](app/communication/implementations/grpc_impl.py) - gRPC client
- [app/grpc_protos/servers/user_service_server.py](app/grpc_protos/servers/user_service_server.py) - gRPC server

---

## 8. Key Learnings

1. **gRPC infrastructure was never the issue** - All components work correctly
2. **Test isolation is critical** - Fixture users must be protected from test modifications
3. **Database state matters** - Tests assume fixtures exist in specific state
4. **Failure cascades** - One corrupted fixture causes many downstream 404 errors
5. **Silent failures are dangerous** - Initial grep filtering hid fixture population errors

---

**Next Action**: Run benchmark to validate that correct fixtures eliminate 404 errors.
