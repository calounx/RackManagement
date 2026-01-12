#!/bin/bash

#############################################################################
# HomeRack Production Deployment Script
#
# This script deploys HomeRack to production with PostgreSQL.
#
# Usage:
#   ./deploy_production.sh [options]
#
# Options:
#   --skip-migration         Skip data migration from SQLite
#   --skip-backup            Skip creating SQLite backup
#   --migrate-only           Only run data migration, don't deploy
#   --force                  Skip all confirmation prompts
#
#############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${PROJECT_DIR}/backend"
SQLITE_PATH="${BACKEND_DIR}/homerack.db"

# Options
SKIP_MIGRATION=false
SKIP_BACKUP=false
MIGRATE_ONLY=false
FORCE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --migrate-only)
            MIGRATE_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "HomeRack Production Deployment Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-migration    Skip data migration from SQLite"
            echo "  --skip-backup       Skip creating SQLite backup"
            echo "  --migrate-only      Only run data migration, don't deploy"
            echo "  --force             Skip all confirmation prompts"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==>${NC} ${BLUE}$1${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_info "✓ Docker installed"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    log_info "✓ Docker Compose installed"

    # Check .env.production
    if [ ! -f "${PROJECT_DIR}/.env.production" ]; then
        log_error ".env.production not found"
        log_error "Please copy .env.production.example to .env.production and configure it"
        exit 1
    fi
    log_info "✓ .env.production exists"

    # Check for default passwords
    if grep -q "CHANGE_THIS" "${PROJECT_DIR}/.env.production"; then
        log_error ".env.production contains default passwords"
        log_error "Please update POSTGRES_PASSWORD, SECRET_KEY, and JWT_SECRET_KEY"
        exit 1
    fi
    log_info "✓ Production secrets configured"
}

# Load environment variables
load_env() {
    log_step "Loading environment variables"

    set -a
    source "${PROJECT_DIR}/.env.production"
    set +a

    log_info "✓ Environment loaded"
}

# Start PostgreSQL
start_postgres() {
    log_step "Starting PostgreSQL"

    cd "${PROJECT_DIR}"
    docker-compose -f docker-compose.prod.yml up -d postgres

    log_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec homerack-postgres pg_isready -U homerack_user -d homerack &> /dev/null; then
            log_info "✓ PostgreSQL is ready"
            return 0
        fi
        sleep 2
    done

    log_error "PostgreSQL failed to start"
    exit 1
}

# Apply migrations
apply_migrations() {
    log_step "Applying database migrations"

    cd "${BACKEND_DIR}"

    # Export DATABASE_URL for migrations
    export DATABASE_URL="postgresql://homerack_user:${POSTGRES_PASSWORD}@localhost:5432/homerack"

    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        log_warn "Alembic not found, installing dependencies..."
        pip install -r requirements.txt
    fi

    # Run migrations
    alembic upgrade head

    log_info "✓ Migrations applied"
}

# Migrate data
migrate_data() {
    log_step "Migrating data from SQLite to PostgreSQL"

    # Check if SQLite database exists
    if [ ! -f "${SQLITE_PATH}" ]; then
        log_warn "SQLite database not found at ${SQLITE_PATH}"
        log_warn "Skipping data migration"
        return 0
    fi

    cd "${BACKEND_DIR}"

    # Run migration script
    python scripts/migrate_to_postgres.py \
        --sqlite-path "${SQLITE_PATH}" \
        --postgres-url "postgresql://homerack_user:${POSTGRES_PASSWORD}@localhost:5432/homerack"

    log_info "✓ Data migration completed"
}

# Deploy services
deploy_services() {
    log_step "Deploying all services"

    cd "${PROJECT_DIR}"

    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down

    # Build and start all services
    log_info "Building and starting services..."
    docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --build

    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check service health
    for i in {1..30}; do
        if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
            log_info "✓ Services are healthy"
            return 0
        fi
        sleep 2
    done

    log_warn "Services may not be fully healthy yet"
}

# Verify deployment
verify_deployment() {
    log_step "Verifying deployment"

    # Check database connection
    if curl -sf http://localhost:8080/health > /dev/null; then
        log_info "✓ Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi

    # Check database type
    DB_TYPE=$(curl -sf http://localhost:8080/health | grep -o '"database_type":"[^"]*"' | cut -d'"' -f4)
    if [ "$DB_TYPE" = "postgresql" ]; then
        log_info "✓ Using PostgreSQL database"
    else
        log_error "Not using PostgreSQL: $DB_TYPE"
        return 1
    fi

    # Get pool info
    POOL_INFO=$(curl -sf http://localhost:8080/health | grep -o '"pool_info":{[^}]*}')
    if [ -n "$POOL_INFO" ]; then
        log_info "✓ Connection pool active: $POOL_INFO"
    fi
}

# Show deployment info
show_info() {
    log_step "Deployment Information"

    echo ""
    echo "HomeRack is now deployed on lampadas.local!"
    echo ""
    echo "Access the application:"
    echo "  http://lampadas.local:8080"
    echo ""
    echo "Useful commands:"
    echo "  View logs:           docker-compose -f docker-compose.prod.yml logs -f"
    echo "  Check status:        docker-compose -f docker-compose.prod.yml ps"
    echo "  Stop services:       docker-compose -f docker-compose.prod.yml down"
    echo "  Restart services:    docker-compose -f docker-compose.prod.yml restart"
    echo ""
    echo "Backup database:"
    echo "  cd deploy && ./backup_postgres.sh"
    echo ""
    echo "Restore database:"
    echo "  cd deploy && ./restore_postgres.sh --backup-file ./backups/homerack_TIMESTAMP.sql.gz"
    echo ""
}

# Main deployment flow
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║        HomeRack Production Deployment to PostgreSQL       ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Load environment
    load_env

    # Confirm deployment
    if [ "$FORCE" = false ]; then
        echo ""
        log_warn "This will deploy HomeRack to production with PostgreSQL"
        read -p "Continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi

    # Start PostgreSQL
    start_postgres

    # Apply migrations
    apply_migrations

    # Migrate data if requested
    if [ "$SKIP_MIGRATION" = false ]; then
        migrate_data
    fi

    # Stop here if migrate-only
    if [ "$MIGRATE_ONLY" = true ]; then
        log_info "Migration completed. Skipping service deployment."
        exit 0
    fi

    # Deploy services
    deploy_services

    # Verify deployment
    if verify_deployment; then
        show_info
    else
        log_error "Deployment verification failed"
        log_error "Check logs: docker-compose -f docker-compose.prod.yml logs"
        exit 1
    fi
}

# Run main
main
