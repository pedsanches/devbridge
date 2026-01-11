#!/bin/bash

# MCP Toolbox Setup Script
# This script helps you set up and test the MCP Toolbox for Databases

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if toolbox binary exists
check_binary() {
    print_header "Checking Toolbox Binary"

    if [ -f "./toolbox" ]; then
        print_success "Toolbox binary found"
        VERSION=$(./toolbox --version 2>&1 || echo "unknown")
        print_info "Version: $VERSION"
        return 0
    else
        print_error "Toolbox binary not found"
        print_info "Please download it first using the installation instructions"
        return 1
    fi
}

# Check Google Cloud authentication
check_gcloud_auth() {
    print_header "Checking Google Cloud Authentication"

    if command -v gcloud &> /dev/null; then
        print_success "gcloud CLI found"

        # Check if authenticated
        if gcloud auth application-default print-access-token &> /dev/null; then
            print_success "Application Default Credentials (ADC) configured"
            ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "unknown")
            print_info "Active account: $ACCOUNT"
        else
            print_warning "ADC not configured"
            print_info "Run: gcloud auth application-default login"
        fi
    else
        print_warning "gcloud CLI not found"
        print_info "Install from: https://cloud.google.com/sdk/docs/install"
    fi
}

# Create environment file template
create_env_template() {
    print_header "Creating Environment Template"

    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping .env creation"
            return 0
        fi
    fi

    cat > .env << 'EOF'
# Google Cloud Project Configuration
export GCP_PROJECT_ID="your-project-id"

# AlloyDB Production Configuration
export ALLOYDB_PROD_REGION="us-central1"
export ALLOYDB_PROD_CLUSTER="your-cluster"
export ALLOYDB_PROD_INSTANCE="your-instance"
export ALLOYDB_PROD_DATABASE="your-database"
export ALLOYDB_PROD_USER="your-user@your-domain.com"
export ALLOYDB_PROD_PASSWORD=""  # Leave empty for IAM auth

# AlloyDB Development Configuration
export ALLOYDB_DEV_REGION="us-central1"
export ALLOYDB_DEV_CLUSTER="dev-cluster"
export ALLOYDB_DEV_INSTANCE="dev-instance"
export ALLOYDB_DEV_DATABASE="dev_db"
export ALLOYDB_DEV_USER="dev-user"
export ALLOYDB_DEV_PASSWORD="dev-password"

# Local PostgreSQL Configuration
export LOCAL_PG_HOST="127.0.0.1"
export LOCAL_PG_PORT="5432"
export LOCAL_PG_DATABASE="local_db"
export LOCAL_PG_USER="postgres"
export LOCAL_PG_PASSWORD="postgres"
EOF

    print_success "Created .env template"
    print_warning "Please edit .env with your actual credentials"
}

# Create minimal tools.yaml
create_minimal_config() {
    print_header "Creating Minimal Configuration"

    if [ -f "tools.yaml" ]; then
        print_warning "tools.yaml already exists"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping tools.yaml creation"
            return 0
        fi
    fi

    cat > tools.yaml << 'EOF'
# Minimal MCP Toolbox Configuration
# This is a starter configuration - customize it for your needs

sources:
  # Example: Local PostgreSQL
  local-db:
    kind: postgres
    host: ${LOCAL_PG_HOST:-127.0.0.1}
    port: ${LOCAL_PG_PORT:-5432}
    database: ${LOCAL_PG_DATABASE:-postgres}
    user: ${LOCAL_PG_USER:-postgres}
    password: ${LOCAL_PG_PASSWORD}

tools:
  # Simple test tool
  list-databases:
    kind: postgres-sql
    source: local-db
    description: List all databases
    statement: |
      SELECT datname FROM pg_database
      WHERE datistemplate = false
      ORDER BY datname;

  # List tables
  list-tables:
    kind: postgres-sql
    source: local-db
    description: List all tables in the current database
    statement: |
      SELECT
        schemaname,
        tablename
      FROM pg_tables
      WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
      ORDER BY schemaname, tablename;

toolsets:
  basic:
    - list-databases
    - list-tables
EOF

    print_success "Created minimal tools.yaml"
    print_info "This configuration uses local PostgreSQL for testing"
}

# Test configuration
test_config() {
    print_header "Testing Configuration"

    if [ ! -f "tools.yaml" ]; then
        print_error "tools.yaml not found"
        print_info "Create it first using option 3"
        return 1
    fi

    print_info "Validating configuration..."

    # Try to start the server briefly
    timeout 5s ./toolbox --tools-file tools.yaml --log-level INFO 2>&1 | head -n 20 || true

    print_success "Configuration validation complete"
    print_info "Check the output above for any errors"
}

# Run with UI
run_with_ui() {
    print_header "Starting Toolbox with UI"

    if [ ! -f "tools.yaml" ]; then
        print_error "tools.yaml not found"
        print_info "Create it first using option 3"
        return 1
    fi

    print_info "Starting server on http://127.0.0.1:5000"
    print_info "Press Ctrl+C to stop"

    ./toolbox --tools-file tools.yaml --ui
}

# Run with prebuilt config
run_prebuilt() {
    print_header "Available Prebuilt Configurations"

    echo "AlloyDB:"
    echo "  1. alloydb-postgres"
    echo "  2. alloydb-postgres-admin"
    echo "  3. alloydb-postgres-observability"
    echo ""
    echo "Cloud SQL:"
    echo "  4. cloud-sql-postgres"
    echo "  5. cloud-sql-mysql"
    echo "  6. cloud-sql-mssql"
    echo ""
    echo "Other:"
    echo "  7. postgres"
    echo "  8. mysql"
    echo "  9. bigquery"
    echo "  10. spanner"
    echo ""

    read -p "Enter number (or 'q' to quit): " choice

    case $choice in
        1) CONFIG="alloydb-postgres" ;;
        2) CONFIG="alloydb-postgres-admin" ;;
        3) CONFIG="alloydb-postgres-observability" ;;
        4) CONFIG="cloud-sql-postgres" ;;
        5) CONFIG="cloud-sql-mysql" ;;
        6) CONFIG="cloud-sql-mssql" ;;
        7) CONFIG="postgres" ;;
        8) CONFIG="mysql" ;;
        9) CONFIG="bigquery" ;;
        10) CONFIG="spanner" ;;
        q|Q) return 0 ;;
        *) print_error "Invalid choice"; return 1 ;;
    esac

    print_info "Starting with prebuilt config: $CONFIG"
    print_info "Press Ctrl+C to stop"

    ./toolbox --prebuilt "$CONFIG"
}

# Show help
show_help() {
    cat << EOF

MCP Toolbox Setup Script - Help

This script helps you set up and test the MCP Toolbox for Databases.

Options:
  1. Check system requirements
     - Verifies toolbox binary exists
     - Checks Google Cloud authentication

  2. Create environment template
     - Creates .env file with placeholder values
     - You need to edit it with your actual credentials

  3. Create minimal configuration
     - Creates a basic tools.yaml for testing
     - Uses local PostgreSQL by default

  4. Test configuration
     - Validates your tools.yaml
     - Shows any configuration errors

  5. Run with UI
     - Starts the toolbox with web interface
     - Access at http://127.0.0.1:5000

  6. Run with prebuilt config
     - Quick start with predefined configurations
     - No tools.yaml needed

  7. Show this help

  0. Exit

For more information, see README.md

EOF
}

# Main menu
main_menu() {
    while true; do
        print_header "MCP Toolbox Setup Menu"

        echo "1. Check system requirements"
        echo "2. Create environment template (.env)"
        echo "3. Create minimal configuration (tools.yaml)"
        echo "4. Test configuration"
        echo "5. Run with UI"
        echo "6. Run with prebuilt config"
        echo "7. Show help"
        echo "0. Exit"
        echo ""

        read -p "Select an option: " choice

        case $choice in
            1)
                check_binary
                check_gcloud_auth
                ;;
            2)
                create_env_template
                ;;
            3)
                create_minimal_config
                ;;
            4)
                test_config
                ;;
            5)
                run_with_ui
                ;;
            6)
                run_prebuilt
                ;;
            7)
                show_help
                ;;
            0)
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main menu
main_menu
