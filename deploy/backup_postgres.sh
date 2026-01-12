#!/bin/bash

#############################################################################
# PostgreSQL Backup Script for HomeRack
#
# This script creates automated backups of the HomeRack PostgreSQL database
# with compression and retention policy.
#
# Usage:
#   ./backup_postgres.sh [options]
#
# Options:
#   --retention-days DAYS    Number of days to keep backups (default: 7)
#   --backup-dir DIR         Backup directory (default: ./backups)
#   --container NAME         Container name (default: homerack-postgres)
#   --compress               Enable gzip compression (default: enabled)
#   --no-compress            Disable compression
#
# Examples:
#   ./backup_postgres.sh
#   ./backup_postgres.sh --retention-days 14
#   ./backup_postgres.sh --backup-dir /mnt/backups
#
#############################################################################

set -euo pipefail

# Default configuration
RETENTION_DAYS=7
BACKUP_DIR="./backups"
CONTAINER_NAME="homerack-postgres"
COMPRESS=true
DB_NAME="homerack"
DB_USER="homerack_user"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --compress)
            COMPRESS=true
            shift
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --help)
            echo "PostgreSQL Backup Script for HomeRack"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --retention-days DAYS    Number of days to keep backups (default: 7)"
            echo "  --backup-dir DIR         Backup directory (default: ./backups)"
            echo "  --container NAME         Container name (default: homerack-postgres)"
            echo "  --compress               Enable gzip compression (default: enabled)"
            echo "  --no-compress            Disable compression"
            echo "  --help                   Show this help message"
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running"
    exit 1
fi

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_error "Container ${CONTAINER_NAME} is not running"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ "$COMPRESS" = true ]; then
    BACKUP_FILE="${BACKUP_DIR}/homerack_${TIMESTAMP}.sql.gz"
else
    BACKUP_FILE="${BACKUP_DIR}/homerack_${TIMESTAMP}.sql"
fi

log_info "Starting PostgreSQL backup..."
log_info "Container: ${CONTAINER_NAME}"
log_info "Database: ${DB_NAME}"
log_info "Backup file: ${BACKUP_FILE}"

# Perform backup
START_TIME=$(date +%s)

if [ "$COMPRESS" = true ]; then
    # Backup with compression
    if docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"; then
        log_info "Backup created successfully (compressed)"
    else
        log_error "Backup failed"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi
else
    # Backup without compression
    if docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" > "${BACKUP_FILE}"; then
        log_info "Backup created successfully"
    else
        log_error "Backup failed"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Get backup file size
if [ "$COMPRESS" = true ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
else
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
fi

log_info "Backup completed in ${DURATION} seconds"
log_info "Backup size: ${BACKUP_SIZE}"

# Clean up old backups based on retention policy
log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."

DELETED_COUNT=0
while IFS= read -r -d '' backup_file; do
    FILE_AGE_DAYS=$(( ($(date +%s) - $(stat -c %Y "${backup_file}")) / 86400 ))

    if [ "${FILE_AGE_DAYS}" -gt "${RETENTION_DAYS}" ]; then
        log_info "Deleting old backup: $(basename "${backup_file}") (${FILE_AGE_DAYS} days old)"
        rm -f "${backup_file}"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    fi
done < <(find "${BACKUP_DIR}" -name "homerack_*.sql*" -type f -print0)

if [ ${DELETED_COUNT} -eq 0 ]; then
    log_info "No old backups to delete"
else
    log_info "Deleted ${DELETED_COUNT} old backup(s)"
fi

# List current backups
log_info "Current backups:"
find "${BACKUP_DIR}" -name "homerack_*.sql*" -type f -exec ls -lh {} \; | awk '{print "  " $9 " (" $5 ")"}'

# Verify backup integrity (for compressed backups)
if [ "$COMPRESS" = true ]; then
    if gunzip -t "${BACKUP_FILE}" 2>/dev/null; then
        log_info "Backup file integrity verified"
    else
        log_warn "Backup file may be corrupted"
    fi
fi

log_info "Backup completed successfully!"
log_info "To restore this backup, run:"
if [ "$COMPRESS" = true ]; then
    echo "  gunzip -c ${BACKUP_FILE} | docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}"
else
    echo "  docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} < ${BACKUP_FILE}"
fi

exit 0
