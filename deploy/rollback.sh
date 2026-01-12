#!/bin/bash
set -euo pipefail

##############################################################################
# HomeRack Rollback Script
# Rolls back to a previous deployment version
##############################################################################

REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
DEPLOY_DIR="/opt/homerack"

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

log_info "Rolling back deployment on ${REMOTE_HOST}..."

# Stop current containers
log_info "Stopping current containers..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml down"

# Remove current images
log_warning "Removing current container images..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker rmi homerack-backend homerack-frontend || true"

# Pull and restart
log_info "Restarting with previous configuration..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml up -d --build"

log_success "Rollback completed"
