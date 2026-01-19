#!/usr/bin/env bash
# ============================================================
# DevBridge Diagnostic Script
# ============================================================
# Quick diagnosis of common issues in the development stack.
# Usage: ./scripts/diagnose.sh [command]
#
# Commands:
#   all       - Run all diagnostics (default)
#   services  - Check service health
#   env       - Validate environment variables
#   logs      - Show recent errors from all services
#   ports     - Check port availability
#   db        - Database diagnostics
#   help      - Show this help message
# ============================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
CHECK="✓"
CROSS="✗"
WARN="⚠"

# ============================================================
# Helper Functions
# ============================================================

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "  ${GREEN}${CHECK}${NC} $1"
}

print_error() {
    echo -e "  ${RED}${CROSS}${NC} $1"
}

print_warning() {
    echo -e "  ${YELLOW}${WARN}${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}→${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================================
# Diagnostic Functions
# ============================================================

diagnose_services() {
    print_header "Service Health Check"

    local all_healthy=true

    # Backend API
    echo -e "${YELLOW}Backend API (localhost:8001):${NC}"
    if curl -sf http://localhost:8001/health &>/dev/null; then
        print_success "Running"
        local version=$(curl -sf http://localhost:8001/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        if [[ -n "$version" ]]; then
            print_info "Version: $version"
        fi
    else
        print_error "Not running or not responding"
        print_info "Try: make dev-backend"
        all_healthy=false
    fi
    echo ""

    # Frontend
    echo -e "${YELLOW}Frontend (localhost:3001):${NC}"
    if curl -sf http://localhost:3001 &>/dev/null; then
        print_success "Running"
    else
        print_error "Not running or not responding"
        print_info "Try: make dev-frontend"
        all_healthy=false
    fi
    echo ""

    # PostgreSQL
    echo -e "${YELLOW}PostgreSQL (localhost:5432):${NC}"
    if docker exec devbridge-postgres pg_isready -U devbridge &>/dev/null; then
        print_success "Running"
        # Check connection count
        local conn_count=$(docker exec devbridge-postgres psql -U devbridge -t -c "SELECT count(*) FROM pg_stat_activity" 2>/dev/null | tr -d ' ')
        if [[ -n "$conn_count" ]]; then
            print_info "Active connections: $conn_count"
        fi
    else
        print_error "Not running"
        print_info "Try: docker compose up -d postgres"
        all_healthy=false
    fi
    echo ""

    # Redis
    echo -e "${YELLOW}Redis (localhost:6379):${NC}"
    if docker exec devbridge-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        print_success "Running"
    else
        print_error "Not running"
        print_info "Try: docker compose up -d redis"
        all_healthy=false
    fi
    echo ""

    # Observability (optional)
    echo -e "${YELLOW}Observability Stack (optional):${NC}"
    local obs_running=0

    if curl -sf http://localhost:3033/api/health &>/dev/null; then
        print_success "Grafana (localhost:3033)"
        ((obs_running++))
    else
        print_warning "Grafana not running"
    fi

    if curl -sf http://localhost:3100/ready 2>/dev/null | grep -q "ready"; then
        print_success "Loki (localhost:3100)"
        ((obs_running++))
    else
        print_warning "Loki not running"
    fi

    if curl -sf http://localhost:16686 &>/dev/null; then
        print_success "Jaeger (localhost:16686)"
        ((obs_running++))
    else
        print_warning "Jaeger not running"
    fi

    if [[ $obs_running -eq 0 ]]; then
        print_info "Start with: make obs-up"
    fi
    echo ""

    if $all_healthy; then
        echo -e "${GREEN}All core services are healthy!${NC}"
    else
        echo -e "${RED}Some services need attention.${NC}"
        return 1
    fi
}

diagnose_env() {
    print_header "Environment Configuration"

    local env_file="${1:-.env}"
    local issues=0

    if [[ ! -f "$env_file" ]]; then
        print_error ".env file not found"
        print_info "Copy from .env.example: cp .env.example .env"
        return 1
    fi

    print_success ".env file exists"

    # Required variables
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
    )

    echo ""
    echo -e "${YELLOW}Required Variables:${NC}"
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$env_file"; then
            local value=$(grep "^${var}=" "$env_file" | cut -d'=' -f2-)
            if [[ -z "$value" || "$value" == '""' || "$value" == "''" ]]; then
                print_error "$var is empty"
                ((issues++))
            else
                print_success "$var is set"
            fi
        else
            print_error "$var is missing"
            ((issues++))
        fi
    done

    # Optional but recommended
    echo ""
    echo -e "${YELLOW}Optional Variables:${NC}"
    local optional_vars=(
        "GITHUB_TOKEN"
        "OPENAI_API_KEY"
        "SENTRY_DSN"
    )

    for var in "${optional_vars[@]}"; do
        if grep -q "^${var}=" "$env_file"; then
            local value=$(grep "^${var}=" "$env_file" | cut -d'=' -f2-)
            if [[ -z "$value" || "$value" == '""' || "$value" == "''" ]]; then
                print_warning "$var is empty (optional)"
            else
                print_success "$var is set"
            fi
        else
            print_warning "$var not configured (optional)"
        fi
    done

    echo ""
    if [[ $issues -eq 0 ]]; then
        echo -e "${GREEN}Environment configuration looks good!${NC}"
    else
        echo -e "${RED}Found $issues issue(s) with environment configuration.${NC}"
        return 1
    fi
}

diagnose_ports() {
    print_header "Port Availability"

    local ports=(
        "3001:Frontend (Next.js)"
        "8001:Backend (FastAPI)"
        "5432:PostgreSQL"
        "6379:Redis"
        "3033:Grafana"
        "3100:Loki"
        "16686:Jaeger"
    )

    for entry in "${ports[@]}"; do
        local port="${entry%%:*}"
        local name="${entry#*:}"

        if lsof -i ":$port" &>/dev/null; then
            local pid=$(lsof -t -i ":$port" | head -1)
            local process=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
            print_success "Port $port ($name) - in use by $process"
        else
            print_warning "Port $port ($name) - available"
        fi
    done
}

diagnose_logs() {
    print_header "Recent Errors (last 50 lines)"

    echo -e "${YELLOW}Backend Errors:${NC}"
    if docker logs devbridge-backend-1 2>&1 | grep -i "error\|exception\|traceback" | tail -10; then
        :
    else
        print_success "No recent errors in backend logs"
    fi
    echo ""

    echo -e "${YELLOW}Worker Errors:${NC}"
    if docker logs devbridge-worker-1 2>&1 2>/dev/null | grep -i "error\|exception\|traceback" | tail -10; then
        :
    else
        print_success "No recent errors in worker logs (or worker not running)"
    fi
}

diagnose_db() {
    print_header "Database Diagnostics"

    if ! docker exec devbridge-postgres pg_isready -U devbridge &>/dev/null; then
        print_error "Cannot connect to PostgreSQL"
        return 1
    fi

    print_success "PostgreSQL is accepting connections"

    # Check database exists
    echo ""
    echo -e "${YELLOW}Database Info:${NC}"
    local db_size=$(docker exec devbridge-postgres psql -U devbridge -t -c "SELECT pg_size_pretty(pg_database_size('devbridge'))" 2>/dev/null | tr -d ' ')
    if [[ -n "$db_size" ]]; then
        print_info "Database size: $db_size"
    fi

    # Check table count
    local table_count=$(docker exec devbridge-postgres psql -U devbridge -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'" 2>/dev/null | tr -d ' ')
    if [[ -n "$table_count" ]]; then
        print_info "Tables: $table_count"
    fi

    # Check pending migrations
    echo ""
    echo -e "${YELLOW}Migration Status:${NC}"
    if cd backend && uv run alembic current 2>/dev/null; then
        print_success "Alembic is accessible"
    else
        print_warning "Could not check migration status"
    fi
}

show_help() {
    echo "DevBridge Diagnostic Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all       Run all diagnostics (default)"
    echo "  services  Check service health"
    echo "  env       Validate environment variables"
    echo "  logs      Show recent errors from all services"
    echo "  ports     Check port availability"
    echo "  db        Database diagnostics"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all diagnostics"
    echo "  $0 services     # Check only service health"
    echo "  $0 env          # Validate .env file"
}

# ============================================================
# Main
# ============================================================

main() {
    local command="${1:-all}"

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           DevBridge Diagnostic Tool                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

    case "$command" in
        all)
            diagnose_services
            diagnose_env
            diagnose_ports
            ;;
        services)
            diagnose_services
            ;;
        env)
            diagnose_env
            ;;
        logs)
            diagnose_logs
            ;;
        ports)
            diagnose_ports
            ;;
        db)
            diagnose_db
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            show_help
            exit 1
            ;;
    esac

    echo ""
}

main "$@"
