#!/bin/bash

#############################################################################
# HomeRack Credential Rotation Script
#
# This script generates new secure credentials and updates production.
#
# Usage:
#   ./rotate_credentials.sh [options]
#
# Options:
#   --dry-run       Show what would be changed without making changes
#   --local-only    Only update local files, don't deploy to production
#   --no-restart    Update credentials but don't restart services
#
#############################################################################

set -euo pipefail

# Configuration
REMOTE_HOST="${REMOTE_HOST:-lampadas.local}"
REMOTE_USER="${REMOTE_USER:-calounx}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/homerack}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.generated"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Flags
DRY_RUN=false
LOCAL_ONLY=false
NO_RESTART=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --local-only)
            LOCAL_ONLY=true
            shift
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "HomeRack Credential Rotation"
echo "========================================="
echo ""

if $DRY_RUN; then
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

#############################################################################
# Step 1: Generate new credentials
#############################################################################

echo -e "${BLUE}[1/5] Generating new secure credentials...${NC}"

NEW_SECRET_KEY=$(openssl rand -hex 32)
NEW_JWT_SECRET_KEY=$(openssl rand -hex 32)
NEW_POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
NEW_REDIS_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
NEW_GRAFANA_PASSWORD=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)

echo -e "${GREEN}✓ Generated new credentials${NC}"
echo ""

#############################################################################
# Step 2: Create new .env.generated file
#############################################################################

echo -e "${BLUE}[2/5] Creating new environment file...${NC}"

ENV_CONTENT="# HomeRack Production Environment Configuration
# Generated: $(date -u)
# IMPORTANT: This file contains secrets - NEVER commit to git

# ==============================================
# APPLICATION SECURITY
# ==============================================
SECRET_KEY=${NEW_SECRET_KEY}
JWT_SECRET_KEY=${NEW_JWT_SECRET_KEY}

# ==============================================
# DATABASE
# ==============================================
POSTGRES_USER=homerack
POSTGRES_PASSWORD=${NEW_POSTGRES_PASSWORD}
POSTGRES_DB=homerack
DATABASE_URL=postgresql://homerack:${NEW_POSTGRES_PASSWORD}@postgres:5432/homerack

# ==============================================
# REDIS
# ==============================================
REDIS_PASSWORD=${NEW_REDIS_PASSWORD}
REDIS_URL=redis://:${NEW_REDIS_PASSWORD}@redis:6379/0

# ==============================================
# MONITORING
# ==============================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${NEW_GRAFANA_PASSWORD}

# ==============================================
# APPLICATION SETTINGS
# ==============================================
APP_NAME=HomeRack API
VERSION=1.0.1
DEBUG=false
ENVIRONMENT=production

# Worker Configuration
WORKERS=4
WORKER_TIMEOUT=120
GRACEFUL_TIMEOUT=30
MAX_REQUESTS=10000
MAX_REQUESTS_JITTER=1000
WORKER_CONNECTIONS=1000

# CORS Configuration (update with your domain)
CORS_ORIGINS=[\"http://lampadas.local\",\"http://lampadas.local:8080\"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Caching
CACHE_ENABLED=true

# Reliability
CIRCUIT_BREAKER_ENABLED=true
RETRY_ENABLED=true

# File Uploads
UPLOAD_DIR=/app/uploads
BRAND_LOGOS_DIR=/app/uploads/brand_logos
MAX_UPLOAD_SIZE=10485760

# Monitoring
PROMETHEUS_ENABLED=true

# External Integrations
NETBOX_ENABLED=false
SPEC_FETCH_ENABLED=true
"

if $DRY_RUN; then
    echo "Would write to: $ENV_FILE"
    echo "---"
    echo "$ENV_CONTENT" | head -30
    echo "..."
else
    echo "$ENV_CONTENT" > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo -e "${GREEN}✓ Created $ENV_FILE${NC}"
fi
echo ""

#############################################################################
# Step 3: Display credentials (for backup)
#############################################################################

echo -e "${BLUE}[3/5] New credentials (save these securely):${NC}"
echo ""
echo "  SECRET_KEY:          ${NEW_SECRET_KEY:0:16}...${NEW_SECRET_KEY: -8}"
echo "  JWT_SECRET_KEY:      ${NEW_JWT_SECRET_KEY:0:16}...${NEW_JWT_SECRET_KEY: -8}"
echo "  POSTGRES_PASSWORD:   ${NEW_POSTGRES_PASSWORD:0:8}...${NEW_POSTGRES_PASSWORD: -4}"
echo "  REDIS_PASSWORD:      ${NEW_REDIS_PASSWORD:0:8}...${NEW_REDIS_PASSWORD: -4}"
echo "  GRAFANA_PASSWORD:    ${NEW_GRAFANA_PASSWORD:0:4}...${NEW_GRAFANA_PASSWORD: -4}"
echo ""

if $LOCAL_ONLY; then
    echo -e "${YELLOW}LOCAL ONLY mode - skipping production deployment${NC}"
    echo ""
    echo -e "${GREEN}✓ Credential rotation complete (local only)${NC}"
    echo ""
    echo "To deploy to production, run:"
    echo "  scp $ENV_FILE $REMOTE_USER@$REMOTE_HOST:$DEPLOY_DIR/.env"
    echo "  ssh $REMOTE_USER@$REMOTE_HOST 'cd $DEPLOY_DIR && docker-compose down && docker-compose up -d'"
    exit 0
fi

#############################################################################
# Step 4: Deploy to production
#############################################################################

echo -e "${BLUE}[4/5] Deploying to production ($REMOTE_HOST)...${NC}"

if $DRY_RUN; then
    echo "Would copy $ENV_FILE to $REMOTE_USER@$REMOTE_HOST:$DEPLOY_DIR/.env"
else
    # Check if we can reach the remote host
    if ! ssh -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" "echo ok" &>/dev/null; then
        echo -e "${RED}Cannot connect to $REMOTE_HOST${NC}"
        echo "Please ensure:"
        echo "  1. The server is running"
        echo "  2. SSH access is configured"
        echo "  3. The host is reachable"
        echo ""
        echo "To deploy manually later:"
        echo "  scp $ENV_FILE $REMOTE_USER@$REMOTE_HOST:$DEPLOY_DIR/.env"
        exit 1
    fi

    # Copy the new env file
    scp "$ENV_FILE" "$REMOTE_USER@$REMOTE_HOST:$DEPLOY_DIR/.env"
    ssh "$REMOTE_USER@$REMOTE_HOST" "chmod 600 $DEPLOY_DIR/.env"
    echo -e "${GREEN}✓ Deployed new credentials to production${NC}"
fi
echo ""

#############################################################################
# Step 5: Restart services
#############################################################################

if $NO_RESTART; then
    echo -e "${YELLOW}NO RESTART mode - skipping service restart${NC}"
    echo ""
    echo "To restart services manually:"
    echo "  ssh $REMOTE_USER@$REMOTE_HOST 'cd $DEPLOY_DIR && docker-compose down && docker-compose up -d'"
else
    echo -e "${BLUE}[5/5] Restarting production services...${NC}"

    if $DRY_RUN; then
        echo "Would restart Docker containers on $REMOTE_HOST"
    else
        ssh "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
cd /opt/homerack

echo "Stopping services..."
docker-compose down 2>/dev/null || true

echo "Starting services with new credentials..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking service health..."
docker-compose ps
ENDSSH
        echo -e "${GREEN}✓ Services restarted${NC}"
    fi
fi
echo ""

#############################################################################
# Verification
#############################################################################

echo -e "${BLUE}Verifying deployment...${NC}"

if ! $DRY_RUN && ! $LOCAL_ONLY; then
    # Wait a moment for services to fully start
    sleep 5

    # Check health endpoint
    if curl -sf "http://$REMOTE_HOST/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API health check passed${NC}"
    else
        echo -e "${YELLOW}⚠ API health check failed - services may still be starting${NC}"
        echo "  Check manually: curl http://$REMOTE_HOST/api/health"
    fi
fi
echo ""

#############################################################################
# Summary
#############################################################################

echo "========================================="
echo -e "${GREEN}Credential Rotation Complete${NC}"
echo "========================================="
echo ""
echo "Actions taken:"
if ! $DRY_RUN; then
    echo "  ✓ Generated new secure credentials"
    echo "  ✓ Created $ENV_FILE"
    if ! $LOCAL_ONLY; then
        echo "  ✓ Deployed to $REMOTE_HOST"
        if ! $NO_RESTART; then
            echo "  ✓ Restarted production services"
        fi
    fi
else
    echo "  (Dry run - no changes made)"
fi
echo ""
echo -e "${YELLOW}IMPORTANT: The old credentials in git history are still exposed.${NC}"
echo "Consider using BFG Repo-Cleaner to remove them from history if needed."
echo ""
echo "To purge from git history (DESTRUCTIVE):"
echo "  1. Install BFG: brew install bfg"
echo "  2. Run: bfg --delete-files .env.generated"
echo "  3. Run: git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "  4. Force push: git push --force"
echo ""
