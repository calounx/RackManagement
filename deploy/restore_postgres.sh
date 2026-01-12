#!/bin/bash

#############################################################################
# PostgreSQL Restore Script for HomeRack
#
# This script restores a HomeRack PostgreSQL database from backup.
#
# Usage:
#   ./restore_postgres.sh --backup-file <path_to_backup>
#
# Options:
#   --backup-file FILE       Path to backup file (required)
#   --container NAME         Container name (default: homerack-postgres)
#   --force                  Skip confirmation prompt
#
# Examples:
#   ./restore_postgres.sh --backup-file ./backups/homerack_20260112_120000.sql.gz
#   ./restore_postgres.sh --backup-file ./backups/homerack_20260112_120000.sql --force
#
#############################################################################

set -euo pipefail

# Default configuration
CONTAINER_NAME="homerack-postgres"
BACKUP_FILE=""
FORCE=false
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
        --backup-file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "PostgreSQL Restore Script for HomeRack"
            echo ""
            echo "Usage: $0 --backup-file <path_to_backup> [options]"
            echo ""
            echo "Options:"
            echo "  --backup-file FILE       Path to backup file (required)"
            echo "  --container NAME         Container name (default: homerack-postgres)"
            echo "  --force                  Skip confirmation prompt"
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

# Validate required parameters
if [ -z "${BACKUP_FILE}" ]; then
    log_error "Backup file is required. Use --backup-file option."
    exit 1
fi

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

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

# Determine if backup is compressed
IS_COMPRESSED=false
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    IS_COMPRESSED=true
fi

# Show restore information
log_info "PostgreSQL Restore Configuration:"
log_info "  Container: ${CONTAINER_NAME}"
log_info "  Database: ${DB_NAME}"
log_info "  Backup file: ${BACKUP_FILE}"
log_info "  Compressed: ${IS_COMPRESSED}"

# Verify backup file integrity (if compressed)
if [ "$IS_COMPRESSED" = true ]; then
    log_info "Verifying backup file integrity..."
    if gunzip -t "${BACKUP_FILE}" 2>/dev/null; then
        log_info "Backup file integrity verified"
    else
        log_error "Backup file is corrupted"
        exit 1
    fi
fi

# Warning and confirmation
log_warn "WARNING: This will REPLACE the current database with the backup!"
log_warn "All current data will be lost."
log_warn ""

if [ "$FORCE" = false ]; then
    read -p "Are you sure you want to continue? Type 'yes' to proceed: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
fi

# Create a pre-restore backup
log_info "Creating pre-restore backup of current database..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PRE_RESTORE_BACKUP="./pre_restore_backup_${TIMESTAMP}.sql.gz"

if docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${PRE_RESTORE_BACKUP}"; then
    log_info "Pre-restore backup created: ${PRE_RESTORE_BACKUP}"
else
    log_error "Failed to create pre-restore backup"
    exit 1
fi

# Perform restore
log_info "Starting database restore..."
START_TIME=$(date +%s)

# Drop and recreate database
log_info "Dropping and recreating database..."
docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" || {
    log_error "Failed to drop database"
    exit 1
}

docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};" || {
    log_error "Failed to create database"
    exit 1
}

# Restore from backup
log_info "Restoring data from backup..."
if [ "$IS_COMPRESSED" = true ]; then
    # Restore from compressed backup
    if gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1; then
        log_info "Database restored successfully"
    else
        log_error "Restore failed"
        log_error "You can restore the pre-restore backup using:"
        log_error "  gunzip -c ${PRE_RESTORE_BACKUP} | docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}"
        exit 1
    fi
else
    # Restore from uncompressed backup
    if docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${BACKUP_FILE}" > /dev/null 2>&1; then
        log_info "Database restored successfully"
    else
        log_error "Restore failed"
        log_error "You can restore the pre-restore backup using:"
        log_error "  gunzip -c ${PRE_RESTORE_BACKUP} | docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}"
        exit 1
    fi
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_info "Restore completed in ${DURATION} seconds"

# Verify restore
log_info "Verifying restore..."
TABLE_COUNT=$(docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

log_info "Tables in restored database: ${TABLE_COUNT}"

# Show database statistics
log_info "Database statistics:"
docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows
FROM pg_stat_user_tables
ORDER BY tablename;
" || log_warn "Could not retrieve database statistics"

log_info "Restore completed successfully!"
log_info ""
log_info "Pre-restore backup saved to: ${PRE_RESTORE_BACKUP}"
log_info "You can delete it once you verify the restore was successful."

exit 0
