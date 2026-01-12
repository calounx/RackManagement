#!/bin/bash
set -euo pipefail

##############################################################################
# HomeRack Monitoring Script
# Displays real-time health and status information
##############################################################################

REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
DEPLOY_DIR="/opt/homerack"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}=========================================="
echo "  HomeRack Application Monitor"
echo "  Host: ${REMOTE_HOST}"
echo "==========================================${NC}"
echo ""

# Check container status
echo -e "${BLUE}Container Status:${NC}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker ps --filter name=homerack --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
echo ""

# Check health endpoints
echo -e "${BLUE}Health Checks:${NC}"

# Backend health
if ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker exec homerack-backend curl -sf http://localhost:8000/health" > /dev/null 2>&1; then
    echo -e "  Backend: ${GREEN}HEALTHY${NC}"
    BACKEND_VERSION=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker exec homerack-backend curl -s http://localhost:8000/health 2>/dev/null | grep -o '\"version\":\"[^\"]*\"' | cut -d'\"' -f4")
    echo -e "    Version: ${BACKEND_VERSION}"
else
    echo -e "  Backend: ${RED}UNHEALTHY${NC}"
fi

# Frontend health
if ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker exec homerack-frontend curl -sf http://localhost:80/ > /dev/null 2>&1"; then
    echo -e "  Frontend: ${GREEN}HEALTHY${NC}"
else
    echo -e "  Frontend: ${RED}UNHEALTHY${NC}"
fi
echo ""

# Resource usage
echo -e "${BLUE}Resource Usage:${NC}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}' --filter name=homerack"
echo ""

# Volume information
echo -e "${BLUE}Data Volumes:${NC}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker volume ls --filter name=homerack --format 'table {{.Name}}\t{{.Driver}}'"
echo ""

# Recent logs
echo -e "${BLUE}Recent Backend Logs (last 10 lines):${NC}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker logs --tail 10 homerack-backend 2>&1" || echo "No logs available"
echo ""

echo -e "${BLUE}Recent Frontend Logs (last 10 lines):${NC}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "docker logs --tail 10 homerack-frontend 2>&1" || echo "No logs available"
echo ""

echo -e "${CYAN}==========================================${NC}"
echo -e "Access URLs:"
echo -e "  Frontend: ${GREEN}http://${REMOTE_HOST}:8080${NC}"
echo -e "  API Docs: ${GREEN}http://${REMOTE_HOST}:8080/docs${NC}"
echo -e "${CYAN}==========================================${NC}"
