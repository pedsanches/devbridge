# ============================================================
# DevBridge Makefile
# ============================================================
# Usage: make <target>
# Run `make help` to see all available commands
# ============================================================

.PHONY: help dev setup test lint format build clean docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

## ============================================================
## DEVELOPMENT
## ============================================================

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)DevBridge$(NC) - Available Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

setup: ## Initial project setup
	@./scripts/setup.sh

dev: ## Start development servers
	@./scripts/dev.sh

dev-backend: ## Start only backend
	@./scripts/dev.sh backend

dev-frontend: ## Start only frontend
	@./scripts/dev.sh frontend

## ============================================================
## TESTING
## ============================================================

test: ## Run all tests
	@echo "$(BLUE)[TEST]$(NC) Running backend tests..."
	@cd backend && poetry run pytest
	@echo "$(BLUE)[TEST]$(NC) Running frontend tests..."
	@cd frontend && pnpm test

test-backend: ## Run backend tests
	@cd backend && poetry run pytest -v

test-frontend: ## Run frontend tests
	@cd frontend && pnpm test

test-cov: ## Run tests with coverage
	@cd backend && poetry run pytest --cov=app --cov-report=html
	@echo "$(GREEN)[OK]$(NC) Coverage report: backend/htmlcov/index.html"

## ============================================================
## CODE QUALITY
## ============================================================

lint: ## Run linters
	@echo "$(BLUE)[LINT]$(NC) Checking Python..."
	@cd backend && poetry run ruff check .
	@cd backend && poetry run mypy app/
	@echo "$(BLUE)[LINT]$(NC) Checking TypeScript..."
	@cd frontend && pnpm lint
	@echo "$(GREEN)[OK]$(NC) All checks passed"

complexity: ## Check code complexity
	@echo "$(BLUE)[COMPLEXITY]$(NC) Checking complexity (Radon)..."
	@cd backend && poetry run radon cc app/ -a -s

security: ## Check for security vulnerabilities
	@echo "$(BLUE)[SECURITY]$(NC) Checking security (Bandit)..."
	@cd backend && poetry run bandit -r app/ -c pyproject.toml

check-docs: ## Check documentation coverage
	@echo "$(BLUE)[DOCS]$(NC) Checking documentation (Interrogate)..."
	@cd backend && poetry run interrogate -v app/


format: ## Format code
	@echo "$(BLUE)[FORMAT]$(NC) Formatting Python..."
	@cd backend && poetry run ruff format .
	@echo "$(BLUE)[FORMAT]$(NC) Formatting TypeScript..."
	@cd frontend && pnpm format
	@echo "$(GREEN)[OK]$(NC) Code formatted"

precommit: ## Run pre-commit on all files
	@cd backend && poetry run pre-commit run --all-files

## ============================================================
## BUILD & DEPLOY
## ============================================================

build: ## Build for production
	@echo "$(BLUE)[BUILD]$(NC) Building backend..."
	@cd backend && poetry build
	@echo "$(BLUE)[BUILD]$(NC) Building frontend..."
	@cd frontend && pnpm build
	@echo "$(GREEN)[OK]$(NC) Build complete"

docker-build: ## Build Docker images
	@if command -v docker-compose >/dev/null 2>&1; then docker-compose build; else docker compose build; fi

## ============================================================
## DOCKER
## ============================================================

docker-up: ## Start Docker services
	@if command -v docker-compose >/dev/null 2>&1; then docker-compose up -d; else docker compose up -d; fi
	@echo "$(GREEN)[OK]$(NC) Docker services started"

docker-down: ## Stop Docker services
	@if command -v docker-compose >/dev/null 2>&1; then docker-compose down; else docker compose down; fi
	@echo "$(GREEN)[OK]$(NC) Docker services stopped"

docker-logs: ## Show Docker logs
	@if command -v docker-compose >/dev/null 2>&1; then docker-compose logs -f; else docker compose logs -f; fi

docker-ps: ## Show Docker status
	@if command -v docker-compose >/dev/null 2>&1; then docker-compose ps; else docker compose ps; fi

## ============================================================
## DATABASE
## ============================================================

db-migrate: ## Run database migrations
	@cd backend && poetry run alembic upgrade head

db-rollback: ## Rollback last migration
	@cd backend && poetry run alembic downgrade -1

db-seed: ## Seed database with test data
	@cd backend && poetry run python -m app.db.seed

reset-db: ## Reset database (drop volumes and re-migrate)
	@echo "$(BLUE)[RESET]$(NC) Resetting database..."
	@make clean-docker
	@make docker-up
	@echo "$(BLUE)[RESET]$(NC) Waiting for database to be ready..."
	@sleep 10
	@make db-migrate
	@echo "$(GREEN)[OK]$(NC) Database reset complete"

## ============================================================
## CLEANUP
## ============================================================

clean: ## Clean build artifacts
	@echo "$(BLUE)[CLEAN]$(NC) Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[OK]$(NC) Cleanup complete"

clean-docker: ## Remove Docker volumes and containers
	@if command -v docker-compose >/dev/null 2>&1; then docker-compose down -v --remove-orphans; else docker compose down -v --remove-orphans; fi
	@echo "$(GREEN)[OK]$(NC) Docker cleanup complete"
