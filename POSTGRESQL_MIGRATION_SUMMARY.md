# PostgreSQL Migration Summary

Complete migration of HomeRack from SQLite to PostgreSQL with production-ready configuration.

## Overview

HomeRack now supports both SQLite (development) and PostgreSQL (production) with:

- Environment-based database selection
- Connection pooling and retry logic
- Automated backup and restore
- Complete data migration tools
- Production deployment scripts

## What Was Changed

### 1. Backend Configuration

#### `/home/calounx/repositories/homerack/backend/app/config.py`
- Added `DB_TYPE` setting (sqlite or postgresql)
- Added connection pool settings:
  - `DB_POOL_SIZE` (default: 20)
  - `DB_MAX_OVERFLOW` (default: 10)
  - `DB_POOL_TIMEOUT` (default: 30)
  - `DB_POOL_RECYCLE` (default: 3600)
  - `DB_POOL_PRE_PING` (default: true)
- Added connection retry settings:
  - `DB_CONNECT_RETRY_MAX_ATTEMPTS` (default: 5)
  - `DB_CONNECT_RETRY_DELAY` (default: 2)

#### `/home/calounx/repositories/homerack/backend/app/database.py`
- Automatic database type detection (SQLite vs PostgreSQL)
- PostgreSQL connection pooling with QueuePool
- SQLite uses NullPool (no pooling)
- Connection retry logic with exponential backoff
- Health check function with pool statistics
- Event listeners for connection lifecycle (PostgreSQL)

#### `/home/calounx/repositories/homerack/backend/requirements.txt`
- Added: `psycopg2-binary==2.9.9` (PostgreSQL driver)

#### `/home/calounx/repositories/homerack/backend/.env.example`
- Complete PostgreSQL configuration section
- Connection pool settings
- Database retry configuration
- Example connection strings for both databases

### 2. Docker Configuration

#### `/home/calounx/repositories/homerack/docker-compose.prod.yml`
- Added PostgreSQL service:
  - Image: `postgres:15-alpine`
  - Container: `homerack-postgres`
  - Persistent volume: `postgres-data`
  - Health check with `pg_isready`
  - Port 5432 exposed for backups
- Updated backend service:
  - Depends on PostgreSQL health check
  - PostgreSQL connection URL
  - Connection pool environment variables
  - Increased startup time for DB connection retries
- Added persistent volume for PostgreSQL data

#### `/home/calounx/repositories/homerack/.env.production.example`
- Production environment template
- Secure password placeholders
- Instructions for generating secrets
- PostgreSQL-specific configuration

### 3. Migration Tools

#### `/home/calounx/repositories/homerack/backend/scripts/migrate_to_postgres.py`
Complete SQLite to PostgreSQL migration script:
- Automatic backup of SQLite database
- Table-ordered migration (respects foreign keys)
- Batch processing for performance
- Integrity error handling
- Sequence reset after import
- Data verification with row counts
- Dry-run mode
- Progress reporting

#### `/home/calounx/repositories/homerack/deploy/backup_postgres.sh`
PostgreSQL backup script:
- Automatic gzip compression
- Configurable retention policy (default: 7 days)
- Backup integrity verification
- Size reporting
- Old backup cleanup
- Restore instructions

#### `/home/calounx/repositories/homerack/deploy/restore_postgres.sh`
PostgreSQL restore script:
- Pre-restore backup creation
- Database drop and recreate
- Compressed backup support
- Verification after restore
- Rollback instructions if failed
- Safety confirmations

#### `/home/calounx/repositories/homerack/deploy/deploy_production.sh`
Automated production deployment:
- Prerequisites validation
- Environment configuration check
- PostgreSQL startup and health check
- Alembic migrations
- Data migration from SQLite
- Service deployment
- Deployment verification
- Multiple deployment modes (full, skip-migration, migrate-only)

### 4. Documentation

#### `/home/calounx/repositories/homerack/deploy/POSTGRESQL_MIGRATION.md`
Complete migration guide covering:
- Prerequisites and system requirements
- Step-by-step migration instructions
- Backup and restore procedures
- Troubleshooting common issues
- Performance tuning recommendations
- Monitoring and maintenance
- Rollback procedures

#### `/home/calounx/repositories/homerack/deploy/POSTGRESQL_QUICKSTART.md`
Quick reference guide:
- 5-minute setup instructions
- Daily operations cheatsheet
- Common commands
- Troubleshooting tips

## Database Features

### Connection Pooling

PostgreSQL uses QueuePool with:
- Pool size: 20 connections
- Max overflow: 10 additional connections
- Pool timeout: 30 seconds
- Connection recycle: 3600 seconds (1 hour)
- Pre-ping: Test connections before use

### Connection Retry

Automatic retry on connection failure:
- Max attempts: 5
- Delay: 2 seconds between retries
- Exponential backoff
- Detailed logging

### Health Monitoring

Health check endpoint provides:
- Database type (sqlite/postgresql)
- Query response time
- Pool statistics (PostgreSQL only):
  - Total pool size
  - Checked in connections
  - Checked out connections
  - Overflow connections

## Usage

### Development (SQLite)

```bash
cd backend
export DATABASE_URL="sqlite:///./homerack.db"
uvicorn app.main:app --reload
```

### Production (PostgreSQL)

```bash
cd /home/calounx/repositories/homerack
cp .env.production.example .env.production
# Edit .env.production with secure passwords
cd deploy
./deploy_production.sh
```

### Migration

```bash
cd backend
python scripts/migrate_to_postgres.py \
  --sqlite-path ./homerack.db \
  --postgres-url "postgresql://user:pass@localhost:5432/homerack"
```

### Backup

```bash
cd deploy
./backup_postgres.sh --retention-days 7
```

### Restore

```bash
cd deploy
./restore_postgres.sh --backup-file backups/homerack_20260112_120000.sql.gz
```

## File Structure

```
homerack/
├── backend/
│   ├── app/
│   │   ├── config.py              # Updated with PostgreSQL settings
│   │   └── database.py            # Connection pooling and retry logic
│   ├── scripts/
│   │   └── migrate_to_postgres.py # SQLite to PostgreSQL migration
│   ├── requirements.txt           # Added psycopg2-binary
│   └── .env.example               # PostgreSQL configuration
├── deploy/
│   ├── backup_postgres.sh         # Backup script
│   ├── restore_postgres.sh        # Restore script
│   ├── deploy_production.sh       # Automated deployment
│   ├── POSTGRESQL_MIGRATION.md    # Complete migration guide
│   └── POSTGRESQL_QUICKSTART.md   # Quick reference
├── docker-compose.prod.yml        # PostgreSQL service added
└── .env.production.example        # Production configuration template
```

## Environment Variables

### Database Configuration

```env
# Database Type
DB_TYPE=postgresql  # or sqlite for development

# Connection URL
DATABASE_URL=postgresql://homerack_user:password@postgres:5432/homerack

# Connection Pool (PostgreSQL only)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Connection Retry
DB_CONNECT_RETRY_MAX_ATTEMPTS=5
DB_CONNECT_RETRY_DELAY=2

# Debug
DB_ECHO=false
```

## Testing

### Verify PostgreSQL Connection

```bash
# Check health endpoint
curl http://lampadas.local:8080/health | jq

# Expected response:
{
  "status": "healthy",
  "database_type": "postgresql",
  "query_time_ms": 2.5,
  "pool_info": {
    "pool_size": 20,
    "checked_in": 19,
    "checked_out": 1,
    "overflow": 0,
    "total_connections": 20
  }
}
```

### Verify Data Migration

```bash
# Connect to PostgreSQL
docker exec -it homerack-postgres psql -U homerack_user -d homerack

# Check row counts
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY tablename;

# Exit
\q
```

## Performance Considerations

### Connection Pool Sizing

- **Low traffic**: Pool size 10, overflow 5
- **Medium traffic**: Pool size 20, overflow 10 (default)
- **High traffic**: Pool size 50, overflow 20

### PostgreSQL Tuning

For production workloads, consider tuning:
- `shared_buffers = 256MB`
- `effective_cache_size = 1GB`
- `work_mem = 4MB`
- `maintenance_work_mem = 64MB`

See [POSTGRESQL_MIGRATION.md](deploy/POSTGRESQL_MIGRATION.md) for complete tuning guide.

## Monitoring

### Connection Pool Statistics

```bash
curl http://lampadas.local:8080/health | jq '.pool_info'
```

### Database Size

```bash
docker exec homerack-postgres psql -U homerack_user -d homerack -c "
SELECT pg_size_pretty(pg_database_size('homerack')) as db_size;
"
```

### Active Connections

```bash
docker exec homerack-postgres psql -U homerack_user -d homerack -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'homerack';
"
```

## Backup Strategy

### Manual Backups

```bash
./deploy/backup_postgres.sh
```

### Automated Daily Backups

```bash
# Add to crontab
crontab -e

# Daily at 2 AM, keep 7 days
0 2 * * * cd /home/calounx/repositories/homerack/deploy && ./backup_postgres.sh --retention-days 7
```

### Backup Retention

- Default: 7 days
- Configurable via `--retention-days` flag
- Automatic cleanup of old backups
- Backups stored in `deploy/backups/`

## Rollback

### To SQLite

1. Stop services:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. Use SQLite configuration:
   ```bash
   export DATABASE_URL="sqlite:///./homerack.db"
   ```

3. Restore SQLite backup:
   ```bash
   cp backend/homerack.db.backup backend/homerack.db
   ```

### To Previous PostgreSQL State

```bash
./deploy/restore_postgres.sh --backup-file backups/homerack_TIMESTAMP.sql.gz
```

## Security Best Practices

1. **Never commit .env.production** - Contains sensitive credentials
2. **Use strong passwords** - Generate with `openssl rand -base64 32`
3. **Restrict PostgreSQL access** - Firewall rules if exposed externally
4. **Regular backups** - Automated daily backups
5. **Monitor logs** - Check for unauthorized access
6. **Update regularly** - Keep Docker images and dependencies updated

## Support

### Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker logs -f homerack-backend

# PostgreSQL only
docker logs -f homerack-postgres
```

### Common Issues

1. **Connection refused**: Check PostgreSQL is running
2. **Pool exhausted**: Increase pool size
3. **Slow queries**: Add indexes, tune PostgreSQL
4. **Migration failed**: Check Alembic migrations applied

See [POSTGRESQL_MIGRATION.md](deploy/POSTGRESQL_MIGRATION.md) for detailed troubleshooting.

## Success Criteria

All criteria met:

- ✅ PostgreSQL running in Docker
- ✅ Connection pooling configured (size: 20, overflow: 10)
- ✅ All migrations work with PostgreSQL
- ✅ Data migration script working
- ✅ Backup script functional (with compression and retention)
- ✅ Restore script functional (with pre-restore backup)
- ✅ Automated deployment script
- ✅ Backward compatibility with SQLite preserved
- ✅ Comprehensive documentation
- ✅ Health check with pool monitoring
- ✅ Connection retry logic implemented

## Next Steps

1. **Deploy to production:**
   ```bash
   cd /home/calounx/repositories/homerack/deploy
   ./deploy_production.sh
   ```

2. **Set up automated backups:**
   ```bash
   crontab -e
   # Add: 0 2 * * * cd /home/calounx/repositories/homerack/deploy && ./backup_postgres.sh
   ```

3. **Monitor performance:**
   ```bash
   curl http://lampadas.local:8080/health
   ```

4. **Review and tune:**
   - Monitor connection pool usage
   - Tune PostgreSQL settings if needed
   - Adjust pool size based on traffic

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)

---

**Migration Date:** 2026-01-12
**Version:** 1.0.1
**PostgreSQL Version:** 15
**Database Driver:** psycopg2-binary 2.9.9
