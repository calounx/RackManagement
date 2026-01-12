# PostgreSQL Quick Start Guide

Quick reference for deploying and managing HomeRack with PostgreSQL.

## Initial Setup (5 minutes)

```bash
# 1. Copy production environment template
cd /home/calounx/repositories/homerack
cp .env.production.example .env.production

# 2. Generate secure passwords
openssl rand -base64 32  # Copy for POSTGRES_PASSWORD
openssl rand -hex 32     # Copy for SECRET_KEY
openssl rand -hex 32     # Copy for JWT_SECRET_KEY

# 3. Edit .env.production and paste the generated values
nano .env.production

# 4. Deploy to production
cd deploy
./deploy_production.sh
```

That's it! HomeRack will be available at http://lampadas.local:8080

## Daily Operations

### Backup Database

```bash
cd /home/calounx/repositories/homerack/deploy
./backup_postgres.sh
```

### Restore Database

```bash
# List backups
ls -lh backups/

# Restore
./restore_postgres.sh --backup-file backups/homerack_20260112_120000.sql.gz
```

### View Logs

```bash
# All services
docker-compose -f /home/calounx/repositories/homerack/docker-compose.prod.yml logs -f

# Backend only
docker logs -f homerack-backend
```

### Check Status

```bash
# Service status
docker ps

# Health check
curl http://lampadas.local:8080/health
```

### Restart Services

```bash
cd /home/calounx/repositories/homerack
docker-compose -f docker-compose.prod.yml restart
```

## Automated Backups

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /home/calounx/repositories/homerack/deploy && ./backup_postgres.sh --retention-days 7
```

## Useful PostgreSQL Commands

```bash
# Connect to database
docker exec -it homerack-postgres psql -U homerack_user -d homerack

# List tables
\dt

# Check database size
SELECT pg_size_pretty(pg_database_size('homerack'));

# Exit
\q
```

## Troubleshooting

### Service won't start

```bash
docker logs homerack-postgres
docker logs homerack-backend
```

### Reset everything

```bash
cd /home/calounx/repositories/homerack
docker-compose -f docker-compose.prod.yml down -v
./deploy/deploy_production.sh
```

## More Information

- Complete migration guide: [POSTGRESQL_MIGRATION.md](./POSTGRESQL_MIGRATION.md)
- Deployment scripts: [README.md](./README.md)
- General deployment: [DEPLOYMENT_SUCCESS.md](./DEPLOYMENT_SUCCESS.md)
