#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for Monolithic Mode
Generates detailed HTML test reports
"""
import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Test configuration
BASE_URL = "http://localhost:5555"
TIMEOUT = 10


class TestStatus(Enum):
    """Test result status"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    SKIP = "⏭️  SKIP"
    ERROR = "⚠️  ERROR"


@dataclass
class TestResult:
    """Individual test result"""
    name: str
    endpoint: str
    method: str
    status: TestStatus
    duration_ms: float
    status_code: int = None
    expected_code: int = None
    response_data: Dict = None
    error_message: str = None


@dataclass
class TestSuite:
    """Test suite results"""
    name: str
    tests: List[TestResult]
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_ms: float = 0


class APITester:
    """API Testing Framework"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.admin_token = None
        self.test_user_id = None
        self.results: List[TestSuite] = []

    def test_request(self,
                     name: str,
                     method: str,
                     endpoint: str,
                     expected_status: int,
                     headers: Dict = None,
                     json_data: Dict = None,
                     params: Dict = None) -> TestResult:
        """Execute a single test request"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=TIMEOUT
            )
            duration_ms = (time.time() - start_time) * 1000

            # Determine test status
            status = TestStatus.PASS if response.status_code == expected_status else TestStatus.FAIL

            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw": response.text[:200]}

            return TestResult(
                name=name,
                endpoint=endpoint,
                method=method,
                status=status,
                duration_ms=duration_ms,
                status_code=response.status_code,
                expected_code=expected_status,
                response_data=response_data
            )

        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                endpoint=endpoint,
                method=method,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                error_message="Request timeout"
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                endpoint=endpoint,
                method=method,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )

    def run_health_checks(self) -> TestSuite:
        """Test health check endpoints"""
        print("\n" + "="*60)
        print("📊 Running Health Check Tests")
        print("="*60)

        tests = []

        # Test 1: Health endpoint
        print("\n1️⃣  Testing /health...")
        result = self.test_request(
            name="Health Check",
            method="GET",
            endpoint="/health",
            expected_status=200
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        # Test 2: Readiness endpoint
        print("\n2️⃣  Testing /ready...")
        result = self.test_request(
            name="Readiness Check",
            method="GET",
            endpoint="/ready",
            expected_status=200
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        return self._create_suite("Health Checks", tests)

    def run_auth_tests(self) -> TestSuite:
        """Test authentication endpoints"""
        print("\n" + "="*60)
        print("🔐 Running Authentication Tests")
        print("="*60)

        tests = []

        # Use existing testuser1 instead of creating new one
        test_username = "testuser1"
        test_email = "testuser1@example.com"
        test_password = "Test123456"

        # Test 1: Login with existing user
        print("\n1️⃣  Testing user login...")
        login_data = {
            "username_or_email": test_username,
            "password": test_password
        }
        result = self.test_request(
            name="User Login",
            method="POST",
            endpoint="/api/v1/auth/login",
            expected_status=200,
            json_data=login_data
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        if result.status == TestStatus.PASS:
            self.access_token = result.response_data.get('data', {}).get('access_token')
            user_data = result.response_data.get('data', {}).get('user', {})
            self.test_user_id = user_data.get('id')
            print(f"   Access token obtained: {self.access_token[:20]}...")
            print(f"   User ID: {self.test_user_id}")

        # Test 2: Get current user profile (requires auth)
        print("\n2️⃣  Testing get current user profile...")
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        result = self.test_request(
            name="Get Current User Profile",
            method="GET",
            endpoint="/api/v1/auth/me",
            expected_status=200,
            headers=headers
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        # Test 3: Register new user
        timestamp = int(time.time())
        new_username = f"newuser_{timestamp}"
        new_email = f"{new_username}@example.com"
        print(f"\n3️⃣  Testing user registration ({new_username})...")
        register_data = {
            "username": new_username,
            "email": new_email,
            "password": "SecurePass123",
            "first_name": "New",
            "last_name": "User"
        }
        result = self.test_request(
            name="User Registration",
            method="POST",
            endpoint="/api/v1/auth/register",
            expected_status=201,
            json_data=register_data
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        # Test 4: Duplicate registration (should fail)
        print(f"\n4️⃣  Testing duplicate registration ({new_username})...")
        result = self.test_request(
            name="Duplicate Registration (Expected Fail)",
            method="POST",
            endpoint="/api/v1/auth/register",
            expected_status=409,
            json_data=register_data
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        # Test 5: Logout
        print("\n5️⃣  Testing user logout...")
        result = self.test_request(
            name="User Logout",
            method="POST",
            endpoint="/api/v1/auth/logout",
            expected_status=200,
            headers=headers
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        return self._create_suite("Authentication", tests)

    def login_as_admin(self) -> bool:
        """Login as admin and store admin token"""
        print("\n🔑 Logging in as admin for User Management tests...")
        admin_login_data = {
            "username_or_email": "admin",
            "password": "admin123"
        }

        result = self.test_request(
            name="Admin Login",
            method="POST",
            endpoint="/api/v1/auth/login",
            expected_status=200,
            json_data=admin_login_data
        )

        if result.status == TestStatus.PASS:
            self.admin_token = result.response_data.get('data', {}).get('access_token')
            print(f"   ✅ Admin token obtained: {self.admin_token[:20]}...")
            return True
        else:
            print(f"   ❌ Admin login failed: {result.error_message or result.response_data}")
            return False

    def run_user_tests(self) -> TestSuite:
        """Test user management endpoints"""
        print("\n" + "="*60)
        print("👥 Running User Management Tests")
        print("="*60)

        tests = []

        # Login as admin first to get admin token
        if not self.admin_token:
            self.login_as_admin()

        # Use admin token for User Management endpoints (they require ADMIN role)
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}

        # Test 1: Get all users (paginated)
        print("\n1️⃣  Testing get all users...")
        result = self.test_request(
            name="Get All Users (Paginated)",
            method="GET",
            endpoint="/api/v1/users",
            expected_status=200,
            params={"page": 1, "per_page": 10},
            headers=headers
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        # Test 2: Get specific user by ID
        if self.test_user_id:
            print(f"\n2️⃣  Testing get user by ID ({self.test_user_id})...")
            result = self.test_request(
                name="Get User By ID",
                method="GET",
                endpoint=f"/api/v1/users/{self.test_user_id}",
                expected_status=200,
                headers=headers
            )
            tests.append(result)
            print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")
        else:
            print("\n2️⃣  Skipping get user by ID (no user ID available)...")
            tests.append(TestResult(
                name="Get User By ID",
                endpoint="/api/v1/users/{id}",
                method="GET",
                status=TestStatus.SKIP,
                duration_ms=0,
                error_message="No user ID available"
            ))

        # Test 3: Update user
        if self.test_user_id:
            print(f"\n3️⃣  Testing update user ({self.test_user_id})...")
            update_data = {
                "first_name": "Updated",
                "last_name": "Name"
            }
            result = self.test_request(
                name="Update User",
                method="PUT",
                endpoint=f"/api/v1/users/{self.test_user_id}",
                expected_status=200,
                json_data=update_data,
                headers=headers
            )
            tests.append(result)
            print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")
        else:
            print("\n3️⃣  Skipping update user (no user ID available)...")
            tests.append(TestResult(
                name="Update User",
                endpoint="/api/v1/users/{id}",
                method="PUT",
                status=TestStatus.SKIP,
                duration_ms=0,
                error_message="No user ID available"
            ))

        # Test 4: Search users
        print("\n4️⃣  Testing search users...")
        result = self.test_request(
            name="Search Users",
            method="GET",
            endpoint="/api/v1/users",
            expected_status=200,
            params={"username": "test"},
            headers=headers
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        return self._create_suite("User Management", tests)

    def run_public_user_tests(self) -> TestSuite:
        """Test public user endpoints"""
        print("\n" + "="*60)
        print("🌐 Running Public User Tests")
        print("="*60)

        tests = []

        # Test 1: Get all public users
        print("\n1️⃣  Testing get all public users...")
        result = self.test_request(
            name="Get All Public Users",
            method="GET",
            endpoint="/api/public/users",
            expected_status=200,
            params={"page": 1}
        )
        tests.append(result)
        print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")

        # Test 2: Get specific public user
        if self.test_user_id:
            print(f"\n2️⃣  Testing get public user by ID ({self.test_user_id})...")
            result = self.test_request(
                name="Get Public User By ID",
                method="GET",
                endpoint=f"/api/public/users/{self.test_user_id}",
                expected_status=200
            )
            tests.append(result)
            print(f"   {result.status.value} ({result.duration_ms:.0f}ms)")
        else:
            print("\n2️⃣  Skipping get public user by ID (no user ID available)...")
            tests.append(TestResult(
                name="Get Public User By ID",
                endpoint="/api/public/users/{id}",
                method="GET",
                status=TestStatus.SKIP,
                duration_ms=0,
                error_message="No user ID available"
            ))

        return self._create_suite("Public User Endpoints", tests)

    def _create_suite(self, name: str, tests: List[TestResult]) -> TestSuite:
        """Create test suite from results"""
        total = len(tests)
        passed = sum(1 for t in tests if t.status == TestStatus.PASS)
        failed = sum(1 for t in tests if t.status == TestStatus.FAIL)
        errors = sum(1 for t in tests if t.status == TestStatus.ERROR)
        skipped = sum(1 for t in tests if t.status == TestStatus.SKIP)
        duration = sum(t.duration_ms for t in tests)

        return TestSuite(
            name=name,
            tests=tests,
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_ms=duration
        )

    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "🚀 " + "="*58)
        print("   ARCANA CLOUD - MONOLITHIC API TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run test suites
        self.results.append(self.run_health_checks())
        self.results.append(self.run_auth_tests())
        self.results.append(self.run_user_tests())
        self.results.append(self.run_public_user_tests())

        # Print summary
        self.print_summary()

        # Generate HTML report
        self.generate_html_report()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        total_tests = sum(s.total for s in self.results)
        total_passed = sum(s.passed for s in self.results)
        total_failed = sum(s.failed for s in self.results)
        total_errors = sum(s.errors for s in self.results)
        total_skipped = sum(s.skipped for s in self.results)
        total_duration = sum(s.duration_ms for s in self.results)

        for suite in self.results:
            print(f"\n{suite.name}:")
            print(f"  Total: {suite.total} | ✅ {suite.passed} | ❌ {suite.failed} | ⚠️ {suite.errors} | ⏭️ {suite.skipped}")
            print(f"  Duration: {suite.duration_ms:.0f}ms")

        print("\n" + "-"*60)
        print(f"OVERALL: {total_tests} tests")
        print(f"  ✅ Passed:  {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
        print(f"  ❌ Failed:  {total_failed}/{total_tests}")
        print(f"  ⚠️  Errors:  {total_errors}/{total_tests}")
        print(f"  ⏭️  Skipped: {total_skipped}/{total_tests}")
        print(f"  ⏱️  Duration: {total_duration:.0f}ms")
        print("="*60)

    def generate_html_report(self):
        """Generate HTML test report"""
        output_file = "docs/API_TEST_REPORT.html"

        html_content = self._generate_html()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ HTML Report generated: {output_file}")
        print(f"   Open in browser: file://{os.path.abspath(output_file)}")

    def _generate_html(self) -> str:
        """Generate HTML report content"""
        total_tests = sum(s.total for s in self.results)
        total_passed = sum(s.passed for s in self.results)
        total_failed = sum(s.failed for s in self.results)
        total_errors = sum(s.errors for s in self.results)
        total_skipped = sum(s.skipped for s in self.results)
        total_duration = sum(s.duration_ms for s in self.results)

        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arcana Cloud - API Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .metadata {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 1px solid #e9ecef;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}

        .metadata-label {{
            font-size: 0.85em;
            color: #6c757d;
            margin-bottom: 5px;
        }}

        .metadata-value {{
            font-size: 1.1em;
            font-weight: 600;
            color: #212529;
        }}

        .summary {{
            padding: 40px;
            background: white;
        }}

        .summary h2 {{
            color: #212529;
            margin-bottom: 30px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}

        .stat-card.passed {{
            border-left-color: #28a745;
            background: linear-gradient(135deg, #f8fff9 0%, #e8f5e9 100%);
        }}

        .stat-card.failed {{
            border-left-color: #dc3545;
            background: linear-gradient(135deg, #fff8f8 0%, #ffebee 100%);
        }}

        .stat-card.errors {{
            border-left-color: #ffc107;
            background: linear-gradient(135deg, #fffef8 0%, #fff9e6 100%);
        }}

        .stat-card.skipped {{
            border-left-color: #6c757d;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }}

        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 1s ease;
        }}

        .test-suites {{
            padding: 0 40px 40px;
        }}

        .suite {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            margin-bottom: 30px;
            overflow: hidden;
        }}

        .suite-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 25px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .suite-header:hover {{
            opacity: 0.95;
        }}

        .suite-title {{
            font-size: 1.4em;
            font-weight: 600;
        }}

        .suite-stats {{
            display: flex;
            gap: 20px;
            font-size: 0.95em;
        }}

        .suite-stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .suite-body {{
            padding: 25px;
            background: #f8f9fa;
        }}

        .test-item {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: box-shadow 0.2s;
        }}

        .test-item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .test-item.pass {{
            border-left: 4px solid #28a745;
        }}

        .test-item.fail {{
            border-left: 4px solid #dc3545;
        }}

        .test-item.error {{
            border-left: 4px solid #ffc107;
        }}

        .test-item.skip {{
            border-left: 4px solid #6c757d;
            opacity: 0.7;
        }}

        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .test-name {{
            font-weight: 600;
            font-size: 1.1em;
            color: #212529;
        }}

        .test-status {{
            font-size: 1.2em;
        }}

        .test-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }}

        .test-detail {{
            font-size: 0.9em;
        }}

        .test-detail-label {{
            color: #6c757d;
            margin-right: 5px;
        }}

        .test-detail-value {{
            font-family: 'Courier New', monospace;
            color: #212529;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge.method-get {{
            background: #0dcaf0;
            color: white;
        }}

        .badge.method-post {{
            background: #198754;
            color: white;
        }}

        .badge.method-put {{
            background: #fd7e14;
            color: white;
        }}

        .badge.method-delete {{
            background: #dc3545;
            color: white;
        }}

        .code-block {{
            background: #f1f3f5;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            overflow-x: auto;
            max-height: 300px;
        }}

        .error-message {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            padding: 12px;
            margin-top: 10px;
            color: #856404;
        }}

        .footer {{
            background: #212529;
            color: white;
            padding: 20px;
            text-align: center;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}

            .suite-stats {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Arcana Cloud API Test Report</h1>
            <div class="subtitle">Monolithic Deployment Mode - Comprehensive API Testing</div>
        </div>

        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Test Date</div>
                    <div class="metadata-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Base URL</div>
                    <div class="metadata-value">{self.base_url}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Total Duration</div>
                    <div class="metadata-value">{total_duration:.0f}ms</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Success Rate</div>
                    <div class="metadata-value">{success_rate:.1f}%</div>
                </div>
            </div>
        </div>

        <div class="summary">
            <h2>📊 Executive Summary</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_tests}</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat-card passed">
                    <div class="stat-number" style="color: #28a745;">✅ {total_passed}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-card failed">
                    <div class="stat-number" style="color: #dc3545;">❌ {total_failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card errors">
                    <div class="stat-number" style="color: #ffc107;">⚠️ {total_errors}</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat-card skipped">
                    <div class="stat-number" style="color: #6c757d;">⏭️ {total_skipped}</div>
                    <div class="stat-label">Skipped</div>
                </div>
            </div>

            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%;">
                    {success_rate:.1f}% Success Rate
                </div>
            </div>
        </div>

        <div class="test-suites">
"""

        # Add each test suite
        for suite in self.results:
            suite_success_rate = (suite.passed / suite.total * 100) if suite.total > 0 else 0

            html += f"""
            <div class="suite">
                <div class="suite-header">
                    <div class="suite-title">{suite.name}</div>
                    <div class="suite-stats">
                        <div class="suite-stat">✅ {suite.passed}</div>
                        <div class="suite-stat">❌ {suite.failed}</div>
                        <div class="suite-stat">⚠️ {suite.errors}</div>
                        <div class="suite-stat">⏭️ {suite.skipped}</div>
                        <div class="suite-stat">⏱️ {suite.duration_ms:.0f}ms</div>
                    </div>
                </div>
                <div class="suite-body">
"""

            # Add each test result
            for test in suite.tests:
                status_class = {
                    TestStatus.PASS: "pass",
                    TestStatus.FAIL: "fail",
                    TestStatus.ERROR: "error",
                    TestStatus.SKIP: "skip"
                }.get(test.status, "")

                method_class = f"method-{test.method.lower()}"

                html += f"""
                    <div class="test-item {status_class}">
                        <div class="test-header">
                            <div class="test-name">{test.name}</div>
                            <div class="test-status">{test.status.value}</div>
                        </div>
                        <div class="test-details">
                            <div class="test-detail">
                                <span class="test-detail-label">Method:</span>
                                <span class="badge {method_class}">{test.method}</span>
                            </div>
                            <div class="test-detail">
                                <span class="test-detail-label">Endpoint:</span>
                                <span class="test-detail-value">{test.endpoint}</span>
                            </div>
                            <div class="test-detail">
                                <span class="test-detail-label">Duration:</span>
                                <span class="test-detail-value">{test.duration_ms:.0f}ms</span>
                            </div>
"""

                if test.status_code is not None:
                    status_color = "#28a745" if test.status == TestStatus.PASS else "#dc3545"
                    html += f"""
                            <div class="test-detail">
                                <span class="test-detail-label">Status Code:</span>
                                <span class="test-detail-value" style="color: {status_color};">
                                    {test.status_code} (expected: {test.expected_code})
                                </span>
                            </div>
"""

                html += """
                        </div>
"""

                # Add error message if present
                if test.error_message:
                    html += f"""
                        <div class="error-message">
                            <strong>Error:</strong> {test.error_message}
                        </div>
"""

                # Add response data if present
                if test.response_data and test.status in [TestStatus.PASS, TestStatus.FAIL]:
                    response_json = json.dumps(test.response_data, indent=2)
                    html += f"""
                        <details style="margin-top: 10px;">
                            <summary style="cursor: pointer; font-weight: 600; color: #667eea;">
                                View Response Data
                            </summary>
                            <div class="code-block">
                                <pre>{response_json}</pre>
                            </div>
                        </details>
"""

                html += """
                    </div>
"""

            html += """
                </div>
            </div>
"""

        html += f"""
        </div>

        <div class="footer">
            <p>Generated by Arcana Cloud API Test Suite</p>
            <p style="margin-top: 5px; opacity: 0.7;">
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>
</body>
</html>
"""

        return html


def main():
    """Main test execution"""
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print(f"   Please start the server first:")
        print(f"   ./start_monolithic.sh")
        sys.exit(1)

    # Run tests
    tester = APITester(BASE_URL)
    tester.run_all_tests()


if __name__ == '__main__':
    main()
