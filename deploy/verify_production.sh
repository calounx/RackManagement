#!/bin/bash
# HomeRack Production Deployment Verification Script
# Verifies all production features are working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST="${HOST:-lampadas.local}"
PORT="${PORT:-8080}"
BASE_URL="http://${HOST}:${PORT}"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

separator() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Check if jq is available
if ! command -v jq &> /dev/null; then
    warning "jq not installed - JSON parsing will be limited"
    HAS_JQ=false
else
    HAS_JQ=true
fi

separator "HomeRack Production Verification"

log "Target: ${BASE_URL}"
log "Starting verification..."
echo ""

# Test 1: Docker containers running
separator "1. Container Status"

REQUIRED_CONTAINERS=("homerack-backend" "homerack-frontend" "homerack-postgres" "homerack-redis")

for container in "${REQUIRED_CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        success "Container running: ${container}"
    else
        fail "Container not running: ${container}"
    fi
done

# Test 2: Check worker count
separator "2. Gunicorn Worker Count"

WORKER_COUNT=$(docker exec homerack-backend ps aux | grep -c "gunicorn.*worker" || echo "0")

if [ "$WORKER_COUNT" -ge 4 ]; then
    success "Gunicorn workers: ${WORKER_COUNT} (4+ workers detected)"
else
    fail "Gunicorn workers: ${WORKER_COUNT} (expected 4+)"
fi

# Test 3: Basic health check
separator "3. Basic Health Check"

HEALTH_RESPONSE=$(curl -s "${BASE_URL}/api/health" || echo "")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    success "Basic health check passed"
else
    fail "Basic health check failed"
fi

# Test 4: Liveness probe
separator "4. Liveness Probe (K8s-style)"

LIVENESS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/health/live")

if [ "$LIVENESS_CODE" = "200" ]; then
    success "Liveness probe: HTTP ${LIVENESS_CODE}"
else
    fail "Liveness probe: HTTP ${LIVENESS_CODE} (expected 200)"
fi

# Test 5: Readiness probe
separator "5. Readiness Probe (K8s-style)"

READINESS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/health/ready")

if [ "$READINESS_CODE" = "200" ]; then
    success "Readiness probe: HTTP ${READINESS_CODE}"
else
    fail "Readiness probe: HTTP ${READINESS_CODE} (expected 200)"
fi

# Test 6: Startup probe
separator "6. Startup Probe (K8s-style)"

STARTUP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/health/startup")

if [ "$STARTUP_CODE" = "200" ]; then
    success "Startup probe: HTTP ${STARTUP_CODE}"
else
    fail "Startup probe: HTTP ${STARTUP_CODE} (expected 200)"
fi

# Test 7: Detailed health check
separator "7. Detailed Health Check"

DETAILED_HEALTH=$(curl -s "${BASE_URL}/api/health/detailed" || echo "{}")

if [ "$HAS_JQ" = true ]; then
    OVERALL_STATUS=$(echo "$DETAILED_HEALTH" | jq -r '.status' 2>/dev/null || echo "unknown")

    if [ "$OVERALL_STATUS" = "healthy" ] || [ "$OVERALL_STATUS" = "degraded" ]; then
        success "Overall status: ${OVERALL_STATUS}"
    else
        fail "Overall status: ${OVERALL_STATUS} (expected healthy/degraded)"
    fi

    # Database check
    DB_STATUS=$(echo "$DETAILED_HEALTH" | jq -r '.checks.database.status' 2>/dev/null || echo "unknown")
    if [ "$DB_STATUS" = "up" ]; then
        DB_LATENCY=$(echo "$DETAILED_HEALTH" | jq -r '.checks.database.latency_ms' 2>/dev/null || echo "N/A")
        success "Database: ${DB_STATUS} (latency: ${DB_LATENCY}ms)"
    else
        fail "Database: ${DB_STATUS}"
    fi

    # Redis check
    REDIS_STATUS=$(echo "$DETAILED_HEALTH" | jq -r '.checks.redis.status' 2>/dev/null || echo "unknown")
    if [ "$REDIS_STATUS" = "up" ]; then
        success "Redis: ${REDIS_STATUS}"
    elif [ "$REDIS_STATUS" = "disabled" ]; then
        warning "Redis: ${REDIS_STATUS}"
    else
        fail "Redis: ${REDIS_STATUS}"
    fi

    # Disk check
    DISK_STATUS=$(echo "$DETAILED_HEALTH" | jq -r '.checks.disk.status' 2>/dev/null || echo "unknown")
    DISK_PERCENT=$(echo "$DETAILED_HEALTH" | jq -r '.checks.disk.percent_used' 2>/dev/null || echo "N/A")
    if [ "$DISK_STATUS" = "healthy" ]; then
        success "Disk: ${DISK_STATUS} (${DISK_PERCENT}% used)"
    elif [ "$DISK_STATUS" = "warning" ]; then
        warning "Disk: ${DISK_STATUS} (${DISK_PERCENT}% used)"
    else
        fail "Disk: ${DISK_STATUS} (${DISK_PERCENT}% used)"
    fi

    # Memory check
    MEMORY_STATUS=$(echo "$DETAILED_HEALTH" | jq -r '.checks.memory.status' 2>/dev/null || echo "unknown")
    MEMORY_PERCENT=$(echo "$DETAILED_HEALTH" | jq -r '.checks.memory.percent_used' 2>/dev/null || echo "N/A")
    if [ "$MEMORY_STATUS" = "healthy" ]; then
        success "Memory: ${MEMORY_STATUS} (${MEMORY_PERCENT}% used)"
    elif [ "$MEMORY_STATUS" = "warning" ]; then
        warning "Memory: ${MEMORY_STATUS} (${MEMORY_PERCENT}% used)"
    else
        fail "Memory: ${MEMORY_STATUS} (${MEMORY_PERCENT}% used)"
    fi
else
    if echo "$DETAILED_HEALTH" | grep -q "status"; then
        success "Detailed health check returned data"
    else
        fail "Detailed health check returned no data"
    fi
fi

# Test 8: PostgreSQL connection
separator "8. PostgreSQL Connection"

if docker exec homerack-postgres pg_isready -U homerack -d homerack > /dev/null 2>&1; then
    success "PostgreSQL is accepting connections"
else
    fail "PostgreSQL is not accepting connections"
fi

# Check database size
DB_SIZE=$(docker exec homerack-postgres psql -U homerack -d homerack -t -c \
    "SELECT pg_size_pretty(pg_database_size('homerack'));" 2>/dev/null | xargs || echo "N/A")
log "Database size: ${DB_SIZE}"

# Test 9: Redis connection
separator "9. Redis Connection"

if docker exec homerack-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    success "Redis is responding to PING"
else
    fail "Redis is not responding"
fi

# Check Redis info
REDIS_VERSION=$(docker exec homerack-redis redis-cli info server 2>/dev/null | grep "redis_version:" | cut -d: -f2 | tr -d '\r' || echo "N/A")
log "Redis version: ${REDIS_VERSION}"

# Test 10: API Documentation
separator "10. API Documentation"

DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs")

if [ "$DOCS_CODE" = "200" ]; then
    success "API documentation accessible: HTTP ${DOCS_CODE}"
else
    warning "API documentation: HTTP ${DOCS_CODE}"
fi

# Test 11: Security headers
separator "11. Security Headers"

HEADERS=$(curl -sI "${BASE_URL}/api/health" 2>/dev/null || echo "")

declare -A REQUIRED_HEADERS=(
    ["X-Content-Type-Options"]="nosniff"
    ["X-Frame-Options"]="SAMEORIGIN"
)

for header in "${!REQUIRED_HEADERS[@]}"; do
    if echo "$HEADERS" | grep -qi "${header}:"; then
        success "Security header present: ${header}"
    else
        warning "Security header missing: ${header}"
    fi
done

# Test 12: Monitoring stack (if running)
separator "12. Monitoring Stack (Optional)"

if docker ps --format '{{.Names}}' | grep -q "homerack-prometheus"; then
    PROM_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}:9090/-/healthy")
    if [ "$PROM_CODE" = "200" ]; then
        success "Prometheus is running: HTTP ${PROM_CODE}"
    else
        fail "Prometheus unhealthy: HTTP ${PROM_CODE}"
    fi
else
    warning "Prometheus not running (optional)"
fi

if docker ps --format '{{.Names}}' | grep -q "homerack-grafana"; then
    GRAFANA_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}:3000/api/health")
    if [ "$GRAFANA_CODE" = "200" ]; then
        success "Grafana is running: HTTP ${GRAFANA_CODE}"
    else
        fail "Grafana unhealthy: HTTP ${GRAFANA_CODE}"
    fi
else
    warning "Grafana not running (optional)"
fi

# Test 13: Container resource usage
separator "13. Container Resource Usage"

echo "Current resource usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
    $(docker ps --filter "name=homerack-" --format "{{.Names}}")

# Test 14: Backup directory
separator "14. Backup Configuration"

BACKUP_DIR="/var/backups/homerack"

if [ -d "$BACKUP_DIR" ]; then
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "homerack_backup_*.tar.gz" 2>/dev/null | wc -l || echo "0")
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        success "Backup directory exists with ${BACKUP_COUNT} backup(s)"
        LATEST_BACKUP=$(find "$BACKUP_DIR" -name "homerack_backup_*.tar.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- || echo "none")
        log "Latest backup: ${LATEST_BACKUP}"
    else
        warning "Backup directory exists but no backups found"
    fi
else
    warning "Backup directory not found: ${BACKUP_DIR}"
fi

# Summary
separator "Verification Summary"

TOTAL=$((PASSED + FAILED + WARNINGS))

echo "Results:"
echo -e "  ${GREEN}Passed:${NC}   ${PASSED}"
echo -e "  ${RED}Failed:${NC}   ${FAILED}"
echo -e "  ${YELLOW}Warnings:${NC} ${WARNINGS}"
echo -e "  Total:    ${TOTAL}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ Some optional features are not configured${NC}"
    fi
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
