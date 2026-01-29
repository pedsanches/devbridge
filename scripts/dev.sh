#!/usr/bin/env bash
# ============================================================
# DevBridge - Development Server Script
# ============================================================
# Starts all development services
# Usage: ./scripts/dev.sh [backend|frontend|all]
# ============================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default: start all
MODE="${1:-all}"

docker_compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

wait_for_port() {
    local host="$1"
    local port="$2"
    local name="$3"
    local timeout_s="${4:-30}"

    local start
    start="$(date +%s)"

    while true; do
        if (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
            log_success "${name} ready on ${host}:${port}"
            return 0
        fi

        if (( $(date +%s) - start >= timeout_s )); then
            log_error "Timeout waiting for ${name} on ${host}:${port}"
            return 1
        fi

        sleep 0.2
    done
}

is_port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
        return $?
    fi

    # Fallback: best-effort check
    (echo >"/dev/tcp/127.0.0.1/${port}") >/dev/null 2>&1
}

# Check if Docker services are running
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker not found. Please install Docker Desktop."
        return 1
    fi

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon not running. Please start Docker Desktop."
        return 1
    fi

    log_info "Starting Docker services..."
    docker_compose --profile ai up -d

    # Wait only for dev dependencies; avoids arbitrary sleep.
    wait_for_port "127.0.0.1" 5433 "PostgreSQL" 60 || true
    wait_for_port "127.0.0.1" 6379 "Redis" 60 || true

    log_success "Docker services running"
}

# Start backend
start_backend() {
    log_info "Starting backend..."

    if [[ ! -d backend ]]; then
        log_error "backend/ directory not found"
        return 1
    fi

    cd backend
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
}

# Start frontend
start_frontend() {
    log_info "Starting frontend..."

    if [[ ! -d frontend ]]; then
        log_error "frontend/ directory not found"
        return 1
    fi

    cd frontend
    pnpm dev -p 3001 --webpack
}

# Start Celery worker
start_worker() {
    log_info "Starting Celery worker..."

    if [[ ! -d backend ]]; then
        log_error "backend/ directory not found"
        return 1
    fi

    cd backend
    poetry run celery -A app.worker worker --loglevel=info
}

# Start all services using tmux (if available)
start_all_tmux() {
    if ! command -v tmux >/dev/null 2>&1; then
        return 1
    fi

    SESSION="devbridge"

    # Kill existing session
    tmux kill-session -t $SESSION 2>/dev/null || true

    # Create new session
    tmux new-session -d -s $SESSION -n 'backend'
    tmux send-keys -t $SESSION:backend "cd $(pwd)/backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001" C-m

    tmux new-window -t $SESSION -n 'frontend'
    tmux send-keys -t $SESSION:frontend "cd $(pwd)/frontend && pnpm dev -p 3001" C-m

    tmux new-window -t $SESSION -n 'worker'
    tmux send-keys -t $SESSION:worker "cd $(pwd)/backend && poetry run celery -A app.worker worker --loglevel=info" C-m

    tmux attach-session -t $SESSION
}

# Start all services in background
start_all_bg() {
    log_info "Starting all services in background..."

    if is_port_in_use 8001; then
        log_error "Port 8001 already in use (backend)."
        log_error "Stop existing process or change port in scripts/dev.sh."
        return 1
    fi

    if is_port_in_use 3001; then
        log_error "Port 3001 already in use (frontend)."
        log_error "Stop existing process or change port in scripts/dev.sh."
        return 1
    fi

    local BACKEND_PID=""
    local FRONTEND_PID=""

    # Backend
    if [[ -d backend ]]; then
        (
            cd backend
            exec poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
        ) &
        BACKEND_PID=$!
        log_success "Backend started (PID: $BACKEND_PID)"
    fi

    # Frontend
    if [[ -d frontend ]]; then
        (
            cd frontend
            exec pnpm dev -p 3001 --webpack
        ) &
        FRONTEND_PID=$!
        log_success "Frontend started (PID: $FRONTEND_PID)"
    fi

    echo ""
    echo "Services running:"
    echo "  - Backend:  http://localhost:8001"
    echo "  - Frontend: http://localhost:3001"
    echo "  - API Docs: http://localhost:8001/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"

    # Wait for readiness (best-effort).
    wait_for_port "127.0.0.1" 8001 "Backend" 60 || true
    wait_for_port "127.0.0.1" 3001 "Frontend" 60 || true

    cleanup() {
        log_info "Stopping services..."

        if [[ -n "${BACKEND_PID}" ]]; then
            kill -TERM "${BACKEND_PID}" 2>/dev/null || true
        fi
        if [[ -n "${FRONTEND_PID}" ]]; then
            kill -TERM "${FRONTEND_PID}" 2>/dev/null || true
        fi

        wait "${BACKEND_PID}" 2>/dev/null || true
        wait "${FRONTEND_PID}" 2>/dev/null || true

        log_success "All services stopped"
    }

    trap cleanup INT TERM EXIT

    # Wait for children
    wait
}

# Main
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              DevBridge Development Server                 ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""

    # Start dependencies via docker-compose.yml (if present)
    if [[ -f docker-compose.yml ]]; then
        check_docker
    fi

    case "$MODE" in
        backend)
            start_backend
            ;;
        frontend)
            start_frontend
            ;;
        worker)
            start_worker
            ;;
        all)
            # Try tmux first, fallback to background
            if ! start_all_tmux; then
                start_all_bg
            fi
            ;;
        *)
            echo "Usage: ./scripts/dev.sh [backend|frontend|worker|all]"
            exit 1
            ;;
    esac
}

main "$@"
