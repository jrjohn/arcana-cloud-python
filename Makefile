# ============================================================================
# Arcana Cloud - Makefile
# ============================================================================
# Convenience commands for building and deploying the application
# ============================================================================

.PHONY: help build deploy clean test

# Default target
.DEFAULT_GOAL := help

# Variables
REGISTRY ?= docker.io/arcanacloud
VERSION ?= latest
MODE ?= monolithic
TARGET ?= docker
ENVIRONMENT ?= production

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)Arcana Cloud - Deployment Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

setup: ## Initial project setup
	@echo "$(BLUE)Setting up project...$(NC)"
	@cp -n .env.example .env || true
	@echo "$(GREEN)Created .env file (edit with your configuration)$(NC)"
	@pip install -r requirements.txt
	@pip install -r requirements-dev.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

dev: ## Run in development mode (monolithic)
	@echo "$(BLUE)Starting development server...$(NC)"
	@FLASK_ENV=development flask run --host=0.0.0.0 --port=5000

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@pytest tests/ -v --cov=app --cov-report=html

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	@flake8 app/ tests/
	@black --check app/ tests/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@black app/ tests/
	@isort app/ tests/

##@ Docker Build

build-base: ## Build base Docker image
	@echo "$(BLUE)Building base image...$(NC)"
	@./scripts/build.sh --mode base --registry $(REGISTRY) --version $(VERSION)

build-monolithic: ## Build monolithic image
	@echo "$(BLUE)Building monolithic image...$(NC)"
	@./scripts/build.sh --mode monolithic --registry $(REGISTRY) --version $(VERSION)

build-layered: ## Build layered images
	@echo "$(BLUE)Building layered images...$(NC)"
	@./scripts/build.sh --mode layered --registry $(REGISTRY) --version $(VERSION)

build-microservices: ## Build microservices images
	@echo "$(BLUE)Building microservices images...$(NC)"
	@./scripts/build.sh --mode microservices --registry $(REGISTRY) --version $(VERSION)

build-all: ## Build all images
	@echo "$(BLUE)Building all images...$(NC)"
	@./scripts/build.sh --mode all --registry $(REGISTRY) --version $(VERSION)

build-push: ## Build and push all images to registry
	@echo "$(BLUE)Building and pushing all images...$(NC)"
	@./scripts/build.sh --mode all --registry $(REGISTRY) --version $(VERSION) --push

##@ Docker Compose Deployment

compose-up: ## Start Docker Compose (monolithic mode)
	@echo "$(BLUE)Starting Docker Compose (monolithic)...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Services started$(NC)"
	@docker-compose ps

compose-up-layered: ## Start Docker Compose (layered mode)
	@echo "$(BLUE)Starting Docker Compose (layered)...$(NC)"
	@docker-compose -f docker-compose.layered.yml up -d
	@echo "$(GREEN)Services started$(NC)"
	@docker-compose -f docker-compose.layered.yml ps

compose-up-microservices: ## Start Docker Compose (microservices mode)
	@echo "$(BLUE)Starting Docker Compose (microservices)...$(NC)"
	@docker-compose -f docker-compose.microservices.yml up -d
	@echo "$(GREEN)Services started$(NC)"
	@docker-compose -f docker-compose.microservices.yml ps

compose-down: ## Stop Docker Compose
	@echo "$(BLUE)Stopping Docker Compose...$(NC)"
	@docker-compose down
	@docker-compose -f docker-compose.layered.yml down
	@docker-compose -f docker-compose.microservices.yml down
	@echo "$(GREEN)Services stopped$(NC)"

compose-logs: ## Show Docker Compose logs
	@docker-compose logs -f --tail=100

compose-ps: ## Show Docker Compose status
	@docker-compose ps

##@ Kubernetes Deployment

k8s-deploy: ## Deploy to Kubernetes (use MODE=layered)
	@echo "$(BLUE)Deploying to Kubernetes ($(MODE) mode)...$(NC)"
	@python scripts/deploy.py deploy --target kubernetes --mode $(MODE) --environment $(ENVIRONMENT)
	@echo "$(GREEN)Deployment complete$(NC)"

k8s-status: ## Show Kubernetes deployment status
	@echo "$(BLUE)Kubernetes Status:$(NC)"
	@kubectl get all -n arcana-cloud

k8s-logs: ## Show Kubernetes logs
	@kubectl logs -f -l app=arcana-cloud -n arcana-cloud --all-containers=true --tail=100

k8s-pods: ## Show Kubernetes pods
	@kubectl get pods -n arcana-cloud

k8s-services: ## Show Kubernetes services
	@kubectl get svc -n arcana-cloud

k8s-ingress: ## Show Kubernetes ingress
	@kubectl get ingress -n arcana-cloud

k8s-hpa: ## Show Horizontal Pod Autoscaler status
	@kubectl get hpa -n arcana-cloud

k8s-shell: ## Open shell in controller pod
	@kubectl exec -it -n arcana-cloud deployment/controller-layer -- /bin/bash

k8s-delete: ## Delete Kubernetes deployment
	@echo "$(RED)Warning: This will delete all resources in arcana-cloud namespace$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		kubectl delete namespace arcana-cloud; \
		echo "$(GREEN)Namespace deleted$(NC)"; \
	fi

##@ Database

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@flask db upgrade

db-rollback: ## Rollback last database migration
	@echo "$(BLUE)Rolling back database migration...$(NC)"
	@flask db downgrade

db-shell: ## Open database shell (Docker Compose)
	@docker-compose exec mysql mysql -u arcana -parcana_pass arcana_cloud

##@ Monitoring

logs-app: ## Show application logs (Docker)
	@docker-compose logs -f app --tail=100

logs-controller: ## Show controller logs (Docker layered)
	@docker-compose -f docker-compose.layered.yml logs -f controller-layer --tail=100

logs-service: ## Show service logs (Docker layered)
	@docker-compose -f docker-compose.layered.yml logs -f service-layer --tail=100

logs-repository: ## Show repository logs (Docker layered)
	@docker-compose -f docker-compose.layered.yml logs -f repository-layer --tail=100

metrics: ## Show metrics endpoint
	@curl http://localhost:5000/metrics

health: ## Check health status
	@echo "$(BLUE)Health Check:$(NC)"
	@curl -s http://localhost:5000/health | jq .
	@echo ""
	@echo "$(BLUE)Readiness Check:$(NC)"
	@curl -s http://localhost:5000/ready | jq .

##@ Cleanup

clean-docker: ## Clean Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-images: ## Remove built images
	@echo "$(BLUE)Removing built images...$(NC)"
	@docker images | grep arcana-cloud | awk '{print $$3}' | xargs docker rmi -f || true
	@echo "$(GREEN)Images removed$(NC)"

clean-all: clean-docker clean-images ## Clean everything
	@echo "$(GREEN)All cleaned up$(NC)"

##@ Utilities

shell-app: ## Open shell in app container (Docker)
	@docker-compose exec app /bin/bash

shell-controller: ## Open shell in controller container (Docker layered)
	@docker-compose -f docker-compose.layered.yml exec controller-layer /bin/bash

shell-service: ## Open shell in service container (Docker layered)
	@docker-compose -f docker-compose.layered.yml exec service-layer /bin/bash

shell-repository: ## Open shell in repository container (Docker layered)
	@docker-compose -f docker-compose.layered.yml exec repository-layer /bin/bash

validate-config: ## Validate deployment configuration
	@echo "$(BLUE)Validating deployment configuration...$(NC)"
	@python -c "import yaml; yaml.safe_load(open('deployment-config.yaml'))" && \
		echo "$(GREEN)Configuration is valid$(NC)" || \
		echo "$(RED)Configuration is invalid$(NC)"

version: ## Show version information
	@echo "$(BLUE)Arcana Cloud Version Information$(NC)"
	@echo "Version: $(VERSION)"
	@echo "Registry: $(REGISTRY)"
	@echo "Mode: $(MODE)"
	@echo "Environment: $(ENVIRONMENT)"
