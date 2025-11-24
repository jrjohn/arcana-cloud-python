"""Script to inspect DI container configuration"""
import os
import sys

# Set environment
os.environ['DEPLOYMENT_MODE'] = 'microservices'
os.environ['DEPLOYMENT_LAYER'] = 'controller'
os.environ['USER_SERVICE_URLS'] = 'http://localhost:5001'
os.environ['DATABASE_URL'] = 'mysql+pymysql://arcana:arcana_pass@localhost:3306/arcana_cloud_test'

# Create Flask app to initialize DI container
from app import create_app

app = create_app('testing')

with app.app_context():
    from app.di_container import get_service_communication
    from app.communication.factory import CommunicationFactory

    # Check deployment settings
    print(f"=== Environment Variables ===")
    print(f"DEPLOYMENT_MODE: {os.getenv('DEPLOYMENT_MODE')}")
    print(f"DEPLOYMENT_LAYER: {os.getenv('DEPLOYMENT_LAYER')}")
    print(f"USER_SERVICE_URLS: {os.getenv('USER_SERVICE_URLS')}")

    # Check factory settings
    print(f"\n=== Communication Factory Settings ===")
    deployment_mode = CommunicationFactory._get_deployment_mode()
    deployment_layer = CommunicationFactory._get_deployment_layer()
    use_remote = CommunicationFactory._should_use_remote_communication(deployment_mode, deployment_layer)

    print(f"Deployment Mode (from factory): {deployment_mode}")
    print(f"Deployment Layer (from factory): {deployment_layer}")
    print(f"Should use remote communication: {use_remote}")

    # Check actual communication instance
    print(f"\n=== Actual Communication Instance ===")
    service_comm = get_service_communication()
    print(f"Communication type: {type(service_comm).__name__}")
    print(f"Communication instance: {service_comm}")

    if hasattr(service_comm, 'service_urls'):
        print(f"Service URLs: {service_comm.service_urls}")
    if hasattr(service_comm, 'service'):
        print(f"Has direct service instance: True")
        print(f"Service type: {type(service_comm.service).__name__}")
