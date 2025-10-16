# Integro Development Makefile

.PHONY: help install install-dev sync lock requirements docker-build docker-up docker-down test lint format clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Dependency Management

install: ## Install project dependencies with voice extras
	uv sync --extra voice

install-dev: ## Install project dependencies including dev tools
	uv sync --extra voice --extra dev

sync: ## Sync dependencies from pyproject.toml (updates uv.lock)
	uv sync --extra voice

lock: ## Update uv.lock file without installing
	uv lock
	@echo "✓ Updated uv.lock"

requirements: ## Generate requirements.txt from pyproject.toml
	uv pip compile pyproject.toml --extra voice -o requirements.txt
	@echo "✓ Generated requirements.txt with voice extras"

requirements-base: ## Generate requirements.txt without voice extras
	uv pip compile pyproject.toml -o requirements-base.txt
	@echo "✓ Generated requirements-base.txt without voice extras"

# Docker Commands

docker-build: ## Build all Docker containers
	docker-compose build

docker-build-backend: ## Build backend container only
	docker-compose build backend

docker-build-voice: ## Build voice-agent container only
	docker-compose build voice-agent

docker-up: ## Start all services
	docker-compose up -d

docker-up-logs: ## Start all services and show logs
	docker-compose up

docker-down: ## Stop all services
	docker-compose down

docker-restart: ## Restart all services
	docker-compose restart

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

# Development

run-backend: ## Run backend server locally
	uvicorn integro.web_server:app --host 0.0.0.0 --port 8888 --reload

run-voice: ## Run voice agent locally
	python scripts/run_voice_agent.py dev

# Testing

test: ## Run all tests
	pytest

test-verbose: ## Run tests with verbose output
	pytest -v

test-coverage: ## Run tests with coverage report
	pytest --cov=integro --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-fast: ## Run tests without slow markers
	pytest -m "not slow"

# Code Quality

lint: ## Run linters (ruff)
	ruff check .

lint-fix: ## Run linters and auto-fix issues
	ruff check --fix .

format: ## Format code with black
	black integro tests scripts

format-check: ## Check code formatting without making changes
	black --check integro tests scripts

mypy: ## Run type checking
	mypy integro

# Cleanup

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✓ Cleaned up Python artifacts"

clean-docker: ## Clean up Docker artifacts
	docker-compose down -v
	docker system prune -f
	@echo "✓ Cleaned up Docker artifacts"

# Database

db-migrate: ## Run database migrations (if applicable)
	@echo "Database migrations not yet implemented"

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d db
	@echo "✓ Database reset complete"

# Full Setup

full-setup: clean install requirements docker-build ## Complete setup from scratch
	@echo "✓ Full setup complete!"
	@echo "Run 'make docker-up' to start services"

# Simulation Testing

test-simulation: ## Run two-agent simulation test
	python test_two_agent_simulation.py

# Production

build-prod: ## Build production Docker images
	docker-compose -f docker-compose.yaml build --no-cache

deploy-railway: ## Deploy to Railway (requires Railway CLI)
	railway up

# Information

info: ## Show project information
	@echo "Integro Agent Lab"
	@echo "================="
	@echo "Python version: $$(python --version)"
	@echo "UV version: $$(uv --version)"
	@echo "Docker version: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "Dependencies:"
	@echo "  - pyproject.toml (source of truth)"
	@echo "  - uv.lock (locked versions)"
	@echo "  - requirements.txt (auto-generated for Docker)"
	@echo ""
	@echo "Services:"
	@echo "  - Backend API: http://localhost:8888"
	@echo "  - Frontend: http://localhost:8889"
	@echo "  - Qdrant: http://localhost:6333"
	@echo "  - PostgreSQL: localhost:5432"
