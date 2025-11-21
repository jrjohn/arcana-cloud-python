"""
Communication Layer Usage Examples
Demonstrates how to use the communication layer in different modes
"""
import os
from app.communication import CommunicationFactory


def example_monolithic_mode():
    """Example: Monolithic mode - direct in-process calls"""
    print("="*60)
    print("Example: Monolithic Mode")
    print("="*60)

    # Setup environment
    os.environ['DEPLOYMENT_MODE'] = 'monolithic'
    os.environ['DEPLOYMENT_LAYER'] = 'monolithic'

    # Create service communication
    service_comm = CommunicationFactory.create_service_communication()

    print(f"Communication Mode: {service_comm.get_mode()}")
    print(f"Communication Protocol: {service_comm.get_protocol()}")
    print(f"Health Check: {service_comm.health_check()}")

    # Use service communication
    try:
        result = service_comm.get_users(page=1, per_page=10)
        print(f"Users retrieved: {len(result.get('items', []))} users")
    except Exception as e:
        print(f"Error: {e}")

    print()


def example_layered_mode_http():
    """Example: Layered mode with HTTP"""
    print("="*60)
    print("Example: Layered Mode with HTTP")
    print("="*60)

    # Setup environment (Controller layer)
    os.environ['DEPLOYMENT_MODE'] = 'layered'
    os.environ['DEPLOYMENT_LAYER'] = 'controller'
    os.environ['COMMUNICATION_PROTOCOL'] = 'http'
    os.environ['USER_SERVICE_URLS'] = 'http://service-layer:5001'

    # Create service communication
    service_comm = CommunicationFactory.create_service_communication()

    print(f"Communication Mode: {service_comm.get_mode()}")
    print(f"Communication Protocol: {service_comm.get_protocol()}")
    print(f"Service URLs: {os.getenv('USER_SERVICE_URLS')}")

    # This will make HTTP call to service layer
    try:
        result = service_comm.get_user_by_id(user_id=1)
        print(f"User retrieved via HTTP: {result.get('username')}")
    except Exception as e:
        print(f"Error (expected if service not running): {e}")

    print()


def example_layered_mode_grpc():
    """Example: Layered mode with gRPC"""
    print("="*60)
    print("Example: Layered Mode with gRPC")
    print("="*60)

    # Setup environment (Controller layer)
    os.environ['DEPLOYMENT_MODE'] = 'layered'
    os.environ['DEPLOYMENT_LAYER'] = 'controller'
    os.environ['COMMUNICATION_PROTOCOL'] = 'grpc'
    os.environ['USER_SERVICE_URLS'] = 'service-layer:50051'

    # Create service communication
    service_comm = CommunicationFactory.create_service_communication()

    print(f"Communication Mode: {service_comm.get_mode()}")
    print(f"Communication Protocol: {service_comm.get_protocol()}")
    print(f"Service URLs: {os.getenv('USER_SERVICE_URLS')}")

    # This will make gRPC call to service layer
    try:
        result = service_comm.get_user_by_id(user_id=1)
        print(f"User retrieved via gRPC: {result.get('username')}")
    except NotImplementedError as e:
        print(f"gRPC not implemented yet: {e}")
    except Exception as e:
        print(f"Error: {e}")

    print()


def example_microservices_mode():
    """Example: Microservices mode with gRPC"""
    print("="*60)
    print("Example: Microservices Mode with gRPC")
    print("="*60)

    # Setup environment
    os.environ['DEPLOYMENT_MODE'] = 'microservices'
    os.environ['DEPLOYMENT_LAYER'] = 'service'
    os.environ['COMMUNICATION_PROTOCOL'] = 'grpc'
    os.environ['USER_SERVICE_URLS'] = 'user-service:50051'
    os.environ['USER_REPO_URLS'] = 'user-repository:50052'

    # Create service communication
    service_comm = CommunicationFactory.create_service_communication()
    repo_comm = CommunicationFactory.create_repository_communication()

    print(f"Service Communication Mode: {service_comm.get_mode()}")
    print(f"Service Communication Protocol: {service_comm.get_protocol()}")
    print(f"Repository Communication Mode: {repo_comm.get_mode()}")
    print(f"Repository Communication Protocol: {repo_comm.get_protocol()}")

    print()


def show_communication_info():
    """Show current communication configuration"""
    print("="*60)
    print("Current Communication Configuration")
    print("="*60)

    info = CommunicationFactory.get_communication_info()

    print(f"Deployment Mode: {info['deployment_mode']}")
    print(f"Deployment Layer: {info['deployment_layer']}")
    print(f"Communication Protocol: {info['communication_protocol']}")
    print()
    print("Service Communication:")
    print(f"  Remote: {info['service_communication']['remote']}")
    print(f"  Protocol: {info['service_communication']['protocol']}")
    print(f"  URLs: {info['service_communication']['urls']}")
    print()
    print("Repository Communication:")
    print(f"  Remote: {info['repository_communication']['remote']}")
    print(f"  Protocol: {info['repository_communication']['protocol']}")
    print(f"  URLs: {info['repository_communication']['urls']}")
    print()


if __name__ == '__main__':
    # Run all examples
    example_monolithic_mode()
    example_layered_mode_http()
    example_layered_mode_grpc()
    example_microservices_mode()
    show_communication_info()
