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

# Check if Docker services are running
check_docker() {
    if ! (command -v docker-compose >/dev/null 2>&1 && docker-compose ps | grep -q "Up") && ! (docker compose ps | grep -q "Up"); then
        log_info "Starting Docker services..."
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose up -d
        else
            docker compose up -d
        fi
        sleep 3
    fi
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
    pnpm dev -p 3001
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

    # Backend
    if [[ -d backend ]]; then
        cd backend
        poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
        BACKEND_PID=$!
        cd ..
        log_success "Backend started (PID: $BACKEND_PID)"
    fi

    # Frontend
    if [[ -d frontend ]]; then
        cd frontend
        pnpm dev -p 3001 &
        FRONTEND_PID=$!
        cd ..
        log_success "Frontend started (PID: $FRONTEND_PID)"
    fi

    echo ""
    echo "Services running:"
    echo "  - Backend:  http://localhost:8001"
    echo "  - Frontend: http://localhost:3001"
    echo "  - API Docs: http://localhost:8001/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"

    # Wait for interrupt
    trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null' EXIT
    wait
}

# Main
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              DevBridge Development Server                 ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""

    # Check Docker if docker-compose exists
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
