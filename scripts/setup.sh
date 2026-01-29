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

    # Check/Install Poetry
    if ! command -v poetry >/dev/null 2>&1; then
        log_warn "Poetry not found. Installing..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        if ! command -v poetry >/dev/null 2>&1; then
             log_error "Failed to install Poetry automatically."
             exit 1
        fi
        log_success "Poetry installed."
    fi

    # Check/Install pnpm
    if ! command -v pnpm >/dev/null 2>&1; then
        log_warn "pnpm not found. Installing..."
        if command -v npm >/dev/null 2>&1; then
            npm install -g pnpm
        else
             # Try standalone install if npm is missing
             curl -fsSL https://get.pnpm.io/install.sh | sh -
             # Assuming default pnpm location, typically depends on shell, but let's try updating PATH if we can guess
             export PNPM_HOME="$HOME/.local/share/pnpm"
             case ":$PATH:" in
               *":$PNPM_HOME:"*) ;;
               *) export PATH="$PNPM_HOME:$PATH" ;;
             esac
        fi

        if ! command -v pnpm >/dev/null 2>&1; then
             log_error "Failed to install pnpm automatically. Please install it manually."
             exit 1
        fi
        log_success "pnpm installed."
    fi

    local missing=()
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    # node is checked implicitly by pnpm, but good to keep if pnpm standalone was used and node is still needed for running app
    command -v node >/dev/null 2>&1 || missing+=("node")

    if [[ "$SKIP_DOCKER" == false ]]; then
        command -v docker >/dev/null 2>&1 || missing+=("docker")
        if command -v docker-compose >/dev/null 2>&1; then
             :
        elif docker compose version >/dev/null 2>&1; then
             :
        else
             missing+=("docker-compose")
        fi
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        echo ""
        echo "Please install the missing tools manually."
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
        if docker compose version >/dev/null 2>&1; then
            docker compose --profile ai up -d
        else
            docker-compose --profile ai up -d
        fi
        log_success "Docker services started"
    else
        log_warn "docker-compose.yml not found, skipping"
    fi
}

# Run database migrations
setup_db() {
    if [[ "$SKIP_DOCKER" == true ]]; then
        log_info "Skipping database setup"
        return
    fi

    log_info "Waiting for database..."

    # Wait for DB port
    local host="127.0.0.1"
    local port="5433"
    local timeout=60
    local start_time=$(date +%s)

    while ! (echo >/dev/tcp/$host/$port) >/dev/null 2>&1; do
        if [ $(($(date +%s) - $start_time)) -gt $timeout ]; then
            log_error "Timeout waiting for database"
            return 1
        fi
        sleep 1
    done

    log_info "Running database migrations..."
    if [[ -d backend ]]; then
        cd backend
        poetry run alembic upgrade head
        cd ..
        log_success "Database migrations applied"
    else
        log_warn "backend/ directory not found, skipping migrations"
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
    setup_db

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
