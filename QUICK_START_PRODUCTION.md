# HomeRack Production Deployment - Quick Start Guide

Fast-track guide to deploy HomeRack with production-grade features.

## Overview

This guide gets you from zero to production in ~15 minutes with:
- 4 Gunicorn workers for high performance
- PostgreSQL database for reliability
- Redis caching for speed
- Comprehensive monitoring (Prometheus + Grafana)
- Automated backups
- Security hardening
- HTTPS support (prepared, optional)

## Prerequisites

- Docker and Docker Compose installed
- 4GB+ RAM, 2+ CPU cores
- Network access to lampadas.local (or your server)

## 5-Minute Setup

### Step 1: Generate Configuration (1 min)

```bash
cd /home/calounx/repositories/homerack

# Generate secure passwords
./deploy/generate_passwords.sh

# When prompted, save to .env.generated
# Review the file
cat .env.generated

# Apply configuration
mv .env.generated .env
```

### Step 2: Deploy Application (3 min)

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.prod.yml ps
```

### Step 3: Verify Deployment (1 min)

```bash
# Run verification script
./deploy/verify_production.sh

# Manual checks
curl http://lampadas.local:8080/api/health/detailed
curl http://lampadas.local:8080/docs
```

## 10-Minute Full Setup (with Monitoring & Backups)

Follow Steps 1-3 above, then:

### Step 4: Start Monitoring Stack (2 min)

```bash
# Start Prometheus + Grafana
./deploy/monitoring.sh start

# Check status
./deploy/monitoring.sh status
./deploy/monitoring.sh urls
```

Access monitoring:
- **Grafana**: http://lampadas.local:3000 (admin/[generated-password])
- **Prometheus**: http://lampadas.local:9090

### Step 5: Configure Backups (3 min)

```bash
# Test backup
sudo ./deploy/backup.sh

# Configure daily automated backups (2 AM)
sudo crontab -e

# Add this line:
0 2 * * * /home/calounx/repositories/homerack/deploy/backup.sh >> /var/log/homerack-backup.log 2>&1
```

Backup location: `/var/backups/homerack/`

## Access Points

After deployment:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://lampadas.local:8080 | - |
| **API** | http://lampadas.local:8080/api | - |
| **API Docs** | http://lampadas.local:8080/docs | - |
| **Health Check** | http://lampadas.local:8080/api/health/detailed | - |
| **Grafana** | http://lampadas.local:3000 | admin/[.env] |
| **Prometheus** | http://lampadas.local:9090 | - |

## Health Checks

HomeRack provides Kubernetes-style health checks:

```bash
# Basic health
curl http://lampadas.local:8080/api/health

# Liveness (is app alive?)
curl http://lampadas.local:8080/api/health/live

# Readiness (ready to serve traffic?)
curl http://lampadas.local:8080/api/health/ready

# Startup (has app started successfully?)
curl http://lampadas.local:8080/api/health/startup

# Detailed (all metrics)
curl http://lampadas.local:8080/api/health/detailed | jq
```

## Common Operations

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Monitoring logs
./deploy/monitoring.sh logs
```

### Restart Services

```bash
# Restart backend (reload code)
docker-compose -f docker-compose.prod.yml restart backend

# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart with rebuild
docker-compose -f docker-compose.prod.yml up -d --build
```

### Check Resource Usage

```bash
# Container stats
docker stats

# Via monitoring script
./deploy/monitoring.sh resources

# Detailed health with system metrics
curl http://lampadas.local:8080/api/health/detailed | jq '.checks'
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it homerack-postgres psql -U homerack -d homerack

# Backup database
./deploy/backup.sh

# Check database size
docker exec homerack-postgres psql -U homerack -d homerack -c \
  "SELECT pg_size_pretty(pg_database_size('homerack'));"
```

### Cache Operations

```bash
# Check Redis
docker exec -it homerack-redis redis-cli ping

# View cache stats
curl http://lampadas.local:8080/api/health/cache/stats

# Clear all cache (use with caution)
curl -X POST http://lampadas.local:8080/api/health/cache/clear

# Invalidate specific pattern
curl -X DELETE http://lampadas.local:8080/api/health/cache/invalidate/thermal:*
```

## Performance Tuning

### Adjust Workers

Edit `.env`:

```bash
# For 2 CPU cores
WORKERS=2

# For 4 CPU cores (default)
WORKERS=4

# For 8 CPU cores
WORKERS=8
```

Restart backend:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Connection Pool

Edit `.env`:

```bash
DB_POOL_SIZE=20         # Concurrent connections
DB_MAX_OVERFLOW=10      # Additional when needed
```

### Redis Memory

Edit `docker-compose.prod.yml`:

```yaml
redis:
  command: >
    redis-server
    --maxmemory 256mb     # Adjust based on available RAM
    --maxmemory-policy allkeys-lru
```

## Monitoring & Alerts

### View Metrics in Grafana

1. Open http://lampadas.local:3000
2. Login with credentials from `.env`
3. Navigate to Dashboards
4. View:
   - **HomeRack Application** - API metrics
   - **HomeRack Infrastructure** - System metrics

### Check Prometheus

1. Open http://lampadas.local:9090
2. Run queries:
   - `up` - Service availability
   - `rate(http_requests_total[5m])` - Request rate
   - `http_request_duration_seconds` - Latency

### Alert Rules

Pre-configured alerts (see `monitoring/alerts.yml`):
- Service down (>2min)
- High memory (>85%)
- High CPU (>80%)
- Low disk space (<20%)
- High API latency (>2s)
- High error rate (>10%)

## Backup & Restore

### Manual Backup

```bash
sudo ./deploy/backup.sh
```

Backs up:
- PostgreSQL database
- Redis data
- Uploaded files (brand logos)

### Restore from Backup

```bash
# List backups
ls -lh /var/backups/homerack/

# Extract backup
cd /var/backups/homerack
tar xzf homerack_backup_TIMESTAMP.tar.gz -C /tmp/restore

# Stop application
docker-compose -f docker-compose.prod.yml down

# Restore database
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 5
gunzip < /tmp/restore/database.sql.gz | \
  docker exec -i homerack-postgres psql -U homerack homerack

# Restore uploads
docker run --rm \
  -v homerack-uploads:/data \
  -v /tmp/restore:/backup \
  alpine \
  tar xzf /backup/uploads.tar.gz -C /data

# Start application
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# 1. Database connection - verify DATABASE_URL in .env
# 2. Port in use - check: sudo lsof -i :8000
# 3. Out of memory - check: docker stats
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Reduce workers
# Edit .env: WORKERS=2
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Connection Issues

```bash
# Test connection
docker exec -it homerack-postgres psql -U homerack -d homerack

# Check from backend
docker exec -it homerack-backend python -c \
  "from sqlalchemy import create_engine; \
   from app.config import settings; \
   engine = create_engine(settings.DATABASE_URL); \
   print(engine.connect())"
```

### Slow API Responses

```bash
# Check detailed health
curl http://lampadas.local:8080/api/health/detailed | jq

# Check database latency
# (in detailed health response: .checks.database.latency_ms)

# Clear cache if needed
curl -X POST http://lampadas.local:8080/api/health/cache/clear

# Check worker count
docker exec homerack-backend ps aux | grep gunicorn
```

## Security Considerations

### Current Setup (lampadas.local)

- **HTTP only** - Appropriate for local network
- **Security headers** - Configured in Nginx
- **Rate limiting** - 10 req/s for API, 30 req/s general
- **Container security** - Non-root user, dropped capabilities

### For Production (Public Internet)

Enable HTTPS:

```bash
# Generate SSL certificate
sudo ./deploy/generate_ssl_cert.sh

# Choose option 2 (Let's Encrypt) for production
# Follow prompts for domain and email

# Deploy with SSL config
# See deploy/SSL_SETUP.md for details
```

Additional security:
- Use strong passwords (generated by script)
- Configure firewall (UFW)
- Regular backups
- Monitor logs for suspicious activity
- Keep Docker images updated

## Upgrade from Previous Version

If upgrading from single-worker setup:

```bash
# 1. Backup current data
sudo ./deploy/backup.sh

# 2. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 3. Generate new configuration
./deploy/generate_passwords.sh

# 4. Deploy with new configuration
docker-compose -f docker-compose.prod.yml up --build -d

# 5. Verify deployment
./deploy/verify_production.sh
```

## Next Steps

1. **Review Configuration**: Check `.env` settings match your needs
2. **Setup Backups**: Configure automated daily backups
3. **Monitor Application**: Review Grafana dashboards
4. **Test Load**: Run load tests to verify performance
5. **Plan Scaling**: Consider horizontal scaling if needed

## Documentation

- **PRODUCTION_SETUP.md** - Comprehensive production guide
- **deploy/README.md** - Deployment scripts documentation
- **deploy/SSL_SETUP.md** - HTTPS/SSL configuration
- **DEPLOYMENT_UPGRADE_SUMMARY.md** - Detailed upgrade notes

## Support

### Quick Checks

```bash
# Verification script (comprehensive)
./deploy/verify_production.sh

# Detailed health check
curl http://lampadas.local:8080/api/health/detailed | jq

# Container status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats --no-stream
```

### Log Locations

- **Application**: `docker-compose logs`
- **Backups**: `/var/backups/homerack/`
- **System**: Check with `./deploy/monitoring.sh logs`

### Need Help?

1. Check logs first
2. Review health checks
3. Check monitoring dashboards
4. Review documentation in `/deploy/`

---

**Quick Reference Card**

```bash
# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verify
./deploy/verify_production.sh

# Monitor
./deploy/monitoring.sh start

# Backup
sudo ./deploy/backup.sh

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# Health
curl http://lampadas.local:8080/api/health/detailed

# Restart
docker-compose -f docker-compose.prod.yml restart backend
```

**Version:** 1.0.1 | **Date:** 2026-01-12 | **Status:** Production Ready
