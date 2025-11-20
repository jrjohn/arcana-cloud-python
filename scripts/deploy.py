#!/usr/bin/env python3
"""
============================================================================
Arcana Cloud - Automated Deployment Script
============================================================================
Reads deployment-config.yaml and deploys the application to target environment
Supports Docker Compose and Kubernetes deployments
============================================================================
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


class DeploymentManager:
    """Manages application deployment based on configuration"""

    def __init__(self, config_path: str, environment: str = "production"):
        self.config_path = Path(config_path)
        self.environment = environment
        self.project_root = self.config_path.parent
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load and parse deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Apply environment-specific overrides
        if self.environment in config.get('environments', {}):
            env_config = config['environments'][self.environment]
            self._merge_config(config, env_config)

        return config

    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge override config into base config"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def build_images(self, mode: str, push: bool = False):
        """Build Docker images for the specified deployment mode"""
        print(f"\n{'='*80}")
        print(f"Building Docker images for {mode} mode")
        print(f"{'='*80}\n")

        mode_config = self.config['deployment_modes'].get(mode)
        if not mode_config:
            raise ValueError(f"Invalid deployment mode: {mode}")

        registry = self.config['global']['registry']
        version = self.config['global']['version']
        build_args = self.config.get('ci_cd', {}).get('build', {}).get('docker_build_args', {})

        # Build base image first
        self._build_image('base', registry, version, build_args)

        # Build images for each container in the mode
        for container_name, container_config in mode_config['containers'].items():
            dockerfile = container_config['dockerfile']
            image_name = container_config['name']

            self._build_image(
                image_name,
                registry,
                version,
                build_args,
                dockerfile=dockerfile
            )

            if push:
                self._push_image(f"{registry}/{image_name}:{version}")

    def _build_image(self, name: str, registry: str, version: str,
                     build_args: Dict, dockerfile: str = None):
        """Build a single Docker image"""
        if dockerfile is None:
            dockerfile = f"docker/Dockerfile.{name}"

        full_image_name = f"{registry}/{name}:{version}"
        latest_tag = f"{registry}/{name}:latest"

        print(f"Building {full_image_name}...")

        # Prepare build command
        cmd = [
            "docker", "build",
            "-t", full_image_name,
            "-t", latest_tag,
            "-f", str(self.project_root / dockerfile)
        ]

        # Add build arguments
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])

        cmd.append(str(self.project_root))

        # Execute build
        result = subprocess.run(cmd, cwd=self.project_root)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build image: {full_image_name}")

        print(f"Successfully built {full_image_name}\n")

    def _push_image(self, image_name: str):
        """Push Docker image to registry"""
        print(f"Pushing {image_name}...")
        result = subprocess.run(["docker", "push", image_name])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to push image: {image_name}")
        print(f"Successfully pushed {image_name}\n")

    def deploy_docker_compose(self, mode: str, detached: bool = True):
        """Deploy using Docker Compose"""
        print(f"\n{'='*80}")
        print(f"Deploying with Docker Compose - {mode} mode")
        print(f"{'='*80}\n")

        # Map mode to compose file
        compose_files = {
            'monolithic': 'docker-compose.yml',
            'layered': 'docker-compose.layered.yml',
            'microservices': 'docker-compose.microservices.yml'
        }

        compose_file = compose_files.get(mode)
        if not compose_file:
            raise ValueError(f"No compose file for mode: {mode}")

        compose_path = self.project_root / compose_file

        # Create .env file from configuration
        self._create_env_file()

        # Run docker-compose
        cmd = ["docker-compose", "-f", str(compose_path)]

        # Stop existing containers
        print("Stopping existing containers...")
        subprocess.run(cmd + ["down"], cwd=self.project_root)

        # Start new containers
        print("Starting containers...")
        if detached:
            cmd.extend(["up", "-d"])
        else:
            cmd.append("up")

        result = subprocess.run(cmd, cwd=self.project_root)
        if result.returncode != 0:
            raise RuntimeError("Docker Compose deployment failed")

        print("\nDeployment successful!")
        print("\nRunning services:")
        subprocess.run(["docker-compose", "-f", str(compose_path), "ps"],
                      cwd=self.project_root)

    def deploy_kubernetes(self, mode: str, namespace: str = None):
        """Deploy to Kubernetes"""
        print(f"\n{'='*80}")
        print(f"Deploying to Kubernetes - {mode} mode")
        print(f"{'='*80}\n")

        if namespace is None:
            namespace = self.config['global']['namespace']

        k8s_dir = self.project_root / 'k8s'

        # Create namespace
        print(f"Creating namespace: {namespace}")
        subprocess.run([
            "kubectl", "create", "namespace", namespace,
            "--dry-run=client", "-o", "yaml"
        ], stdout=subprocess.PIPE)
        subprocess.run([
            "kubectl", "apply", "-f",
            str(k8s_dir / "namespace.yaml")
        ])

        # Apply configurations in order
        manifests_order = [
            "rbac.yaml",
            "configmap.yaml",
            "secrets.yaml",
            "pvc.yaml",
            "controller-deployment.yaml",
            "service-deployment.yaml",
            "repository-deployment.yaml",
            "services.yaml",
            "hpa.yaml",
            "ingress.yaml"
        ]

        for manifest in manifests_order:
            manifest_path = k8s_dir / manifest
            if manifest_path.exists():
                print(f"Applying {manifest}...")
                result = subprocess.run([
                    "kubectl", "apply", "-f", str(manifest_path),
                    "-n", namespace
                ])
                if result.returncode != 0:
                    print(f"Warning: Failed to apply {manifest}")

        print("\nDeployment successful!")
        print("\nChecking deployment status:")
        subprocess.run([
            "kubectl", "get", "all", "-n", namespace
        ])

    def _create_env_file(self):
        """Create .env file from configuration"""
        env_path = self.project_root / ".env"
        env_vars = self.config['global']['environment']

        with open(env_path, 'w') as f:
            f.write("# Auto-generated environment file\n")
            f.write(f"# Environment: {self.environment}\n\n")

            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"Created environment file: {env_path}")

    def show_status(self, target: str = "docker"):
        """Show deployment status"""
        print(f"\n{'='*80}")
        print("Deployment Status")
        print(f"{'='*80}\n")

        if target == "docker":
            subprocess.run(["docker", "ps", "--format",
                          "table {{.Names}}\t{{.Status}}\t{{.Ports}}"])
        elif target == "kubernetes":
            namespace = self.config['global']['namespace']
            subprocess.run(["kubectl", "get", "all", "-n", namespace])

    def cleanup(self, target: str = "docker"):
        """Clean up deployment"""
        print(f"\n{'='*80}")
        print("Cleaning up deployment")
        print(f"{'='*80}\n")

        if target == "docker":
            subprocess.run(["docker-compose", "down", "-v"],
                         cwd=self.project_root)
            print("Docker Compose cleanup completed")

        elif target == "kubernetes":
            namespace = self.config['global']['namespace']
            response = input(f"Delete namespace '{namespace}' and all resources? (y/N): ")
            if response.lower() == 'y':
                subprocess.run(["kubectl", "delete", "namespace", namespace])
                print("Kubernetes cleanup completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Arcana Cloud Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build images for monolithic mode
  python deploy.py build --mode monolithic

  # Deploy to Docker Compose (layered mode)
  python deploy.py deploy --target docker --mode layered

  # Deploy to Kubernetes (microservices mode)
  python deploy.py deploy --target kubernetes --mode microservices

  # Show deployment status
  python deploy.py status --target docker

  # Cleanup
  python deploy.py cleanup --target docker
        """
    )

    parser.add_argument(
        "action",
        choices=["build", "deploy", "status", "cleanup"],
        help="Action to perform"
    )

    parser.add_argument(
        "--config",
        default="deployment-config.yaml",
        help="Path to deployment configuration file"
    )

    parser.add_argument(
        "--environment",
        default="production",
        choices=["development", "staging", "production"],
        help="Target environment"
    )

    parser.add_argument(
        "--mode",
        choices=["monolithic", "layered", "microservices"],
        help="Deployment mode"
    )

    parser.add_argument(
        "--target",
        choices=["docker", "kubernetes"],
        default="docker",
        help="Deployment target"
    )

    parser.add_argument(
        "--push",
        action="store_true",
        help="Push images to registry after building"
    )

    parser.add_argument(
        "--detached",
        action="store_true",
        default=True,
        help="Run Docker Compose in detached mode"
    )

    args = parser.parse_args()

    try:
        manager = DeploymentManager(args.config, args.environment)

        if args.action == "build":
            if not args.mode:
                parser.error("--mode is required for build action")
            manager.build_images(args.mode, args.push)

        elif args.action == "deploy":
            if not args.mode:
                parser.error("--mode is required for deploy action")

            if args.target == "docker":
                manager.deploy_docker_compose(args.mode, args.detached)
            elif args.target == "kubernetes":
                manager.deploy_kubernetes(args.mode)

        elif args.action == "status":
            manager.show_status(args.target)

        elif args.action == "cleanup":
            manager.cleanup(args.target)

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
