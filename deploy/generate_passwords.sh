#!/bin/bash
# Generate Strong Passwords for HomeRack Production Deployment
# This script generates cryptographically secure passwords and keys

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HomeRack Password Generator${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: openssl is not installed${NC}"
    exit 1
fi

# Generate passwords
echo -e "${BLUE}Generating secure passwords and keys...${NC}"
echo ""

SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
GRAFANA_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)

# Display generated values
echo -e "${GREEN}Generated Values:${NC}"
echo "=========================================="
echo ""
echo "Copy these to your .env file:"
echo ""
echo "# Application Security"
echo "SECRET_KEY=${SECRET_KEY}"
echo "JWT_SECRET_KEY=${JWT_SECRET_KEY}"
echo ""
echo "# Database"
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
echo "DATABASE_URL=postgresql://homerack:${POSTGRES_PASSWORD}@postgres:5432/homerack"
echo ""
echo "# Redis"
echo "REDIS_PASSWORD=${REDIS_PASSWORD}"
echo "REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0"
echo ""
echo "# Monitoring"
echo "GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}"
echo ""
echo "=========================================="
echo ""

# Optional: Write to file
read -p "Save to .env.generated file? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > .env.generated << EOF
# HomeRack Production Environment Configuration
# Generated: $(date)
# IMPORTANT: Review and customize before deploying

# ==============================================
# APPLICATION SECURITY
# ==============================================
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# ==============================================
# DATABASE
# ==============================================
POSTGRES_USER=homerack
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=homerack
DATABASE_URL=postgresql://homerack:${POSTGRES_PASSWORD}@postgres:5432/homerack

# ==============================================
# REDIS
# ==============================================
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# ==============================================
# MONITORING
# ==============================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

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
CORS_ORIGINS=["http://lampadas.local","http://lampadas.local:8080"]

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
EOF

    echo -e "${GREEN}Configuration saved to .env.generated${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review .env.generated"
    echo "2. Customize CORS_ORIGINS and other settings"
    echo "3. Rename to .env: mv .env.generated .env"
    echo "4. Deploy: ./deploy/deploy.sh"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Never commit .env to version control!${NC}"
fi

echo ""
echo -e "${GREEN}Password generation complete!${NC}"
