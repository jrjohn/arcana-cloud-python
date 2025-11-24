"""Debug script to test DI container communication layer creation"""
import os

# Set environment variables
os.environ['DEPLOYMENT_MODE'] = 'microservices'
os.environ['DEPLOYMENT_LAYER'] = 'controller'
os.environ['USER_SERVICE_URLS'] = 'http://localhost:5001'
os.environ['DATABASE_URL'] = 'mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test'

# Import after setting env vars
from app.di_container import get_service_communication

print(f"DEPLOYMENT_MODE: {os.getenv('DEPLOYMENT_MODE')}")
print(f"DEPLOYMENT_LAYER: {os.getenv('DEPLOYMENT_LAYER')}")
print(f"USER_SERVICE_URLS: {os.getenv('USER_SERVICE_URLS')}")

# Get communication layer
service_comm = get_service_communication()

print(f"\nCommunication layer type: {type(service_comm).__name__}")
print(f"Communication layer: {service_comm}")

# Check if it's HTTP communication
if hasattr(service_comm, 'service_urls'):
    print(f"Service URLs: {service_comm.service_urls}")

# Try to get users
try:
    result = service_comm.get_users(page=1, per_page=5)
    print(f"\nResult: {result}")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
