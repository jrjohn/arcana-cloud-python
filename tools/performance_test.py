#!/usr/bin/env python3
"""
Performance Comparison: HTTP REST vs gRPC
Measures latency and throughput for various operations
"""
import time
import statistics
import requests
import grpc
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.grpc_protos import user_service_pb2, user_service_pb2_grpc, common_pb2


class PerformanceTest:
    def __init__(self, http_url: str, grpc_host: str, grpc_port: int):
        self.http_url = http_url
        self.grpc_host = grpc_host
        self.grpc_port = grpc_port
        self.http_session = requests.Session()

        # Create gRPC channel
        self.grpc_channel = grpc.insecure_channel(f'{grpc_host}:{grpc_port}')
        self.grpc_stub = user_service_pb2_grpc.UserServiceStub(self.grpc_channel)

        # Auth token (we'll get this from login)
        self.http_token = None

    def setup(self):
        """Setup: Login to get auth token"""
        print("Setting up performance test...")

        # HTTP Login
        response = self.http_session.post(
            f'{self.http_url}/api/v1/auth/login',
            json={'username_or_email': 'admin', 'password': os.environ.get('ADMIN_INIT_PASSWORD', '')}
        )

        if response.status_code == 200:
            self.http_token = response.json()['data']['access_token']
            print(f"✅ HTTP authentication successful")
        else:
            print(f"❌ HTTP authentication failed: {response.status_code}")

    def measure_latency(self, func, iterations: int = 100) -> Dict[str, float]:
        """Measure latency statistics for a function"""
        latencies = []

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func()
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convert to ms
            except Exception as e:
                print(f"Error during measurement: {e}")
                continue

        if not latencies:
            return {'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'p95': 0, 'p99': 0}

        latencies.sort()
        return {
            'min': min(latencies),
            'max': max(latencies),
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'p95': latencies[int(len(latencies) * 0.95)],
            'p99': latencies[int(len(latencies) * 0.99)]
        }

    # HTTP Operations
    def http_get_users(self):
        """HTTP: Get users list"""
        headers = {'Authorization': f'Bearer {self.http_token}'}
        response = self.http_session.get(f'{self.http_url}/api/v1/users', headers=headers)
        return response.status_code == 200

    def http_get_user_by_id(self):
        """HTTP: Get user by ID"""
        headers = {'Authorization': f'Bearer {self.http_token}'}
        response = self.http_session.get(f'{self.http_url}/api/v1/users/1', headers=headers)
        return response.status_code in [200, 404]

    def http_create_user(self):
        """HTTP: Create user"""
        headers = {'Authorization': f'Bearer {self.http_token}'}
        import random
        username = f'perftest_{random.randint(10000, 99999)}'
        response = self.http_session.post(
            f'{self.http_url}/api/v1/users',
            json={
                'username': username,
                'email': f'{username}@example.com',
                'password': os.environ.get('TEST_USER_PASSWORD', '')
            },
            headers=headers
        )
        return response.status_code in [201, 409]

    # gRPC Operations
    def grpc_get_users(self):
        """gRPC: Get users list"""
        request = user_service_pb2.GetUsersRequest(page=1, per_page=20)
        try:
            self.grpc_stub.GetUsers(request)
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    def grpc_get_user_by_id(self):
        """gRPC: Get user by ID"""
        request = user_service_pb2.GetUserByIdRequest(user_id=1)
        try:
            self.grpc_stub.GetUserById(request)
            return True
        except grpc.RpcError as e:
            return e.code() == grpc.StatusCode.NOT_FOUND  # 404 is acceptable

    def grpc_create_user(self):
        """gRPC: Create user"""
        import random
        username = f'perftest_{random.randint(10000, 99999)}'
        request = user_service_pb2.CreateUserRequest(
            username=username,
            email=f'{username}@example.com',
            password=os.environ.get('TEST_USER_PASSWORD', '')
        )
        try:
            self.grpc_stub.CreateUser(request)
            return True
        except grpc.RpcError as e:
            return e.code() == grpc.StatusCode.ALREADY_EXISTS  # Conflict is acceptable

    def run_comparison(self):
        """Run full performance comparison"""
        print("\n" + "="*80)
        print("Performance Comparison: HTTP REST vs gRPC")
        print("="*80)

        operations = [
            {
                'name': 'Get Users List',
                'http': self.http_get_users,
                'grpc': self.grpc_get_users,
                'iterations': 100
            },
            {
                'name': 'Get User By ID',
                'http': self.http_get_user_by_id,
                'grpc': self.grpc_get_user_by_id,
                'iterations': 100
            },
            {
                'name': 'Create User',
                'http': self.http_create_user,
                'grpc': self.grpc_create_user,
                'iterations': 50  # Fewer iterations for write operations
            }
        ]

        results = []

        for op in operations:
            print(f"\n{'='*80}")
            print(f"Testing: {op['name']} ({op['iterations']} iterations)")
            print(f"{'='*80}")

            # Measure HTTP
            print("  Measuring HTTP REST...")
            http_stats = self.measure_latency(op['http'], op['iterations'])

            # Measure gRPC
            print("  Measuring gRPC...")
            grpc_stats = self.measure_latency(op['grpc'], op['iterations'])

            # Calculate improvements
            speedup = http_stats['mean'] / grpc_stats['mean'] if grpc_stats['mean'] > 0 else 0

            results.append({
                'operation': op['name'],
                'http': http_stats,
                'grpc': grpc_stats,
                'speedup': speedup
            })

            # Print results
            print(f"\n  HTTP REST Results:")
            print(f"    Mean:   {http_stats['mean']:.2f} ms")
            print(f"    Median: {http_stats['median']:.2f} ms")
            print(f"    Min:    {http_stats['min']:.2f} ms")
            print(f"    Max:    {http_stats['max']:.2f} ms")
            print(f"    P95:    {http_stats['p95']:.2f} ms")
            print(f"    P99:    {http_stats['p99']:.2f} ms")

            print(f"\n  gRPC Results:")
            print(f"    Mean:   {grpc_stats['mean']:.2f} ms")
            print(f"    Median: {grpc_stats['median']:.2f} ms")
            print(f"    Min:    {grpc_stats['min']:.2f} ms")
            print(f"    Max:    {grpc_stats['max']:.2f} ms")
            print(f"    P95:    {grpc_stats['p95']:.2f} ms")
            print(f"    P99:    {grpc_stats['p99']:.2f} ms")

            print(f"\n  Performance:")
            if speedup > 1:
                print(f"    gRPC is {speedup:.2f}x faster than HTTP REST")
            else:
                print(f"    HTTP REST is {1/speedup:.2f}x faster than gRPC")

        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"\n{'Operation':<20} {'HTTP (ms)':<15} {'gRPC (ms)':<15} {'Speedup':<10}")
        print("-" * 80)

        for result in results:
            op = result['operation']
            http_mean = result['http']['mean']
            grpc_mean = result['grpc']['mean']
            speedup = result['speedup']

            print(f"{op:<20} {http_mean:>10.2f}     {grpc_mean:>10.2f}     {speedup:>6.2f}x")

        avg_speedup = sum(r['speedup'] for r in results) / len(results)
        print("-" * 80)
        print(f"{'Average Speedup:':<20} {avg_speedup:>6.2f}x (gRPC vs HTTP)")
        print(f"{'='*80}\n")

    def cleanup(self):
        """Cleanup resources"""
        self.grpc_channel.close()
        self.http_session.close()


if __name__ == '__main__':
    # Configuration
    HTTP_CONTROLLER_URL = 'http://localhost:5003'
    GRPC_SERVICE_HOST = 'localhost'
    GRPC_SERVICE_PORT = 50051

    test = PerformanceTest(HTTP_CONTROLLER_URL, GRPC_SERVICE_HOST, GRPC_SERVICE_PORT)

    try:
        test.setup()
        test.run_comparison()
    finally:
        test.cleanup()
