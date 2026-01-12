#!/bin/bash
set -euo pipefail

##############################################################################
# HomeRack Update Script
# Updates the running application with minimal downtime
##############################################################################

REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
DEPLOY_DIR="/opt/homerack"
REPO_DIR="/home/calounx/repositories/homerack"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_info "Updating application on ${REMOTE_HOST}..."

# Sync files
log_info "Syncing updated files..."
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude 'frontend/node_modules' \
    --exclude 'frontend/dist' \
    --exclude 'backend/__pycache__' \
    --exclude 'backend/**/__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'backend/homerack.db' \
    --exclude 'backend/data' \
    --exclude 'backend/uploads' \
    "${REPO_DIR}/" \
    "${REMOTE_USER}@${REMOTE_HOST}:${DEPLOY_DIR}/"

# Rebuild and restart with zero downtime
log_info "Rebuilding containers..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml build"

log_info "Restarting containers with zero downtime..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml up -d --force-recreate --no-deps"

# Wait for health checks
log_info "Waiting for services to become healthy..."
sleep 10

for i in {1..30}; do
    if ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker exec homerack-backend curl -sf http://localhost:8000/health > /dev/null 2>&1"; then
        log_success "Backend is healthy"
        break
    fi
    [ $i -eq 30 ] && { log_error "Backend health check failed"; exit 1; }
    sleep 2
done

log_success "Update completed successfully!"
