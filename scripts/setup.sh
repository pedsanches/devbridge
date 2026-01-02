#!/usr/bin/env bash
# ============================================================
# DevBridge - Setup Script
# ============================================================
# Initializes the development environment
# Usage: ./scripts/setup.sh [--skip-docker] [--skip-precommit]
# ============================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
SKIP_DOCKER=false
SKIP_PRECOMMIT=false

# Env Vars for Installer
export POETRY_REQUESTS_TIMEOUT=300
export PIP_DEFAULT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker) SKIP_DOCKER=true; shift ;;
        --skip-precommit) SKIP_PRECOMMIT=true; shift ;;
        --help)
            echo "Usage: ./scripts/setup.sh [--skip-docker] [--skip-precommit]"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check required tools
check_requirements() {
    log_info "Checking requirements..."

    local missing=()

    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v poetry >/dev/null 2>&1 || missing+=("poetry")
    command -v node >/dev/null 2>&1 || missing+=("node")
    command -v pnpm >/dev/null 2>&1 || missing+=("pnpm")

    if [[ "$SKIP_DOCKER" == false ]]; then
        command -v docker >/dev/null 2>&1 || missing+=("docker")
        if ! command -v docker-compose >/dev/null 2>&1; then
            if ! docker compose version >/dev/null 2>&1; then
                missing+=("docker-compose")
            fi
        fi
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        echo ""
        echo "Install missing tools:"
        echo "  - poetry: curl -sSL https://install.python-poetry.org | python3 -"
        echo "  - pnpm: npm install -g pnpm"
        echo "  - docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    log_success "All requirements met"
}

# Setup environment file
setup_env() {
    log_info "Setting up environment..."

    if [[ ! -f .env ]]; then
        cp .env.example .env
        log_success "Created .env from .env.example"
        log_warn "Please edit .env with your configuration"
    else
        log_info ".env already exists, skipping"
    fi
}

# Install backend dependencies
setup_backend() {
    log_info "Setting up backend..."

    if [[ -d backend ]]; then
        cd backend
        poetry install
        cd ..
        log_success "Backend dependencies installed"
    else
        log_warn "backend/ directory not found, skipping"
    fi
}

# Install frontend dependencies
setup_frontend() {
    log_info "Setting up frontend..."

    if [[ -d frontend ]]; then
        cd frontend
        pnpm install
        cd ..
        log_success "Frontend dependencies installed"
    else
        log_warn "frontend/ directory not found, skipping"
    fi
}

# Setup pre-commit hooks
setup_precommit() {
    if [[ "$SKIP_PRECOMMIT" == true ]]; then
        log_info "Skipping pre-commit setup"
        return
    fi

    log_info "Setting up pre-commit hooks..."

    if [[ -f .pre-commit-config.yaml ]]; then
        if [[ -d backend ]]; then
            cd backend
            poetry run pre-commit install
            poetry run pre-commit install --hook-type commit-msg
            cd ..
        fi
        log_success "Pre-commit hooks installed"
    else
        log_warn ".pre-commit-config.yaml not found, skipping"
    fi
}

# Start Docker services
setup_docker() {
    if [[ "$SKIP_DOCKER" == true ]]; then
        log_info "Skipping Docker setup"
        return
    fi

    log_info "Starting Docker services..."

    if [[ -f docker-compose.yml ]]; then
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose up -d
        else
            docker compose up -d
        fi
        log_success "Docker services started"
    else
        log_warn "docker-compose.yml not found, skipping"
    fi
}

# Create secrets directory
setup_secrets() {
    log_info "Setting up secrets directory..."

    mkdir -p secrets

    if [[ ! -f secrets/.gitkeep ]]; then
        touch secrets/.gitkeep
    fi

    # Add to gitignore if not present
    if ! grep -q "secrets/" .gitignore 2>/dev/null; then
        echo "secrets/" >> .gitignore
    fi

    log_success "Secrets directory ready"
}

# Main
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  DevBridge Setup                         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""

    check_requirements
    setup_env
    setup_secrets
    setup_backend
    setup_frontend
    setup_precommit
    setup_docker

    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  Setup Complete! 🎉                       ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env with your configuration"
    echo "  2. Run: make dev (or ./scripts/dev.sh)"
    echo ""
}

main "$@"
