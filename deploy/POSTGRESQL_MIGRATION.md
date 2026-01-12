# PostgreSQL Migration Guide

This guide walks you through migrating HomeRack from SQLite to PostgreSQL for production deployment.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Steps](#migration-steps)
4. [Backup and Restore](#backup-and-restore)
5. [Troubleshooting](#troubleshooting)
6. [Rollback Procedure](#rollback-procedure)

## Overview

HomeRack now supports both SQLite (for development) and PostgreSQL (for production). This guide covers:

- Migrating existing SQLite data to PostgreSQL
- Configuring PostgreSQL with connection pooling
- Setting up automated backups
- Production deployment on lampadas.local

## Prerequisites

### System Requirements

- Docker and Docker Compose installed
- At least 2GB free disk space
- Network connectivity to lampadas.local

### Before You Begin

1. **Backup your current SQLite database:**
   ```bash
   cp backend/app/data/homerack.db backend/app/data/homerack.db.backup
   ```

2. **Review current data:**
   ```bash
   sqlite3 backend/app/data/homerack.db ".tables"
   ```

## Migration Steps

### Step 1: Configure Production Environment

1. **Create production environment file:**
   ```bash
   cp .env.production.example .env.production
   ```

2. **Generate secure passwords:**
   ```bash
   # Generate PostgreSQL password
   openssl rand -base64 32

   # Generate SECRET_KEY
   openssl rand -hex 32

   # Generate JWT_SECRET_KEY
   openssl rand -hex 32
   ```

3. **Update `.env.production` with generated values:**
   ```env
   POSTGRES_PASSWORD=your_generated_password_here
   SECRET_KEY=your_generated_secret_key_here
   JWT_SECRET_KEY=your_generated_jwt_secret_here
   ```

### Step 2: Deploy PostgreSQL with Docker Compose

1. **Start PostgreSQL service:**
   ```bash
   cd /home/calounx/repositories/homerack
   docker-compose -f docker-compose.prod.yml up -d postgres
   ```

2. **Wait for PostgreSQL to be ready:**
   ```bash
   docker logs -f homerack-postgres
   # Wait until you see: "database system is ready to accept connections"
   # Press Ctrl+C to exit logs
   ```

3. **Verify PostgreSQL is running:**
   ```bash
   docker exec homerack-postgres pg_isready -U homerack_user -d homerack
   # Should output: homerack-postgres:5432 - accepting connections
   ```

### Step 3: Apply Database Migrations

1. **Install Python dependencies (if not already installed):**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Apply Alembic migrations to PostgreSQL:**
   ```bash
   # Set PostgreSQL connection for migrations
   export DATABASE_URL="postgresql://homerack_user:YOUR_PASSWORD@localhost:5432/homerack"

   # Run migrations
   alembic upgrade head
   ```

3. **Verify migrations were applied:**
   ```bash
   docker exec homerack-postgres psql -U homerack_user -d homerack -c "\dt"
   # Should list all tables
   ```

### Step 4: Migrate Data from SQLite to PostgreSQL

1. **Run the migration script:**
   ```bash
   cd backend
   python scripts/migrate_to_postgres.py \
     --sqlite-path ./app/data/homerack.db \
     --postgres-url "postgresql://homerack_user:YOUR_PASSWORD@localhost:5432/homerack"
   ```

2. **Review migration output:**
   - Script will show migration plan
   - Prompt for confirmation
   - Display progress for each table
   - Verify row counts match

3. **Expected output:**
   ```
   Migration completed in X seconds
   Total rows migrated: XXX
   ✓ All data verified successfully!
   ```

### Step 5: Deploy Full Stack

1. **Stop any running containers:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Start all services:**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
   ```

3. **Monitor startup:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

4. **Verify services are healthy:**
   ```bash
   docker ps
   # All containers should show "healthy" status
   ```

### Step 6: Verify Deployment

1. **Check database connection:**
   ```bash
   curl http://lampadas.local:8080/health
   ```

2. **Expected response:**
   ```json
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

3. **Test the application:**
   - Open http://lampadas.local:8080 in browser
   - Verify all data is present
   - Test creating/editing racks and devices
   - Run thermal analysis
   - Test optimization features

## Backup and Restore

### Automated Backups

1. **Create backup manually:**
   ```bash
   cd deploy
   ./backup_postgres.sh
   ```

2. **Configure automated daily backups (cron):**
   ```bash
   # Edit crontab
   crontab -e

   # Add daily backup at 2 AM with 7-day retention
   0 2 * * * cd /home/calounx/repositories/homerack/deploy && ./backup_postgres.sh --retention-days 7
   ```

3. **Backup with custom settings:**
   ```bash
   # Keep backups for 14 days
   ./backup_postgres.sh --retention-days 14

   # Store backups in specific directory
   ./backup_postgres.sh --backup-dir /mnt/backup/homerack
   ```

### Restore from Backup

1. **List available backups:**
   ```bash
   ls -lh deploy/backups/
   ```

2. **Restore a backup:**
   ```bash
   cd deploy
   ./restore_postgres.sh --backup-file ./backups/homerack_20260112_120000.sql.gz
   ```

3. **Force restore (skip confirmation):**
   ```bash
   ./restore_postgres.sh --backup-file ./backups/homerack_20260112_120000.sql.gz --force
   ```

## Troubleshooting

### Connection Issues

**Problem:** Backend can't connect to PostgreSQL

```bash
# Check PostgreSQL logs
docker logs homerack-postgres

# Check if PostgreSQL is accepting connections
docker exec homerack-postgres pg_isready -U homerack_user -d homerack

# Verify network connectivity
docker network inspect homerack-network
```

**Solution:**
- Ensure PostgreSQL container is running and healthy
- Verify DATABASE_URL in environment variables
- Check firewall rules

### Migration Failed

**Problem:** Data migration script failed

```bash
# Check if PostgreSQL has any data
docker exec homerack-postgres psql -U homerack_user -d homerack -c "SELECT COUNT(*) FROM racks;"
```

**Solution:**
- Review migration script output for errors
- Verify Alembic migrations were applied
- Ensure source SQLite database is not corrupted
- Try migrating tables individually

### Pool Exhaustion

**Problem:** Connection pool exhausted errors

```bash
# Check pool statistics
curl http://lampadas.local:8080/health | jq '.pool_info'
```

**Solution:**
- Increase `DB_POOL_SIZE` in environment
- Increase `DB_MAX_OVERFLOW`
- Check for connection leaks in application
- Review slow queries

### Slow Queries

**Problem:** Database queries are slow

```bash
# Enable query logging
docker exec homerack-postgres psql -U homerack_user -d homerack -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker restart homerack-postgres

# View slow queries
docker logs homerack-postgres | grep "duration:"
```

**Solution:**
- Add indexes on frequently queried columns
- Review query execution plans
- Increase PostgreSQL shared_buffers
- Optimize application queries

## Rollback Procedure

If you need to rollback to SQLite:

### Option 1: Rollback with Docker Compose

1. **Stop all containers:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Update environment to use SQLite:**
   ```bash
   # Edit docker-compose.prod.yml or use SQLite-specific compose file
   docker-compose -f docker-compose.yml up -d
   ```

3. **Restore SQLite backup:**
   ```bash
   cp backend/app/data/homerack.db.backup backend/app/data/homerack.db
   ```

### Option 2: Keep Both Databases

You can run both SQLite (development) and PostgreSQL (production):

**Development (SQLite):**
```bash
cd backend
export DATABASE_URL="sqlite:///./homerack.db"
uvicorn app.main:app --reload
```

**Production (PostgreSQL):**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Performance Tuning

### PostgreSQL Configuration

For production workloads, consider tuning PostgreSQL:

```bash
# Access PostgreSQL container
docker exec -it homerack-postgres bash

# Edit postgresql.conf
vi /var/lib/postgresql/data/postgresql.conf

# Recommended settings for HomeRack (adjust based on your system):
# shared_buffers = 256MB
# effective_cache_size = 1GB
# maintenance_work_mem = 64MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1
# effective_io_concurrency = 200
# work_mem = 4MB
# min_wal_size = 1GB
# max_wal_size = 4GB

# Restart PostgreSQL
docker restart homerack-postgres
```

### Connection Pool Tuning

Adjust based on your workload:

```env
# Conservative (low traffic)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5

# Moderate (medium traffic)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Aggressive (high traffic)
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
```

## Monitoring

### Check Database Size

```bash
docker exec homerack-postgres psql -U homerack_user -d homerack -c "
SELECT
    pg_size_pretty(pg_database_size('homerack')) as db_size;
"
```

### Check Table Sizes

```bash
docker exec homerack-postgres psql -U homerack_user -d homerack -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Check Connection Stats

```bash
docker exec homerack-postgres psql -U homerack_user -d homerack -c "
SELECT
    datname,
    numbackends as connections,
    xact_commit as commits,
    xact_rollback as rollbacks,
    blks_read as disk_reads,
    blks_hit as cache_hits
FROM pg_stat_database
WHERE datname = 'homerack';
"
```

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Support

If you encounter issues:

1. Check application logs: `docker logs homerack-backend`
2. Check PostgreSQL logs: `docker logs homerack-postgres`
3. Review this troubleshooting guide
4. Check GitHub issues
5. Contact support team

---

**Last Updated:** 2026-01-12
**Version:** 1.0.1
