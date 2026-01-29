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
RED := \033[0;31m
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

kill-ports: ## Kill processes on ports 8001 (backend) and 3001 (frontend)
	@echo "$(BLUE)[CLEANUP]$(NC) Checking for processes on ports 8001 and 3001..."
	@-lsof -ti:8001 | xargs kill -9 >/dev/null 2>&1 || true
	@-lsof -ti:3001 | xargs kill -9 >/dev/null 2>&1 || true
	@echo "$(GREEN)[OK]$(NC) Ports released"

dev: kill-ports ## Start development servers
	@./scripts/dev.sh

dev-backend: ## Start only backend
	@./scripts/dev.sh backend

dev-frontend: ## Start only frontend
	@./scripts/dev.sh frontend

dev-worker: ## Start only worker
	@./scripts/dev.sh worker

storybook: ## Start Storybook
	@cd frontend && pnpm storybook

## ============================================================
## TESTING
## ============================================================

test: ## Run all tests
	@echo "$(BLUE)[TEST]$(NC) Running backend tests..."
	@cd backend && uv run pytest
	@echo "$(BLUE)[TEST]$(NC) Running frontend tests..."
	@cd frontend && pnpm test

test-backend: ## Run backend tests
	@cd backend && uv run pytest -v

test-frontend: ## Run frontend tests
	@cd frontend && pnpm test

test-cov: ## Run tests with coverage
	@cd backend && uv run pytest --cov=app --cov-report=html
	@echo "$(GREEN)[OK]$(NC) Coverage report: backend/htmlcov/index.html"

test-e2e: ## Run E2E tests (headless)
	@cd frontend && pnpm test:e2e

test-e2e-ui: ## Run E2E tests with UI
	@cd frontend && pnpm test:e2e --ui

## ============================================================
## CODE QUALITY
## ============================================================

lint: ## Run linters
	@echo "$(BLUE)[LINT]$(NC) Checking Python..."
	@cd backend && uv run ruff check .
	@cd backend && uv run mypy
	@echo "$(BLUE)[LINT]$(NC) Checking TypeScript..."
	@cd frontend && pnpm lint
	@echo "$(GREEN)[OK]$(NC) All checks passed"

openapi-check: ## Validate OpenAPI spec
	@cd backend && uv run python scripts/check_openapi.py

openapi-sync: ## Regenerate OpenAPI spec
	@cd backend && uv run python scripts/check_openapi.py --write

complexity: ## Check code complexity
	@echo "$(BLUE)[COMPLEXITY]$(NC) Checking complexity (Radon)..."
	@cd backend && uv run radon cc app/ -a -s

security: ## Check for security vulnerabilities
	@echo "$(BLUE)[SECURITY]$(NC) Checking security (Bandit)..."
	@cd backend && uv run bandit -r app/ -c pyproject.toml

check-docs: ## Check documentation coverage
	@echo "$(BLUE)[DOCS]$(NC) Checking documentation (Interrogate)..."
	@cd backend && uv run interrogate -v app/


format: ## Format code
	@echo "$(BLUE)[FORMAT]$(NC) Formatting Python..."
	@cd backend && uv run ruff format .
	@echo "$(BLUE)[FORMAT]$(NC) Formatting TypeScript..."
	@cd frontend && pnpm format
	@echo "$(GREEN)[OK]$(NC) Code formatted"

precommit: ## Run pre-commit on all files
	@cd backend && uv run pre-commit run --all-files

## ============================================================
## BUILD & DEPLOY
## ============================================================

build: ## Build for production
	@echo "$(BLUE)[BUILD]$(NC) Building backend..."
	@cd backend && poetry build
	@echo "$(BLUE)[BUILD]$(NC) Building frontend..."
	@cd frontend && pnpm build
	@echo "$(BLUE)[BUILD]$(NC) Building Storybook..."
	@cd frontend && pnpm build-storybook
	@echo "$(GREEN)[OK]$(NC) Build complete"

docker-build: ## Build Docker images
	@if docker compose version >/dev/null 2>&1; then docker compose build; else docker-compose build; fi

## ============================================================
## DOCKER
## ============================================================

docker-up: ## Start Docker services
	@if docker compose version >/dev/null 2>&1; then docker compose up -d; else docker-compose up -d; fi
	@echo "$(GREEN)[OK]$(NC) Docker services started"

docker-down: ## Stop Docker services
	@if docker compose version >/dev/null 2>&1; then docker compose down; else docker-compose down; fi
	@echo "$(GREEN)[OK]$(NC) Docker services stopped"

docker-logs: ## Show Docker logs
	@if docker compose version >/dev/null 2>&1; then docker compose logs -f; else docker-compose logs -f; fi

docker-ps: ## Show Docker status
	@if docker compose version >/dev/null 2>&1; then docker compose ps; else docker-compose ps; fi

## ============================================================
## OBSERVABILITY (Grafana + Loki + Jaeger)
## ============================================================

obs-up: ## Start observability stack (Grafana, Loki, Jaeger)
	@echo "$(BLUE)[OBS]$(NC) Starting observability stack..."
	@docker compose --profile observability up -d
	@echo "$(GREEN)[OK]$(NC) Observability stack started"
	@echo ""
	@echo "  $(YELLOW)Grafana:$(NC)  http://localhost:3033 (admin/devbridge)"
	@echo "  $(YELLOW)Jaeger:$(NC)   http://localhost:16686"
	@echo "  $(YELLOW)Loki:$(NC)     http://localhost:3100"
	@echo ""

obs-down: ## Stop observability stack
	@echo "$(BLUE)[OBS]$(NC) Stopping observability stack..."
	@docker compose --profile observability down
	@echo "$(GREEN)[OK]$(NC) Observability stack stopped"

obs-logs: ## Show observability logs
	@docker compose --profile observability logs -f

## ============================================================
## DATABASE
## ============================================================

db-migrate: ## Run database migrations
	@cd backend && uv run alembic upgrade head

db-rollback: ## Rollback last migration
	@cd backend && uv run alembic downgrade -1

db-seed: ## Seed database with test data
	@cd backend && uv run python -m app.db.seed

reset-db: ## Reset database (drop volumes and re-migrate)
	@echo "$(BLUE)[RESET]$(NC) Resetting database..."
	@make clean-docker
	@make docker-up
	@echo "$(BLUE)[RESET]$(NC) Waiting for database to be ready..."
	@sleep 10
	@make db-migrate
	@echo "$(GREEN)[OK]$(NC) Database reset complete"

## ============================================================
## DIAGNOSTICS
## ============================================================

health: ## Check all services health
	@echo "$(BLUE)[HEALTH]$(NC) Checking services..."
	@echo ""
	@echo "$(YELLOW)Backend API:$(NC)"
	@curl -sf http://localhost:8001/health 2>/dev/null && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@curl -sf http://localhost:3001 2>/dev/null && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker exec devbridge-postgres pg_isready -U devbridge 2>/dev/null && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker exec devbridge-redis redis-cli ping 2>/dev/null | grep -q PONG && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""
	@echo "$(YELLOW)Grafana:$(NC)"
	@curl -sf http://localhost:3033/api/health 2>/dev/null | grep -q 'database' && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""
	@echo "$(YELLOW)Loki:$(NC)"
	@curl -sf http://localhost:3100/ready 2>/dev/null | grep -q "ready" && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""
	@echo "$(YELLOW)Jaeger:$(NC)"
	@curl -sf http://localhost:16686 2>/dev/null | grep -q "Jaeger" && echo "  $(GREEN)✓ Running$(NC)" || echo "  $(RED)✗ Not running$(NC)"
	@echo ""

logs-backend: ## Stream backend logs only
	@docker logs -f devbridge-backend-1 2>/dev/null || echo "Backend container not running"

logs-worker: ## Stream worker logs only
	@docker logs -f devbridge-worker-1 2>/dev/null || echo "Worker container not running"

test-parallel: ## Run backend tests in parallel (faster)
	@echo "$(BLUE)[TEST]$(NC) Running backend tests in parallel..."
	@cd backend && uv run pytest -n auto -v

diagnose: ## Full diagnostic of all services and config
	@./scripts/diagnose.sh all

diagnose-env: ## Validate .env configuration
	@./scripts/diagnose.sh env

diagnose-logs: ## Show recent errors from all services
	@./scripts/diagnose.sh logs

diagnose-ports: ## Check port availability
	@./scripts/diagnose.sh ports

diagnose-db: ## Database diagnostics
	@./scripts/diagnose.sh db

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
	@if docker compose version >/dev/null 2>&1; then docker compose down -v --remove-orphans; else docker-compose down -v --remove-orphans; fi
	@echo "$(GREEN)[OK]$(NC) Docker cleanup complete"
