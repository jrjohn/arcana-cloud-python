"""
gRPC Server Runner
Unified entry point for starting gRPC servers based on deployment layer
"""
import os
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_grpc_server():
    """
    Start gRPC server based on DEPLOYMENT_LAYER environment variable

    Environment Variables:
        DEPLOYMENT_LAYER: 'service' or 'repository'
        GRPC_PORT: Port to listen on (default: 50051 for service, 50052 for repository)
        COMMUNICATION_PROTOCOL: Must be 'grpc'
    """
    layer = os.getenv('DEPLOYMENT_LAYER', '').lower()
    protocol = os.getenv('COMMUNICATION_PROTOCOL', 'http').lower()

    if protocol != 'grpc':
        logger.error(f"COMMUNICATION_PROTOCOL is '{protocol}', expected 'grpc'")
        logger.error("This script should only be called when protocol is 'grpc'")
        sys.exit(1)

    logger.info(f"Starting gRPC server for layer: {layer}")
    logger.info(f"Communication protocol: {protocol}")

    if layer == 'service':
        logger.info("Initializing User Service gRPC Server...")
        from app.grpc_protos.servers.user_service_server import serve
        port = int(os.getenv('GRPC_PORT', '50051'))
        logger.info(f"Starting User Service on port {port}")
        server = serve(port=port)

    elif layer == 'repository':
        logger.info("Initializing Repository Service gRPC Server...")
        from app.grpc_protos.servers.repository_service_server import serve
        port = int(os.getenv('GRPC_PORT', '50052'))
        logger.info(f"Starting Repository Service on port {port}")
        server = serve(port=port)

    else:
        logger.error(f"Unknown DEPLOYMENT_LAYER: '{layer}'")
        logger.error("Valid values: 'service', 'repository'")
        sys.exit(1)

    logger.info("gRPC server started successfully")
    logger.info("Press Ctrl+C to stop")

    # Keep server running
    try:
        while True:
            time.sleep(86400)  # Sleep for 1 day
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(0)
        logger.info("Server stopped")


if __name__ == '__main__':
    start_grpc_server()
