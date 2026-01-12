#!/bin/bash
# HomeRack Backup Script
# Backs up database and uploaded files (brand logos)

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/homerack}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="homerack_backup_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if Docker is running
if ! docker ps &> /dev/null; then
    error "Docker is not running or not accessible"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting HomeRack backup..."
log "Backup location: $BACKUP_DIR/$BACKUP_NAME"

# Create temporary backup directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Backup database
log "Backing up database..."

# Check if using PostgreSQL or SQLite
if docker ps | grep -q homerack-postgres; then
    # PostgreSQL backup
    log "Detected PostgreSQL database"
    CONTAINER_NAME="homerack-postgres"
    DB_NAME="${POSTGRES_DB:-homerack}"
    DB_USER="${POSTGRES_USER:-homerack}"

    docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$TEMP_DIR/database.sql.gz"

    if [ $? -eq 0 ]; then
        log "PostgreSQL database backed up successfully"
    else
        error "PostgreSQL backup failed"
        exit 1
    fi
else
    # SQLite backup
    log "Detected SQLite database"
    CONTAINER_NAME="homerack-backend"
    DB_PATH="/app/data/homerack.db"

    # Check if database exists
    if docker exec "$CONTAINER_NAME" test -f "$DB_PATH" 2>/dev/null; then
        docker exec "$CONTAINER_NAME" sqlite3 "$DB_PATH" ".backup /tmp/homerack_backup.db"
        docker cp "$CONTAINER_NAME:/tmp/homerack_backup.db" "$TEMP_DIR/database.db"
        gzip "$TEMP_DIR/database.db"

        if [ $? -eq 0 ]; then
            log "SQLite database backed up successfully"
        else
            error "SQLite backup failed"
            exit 1
        fi
    else
        warning "SQLite database not found at $DB_PATH"
    fi
fi

# Backup uploaded files (brand logos, etc.)
log "Backing up uploaded files..."

UPLOADS_DIR="homerack-uploads"

# Check if uploads volume exists
if docker volume ls | grep -q "$UPLOADS_DIR"; then
    # Create temporary container to access volume
    docker run --rm \
        -v ${UPLOADS_DIR}:/data \
        -v ${TEMP_DIR}:/backup \
        alpine \
        tar czf /backup/uploads.tar.gz -C /data .

    if [ $? -eq 0 ]; then
        log "Uploaded files backed up successfully"
    else
        error "Uploads backup failed"
        exit 1
    fi
else
    warning "Uploads volume '$UPLOADS_DIR' not found"
fi

# Create backup metadata
log "Creating backup metadata..."

cat > "$TEMP_DIR/backup_info.txt" << EOF
HomeRack Backup Information
===========================
Backup Date: $(date)
Backup Name: $BACKUP_NAME
Hostname: $(hostname)
Docker Version: $(docker --version)

Contents:
- Database backup (compressed)
- Uploaded files (compressed)

Restore Instructions:
See PRODUCTION_SETUP.md for detailed restore procedures
EOF

# Compress all backup files
log "Compressing backup..."

cd "$TEMP_DIR"
tar czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" .

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    log "Backup compressed successfully (Size: $BACKUP_SIZE)"
else
    error "Backup compression failed"
    exit 1
fi

# Clean up old backups
log "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."

find "$BACKUP_DIR" -name "homerack_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "homerack_backup_*.tar.gz" -type f | wc -l)
log "Remaining backups: $REMAINING_BACKUPS"

# List recent backups
log "Recent backups:"
find "$BACKUP_DIR" -name "homerack_backup_*.tar.gz" -type f -printf "%T@ %Tc %p\n" | sort -n | tail -5 | cut -d' ' -f2-

log "Backup completed successfully!"
echo ""
log "Backup file: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
log "Size: $BACKUP_SIZE"

exit 0
