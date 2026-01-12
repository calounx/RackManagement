#!/bin/bash
set -euo pipefail

##############################################################################
# HomeRack Deployment Script
# Deploys the HomeRack application to lampadas.local
##############################################################################

# Configuration
REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
DEPLOY_DIR="/opt/homerack"
REPO_DIR="/home/calounx/repositories/homerack"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from repository root
if [[ ! -f "docker-compose.prod.yml" ]]; then
    log_error "Must run from repository root directory"
    exit 1
fi

log_info "Starting deployment to ${REMOTE_HOST}..."

# Step 1: Check SSH connectivity
log_info "Checking SSH connectivity..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${REMOTE_USER}@${REMOTE_HOST}" echo "SSH OK" > /dev/null 2>&1; then
    log_error "Cannot connect to ${REMOTE_HOST} via SSH"
    log_info "Ensure SSH keys are configured for passwordless access"
    exit 1
fi
log_success "SSH connectivity verified"

# Step 2: Check Docker availability on remote host
log_info "Checking Docker installation on remote host..."
if ! ssh "${REMOTE_USER}@${REMOTE_HOST}" "command -v docker > /dev/null 2>&1"; then
    log_warning "Docker not found on remote host. Installing Docker..."
    ssh "${REMOTE_USER}@${REMOTE_HOST}" 'bash -s' << 'ENDSSH'
        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh

        # Install Docker Compose plugin
        sudo apt-get update
        sudo apt-get install -y docker-compose-plugin
ENDSSH
    log_success "Docker installed successfully"
    log_warning "You may need to log out and back in for Docker group membership to take effect"
else
    log_success "Docker is already installed"
fi

# Step 3: Create deployment directory
log_info "Creating deployment directory..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p ${DEPLOY_DIR} && sudo chown ${REMOTE_USER}:${REMOTE_USER} ${DEPLOY_DIR}"
log_success "Deployment directory created: ${DEPLOY_DIR}"

# Step 4: Copy application files
log_info "Copying application files to remote host..."
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
log_success "Application files copied"

# Step 5: Create .env file on remote host
log_info "Creating production environment configuration..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cat > ${DEPLOY_DIR}/.env" << 'EOF'
# Production Environment Configuration
SECRET_KEY=$(openssl rand -hex 32)
APP_NAME=HomeRack API
VERSION=1.0.1
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
log_success "Environment configuration created"

# Step 6: Build and start containers
log_info "Building Docker images on remote host..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml build --no-cache"
log_success "Docker images built"

log_info "Starting application containers..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml up -d"
log_success "Application containers started"

# Step 7: Wait for services to be healthy
log_info "Waiting for services to become healthy..."
sleep 10

# Check backend health
log_info "Checking backend health..."
for i in {1..30}; do
    if ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker exec homerack-backend curl -sf http://localhost:8000/health > /dev/null 2>&1"; then
        log_success "Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Backend health check failed after 30 attempts"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml logs backend"
        exit 1
    fi
    sleep 2
done

# Check frontend health
log_info "Checking frontend health..."
for i in {1..30}; do
    if ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker exec homerack-frontend curl -sf http://localhost:80/ > /dev/null 2>&1"; then
        log_success "Frontend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Frontend health check failed after 30 attempts"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml logs frontend"
        exit 1
    fi
    sleep 2
done

# Step 8: Install systemd service for automatic startup
log_info "Installing systemd service..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo cp ${DEPLOY_DIR}/deploy/homerack.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable homerack.service"
log_success "Systemd service installed and enabled"

# Step 9: Display deployment information
log_success "Deployment completed successfully!"
echo ""
echo "=========================================="
echo "  HomeRack Deployment Summary"
echo "=========================================="
echo ""
echo "Application URLs:"
echo "  - Frontend: http://${REMOTE_HOST}:8080"
echo "  - Backend API: http://${REMOTE_HOST}:8080/api"
echo "  - API Documentation: http://${REMOTE_HOST}:8080/docs"
echo "  - Health Check: http://${REMOTE_HOST}:8080/health"
echo ""
echo "Management Commands (run on ${REMOTE_HOST}):"
echo "  - View logs: cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml logs -f"
echo "  - Restart: sudo systemctl restart homerack"
echo "  - Stop: sudo systemctl stop homerack"
echo "  - Status: sudo systemctl status homerack"
echo "  - View containers: docker ps"
echo ""
echo "Data Persistence:"
echo "  - Database: Docker volume 'homerack-data'"
echo "  - Uploads: Docker volume 'homerack-uploads'"
echo ""
echo "Deployment Directory: ${DEPLOY_DIR}"
echo "=========================================="
