# HomeRack Production Deployment Guide

Comprehensive guide for deploying HomeRack in production with security hardening, monitoring, and high availability.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Security Configuration](#security-configuration)
5. [Deployment](#deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Backup & Restore](#backup--restore)
8. [Performance Tuning](#performance-tuning)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## Architecture Overview

### Production Stack

```
┌─────────────────────────────────────────────────────────┐
│                     Internet/Network                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Nginx Proxy  │ (SSL/TLS, Rate Limiting)
              └───────┬───────┘
                      │
         ┌────────────┼────────────┐
         │                         │
         ▼                         ▼
┌────────────────┐        ┌────────────────┐
│    Frontend    │        │    Backend     │
│   (React SPA)  │        │  (FastAPI API) │
│                │        │  4 Workers     │
└────────────────┘        └────────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │                             │
                    ▼                             ▼
           ┌─────────────────┐         ┌──────────────────┐
           │   PostgreSQL    │         │      Redis       │
           │   (Database)    │         │  (Cache/Queue)   │
           └─────────────────┘         └──────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Monitoring Stack                            │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────┐ │
│  │ Prometheus │  │  Grafana  │  │ Node/cAdvisor      │ │
│  └────────────┘  └───────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Features

- **4 Gunicorn workers** with Uvicorn ASGI workers
- **PostgreSQL** for reliable data persistence
- **Redis** for caching and rate limiting
- **Nginx** for reverse proxy with security hardening
- **Prometheus + Grafana** for monitoring
- **Automated backups** with retention policy
- **Health checks** at multiple levels (liveness, readiness, startup)

## Prerequisites

### System Requirements

**Minimum (Small Deployment):**
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space
- Ubuntu 20.04+ or Debian 11+

**Recommended (Production):**
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space (SSD preferred)
- Ubuntu 22.04 LTS

### Software Requirements

```bash
# Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Verify installation
docker --version
docker-compose --version

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

### Network Requirements

- **Port 80** (HTTP) - Open
- **Port 443** (HTTPS) - Open for production
- **Port 8080** (Frontend) - Current setup for lampadas.local
- **Port 9090** (Prometheus) - Internal network only
- **Port 3000** (Grafana) - Internal network only

## Initial Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourorg/homerack.git
cd homerack

# Create production environment file
cp .env.production .env
```

### 2. Generate Secrets

```bash
# Generate strong passwords and keys
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)" >> .env
```

### 3. Edit Configuration

Edit `.env` and update:

```bash
# Domain (or IP for lampadas.local)
CORS_ORIGINS=["http://lampadas.local","http://lampadas.local:8080"]

# Database
POSTGRES_USER=homerack
POSTGRES_PASSWORD=<generated-above>
POSTGRES_DB=homerack
DATABASE_URL=postgresql://homerack:<password>@postgres:5432/homerack

# Redis
REDIS_URL=redis://redis:6379/0

# Workers (adjust based on CPU cores)
WORKERS=4  # Recommended: 2-4 x CPU cores
```

## Security Configuration

### 1. Firewall Setup

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp  # For current lampadas.local setup
sudo ufw enable

# Restrict monitoring ports to local network only
sudo ufw allow from 192.168.0.0/16 to any port 9090
sudo ufw allow from 192.168.0.0/16 to any port 3000
```

### 2. SSL/TLS Setup

For production HTTPS deployment, see [SSL_SETUP.md](deploy/SSL_SETUP.md).

For lampadas.local, HTTP is currently configured and appropriate for local network use.

### 3. Docker Security

The production deployment includes security hardening:

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE
read_only: false  # Needed for uploads
```

### 4. Secrets Management

For enhanced security, use Docker secrets:

```bash
# Create secrets
echo "your-postgres-password" | docker secret create postgres_password -
echo "your-secret-key" | docker secret create app_secret_key -

# Update docker-compose.prod.yml to use secrets
```

## Deployment

### Initial Deployment

```bash
# Deploy application
./deploy/deploy.sh

# This will:
# - Build Docker images
# - Start PostgreSQL and Redis
# - Run database migrations
# - Start backend (4 workers)
# - Start frontend
# - Verify health checks
```

### Verify Deployment

```bash
# Check all containers are running
docker ps

# Expected output:
# - homerack-backend
# - homerack-frontend
# - homerack-postgres
# - homerack-redis

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test API
curl http://lampadas.local:8080
curl http://lampadas.local:8080/api/health

# Detailed health check
curl http://lampadas.local:8080/api/health/detailed
```

### Update Deployment

```bash
# Zero-downtime update
./deploy/update.sh

# This will:
# - Pull latest code
# - Build new images
# - Run migrations
# - Rolling restart of services
# - Health check verification
```

## Monitoring Setup

### Start Monitoring Stack

```bash
# Start Prometheus + Grafana
./deploy/monitoring.sh start

# Check status
./deploy/monitoring.sh status

# View monitoring URLs
./deploy/monitoring.sh urls
```

### Access Monitoring

- **Grafana**: http://lampadas.local:3000 (admin/admin)
- **Prometheus**: http://lampadas.local:9090

### Dashboards

Pre-configured dashboards:
1. **HomeRack Application** - API metrics, latency, error rates
2. **HomeRack Infrastructure** - CPU, memory, disk, containers

### Alerts

Prometheus alerts are configured for:
- Service downtime
- High memory usage (>85%)
- High CPU usage (>80%)
- Low disk space (<20%)
- High API latency (>2s)
- High error rate (>10%)

## Backup & Restore

### Automated Backups

```bash
# Run backup manually
sudo ./deploy/backup.sh

# Schedule daily backups via cron
sudo crontab -e

# Add line:
0 2 * * * /home/calounx/repositories/homerack/deploy/backup.sh >> /var/log/homerack-backup.log 2>&1
```

### Backup Location

Default: `/var/backups/homerack/`

Backups include:
- PostgreSQL database dump (compressed)
- SQLite database (if used)
- Uploaded files (brand logos)
- Backup metadata

Retention: 7 days (configurable via `RETENTION_DAYS`)

### Restore Procedure

```bash
# Stop application
docker-compose -f docker-compose.prod.yml down

# Extract backup
cd /var/backups/homerack
tar xzf homerack_backup_TIMESTAMP.tar.gz -C /tmp/restore

# Restore PostgreSQL database
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 5
docker exec -i homerack-postgres psql -U homerack homerack < /tmp/restore/database.sql

# Restore uploads
docker run --rm \
    -v homerack-uploads:/data \
    -v /tmp/restore:/backup \
    alpine \
    tar xzf /backup/uploads.tar.gz -C /data

# Start application
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl http://lampadas.local:8080/api/health/detailed
```

## Performance Tuning

### Worker Configuration

Adjust workers based on CPU cores:

```bash
# In .env
WORKERS=4  # Recommended: 2-4 x CPU cores

# For 2 CPU cores:
WORKERS=2

# For 8 CPU cores:
WORKERS=8
```

### Database Connection Pool

```bash
# In .env
DB_POOL_SIZE=20          # Concurrent connections
DB_MAX_OVERFLOW=10       # Additional connections when needed
DB_POOL_RECYCLE=3600     # Recycle connections after 1 hour
```

### Redis Configuration

```bash
# In docker-compose.prod.yml
redis:
  command: >
    redis-server
    --maxmemory 256mb          # Adjust based on available RAM
    --maxmemory-policy allkeys-lru
```

### Nginx Optimization

```nginx
# In deploy/nginx.conf
worker_processes auto;  # Auto-detect CPU cores
worker_connections 1024;

# Caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;
```

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# 1. Database connection failed
#    - Verify DATABASE_URL in .env
#    - Check postgres container: docker ps | grep postgres

# 2. Port already in use
#    - Check: sudo lsof -i :8000
#    - Stop conflicting service

# 3. Permission denied
#    - Check volume permissions
#    - Verify user in Dockerfile
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker exec -it homerack-postgres psql -U homerack -d homerack

# Check connection from backend
docker exec -it homerack-backend bash
python -c "from app.config import settings; print(settings.DATABASE_URL)"

# Reset database (CAUTION: deletes all data)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Reduce workers if needed
# Edit .env: WORKERS=2
docker-compose -f docker-compose.prod.yml restart backend

# Check for memory leaks
docker exec homerack-backend ps aux
```

### Slow API Response

```bash
# Check detailed health
curl http://lampadas.local:8080/api/health/detailed

# Monitor query performance
docker exec -it homerack-postgres psql -U homerack -d homerack
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

# Check Redis cache hit rate
curl http://lampadas.local:8080/api/health/cache/stats
```

## Maintenance

### Update Dependencies

```bash
# Backend
cd backend
pip-compile requirements.in  # If using pip-tools
docker-compose -f ../docker-compose.prod.yml build backend
```

### Database Migrations

```bash
# Create migration
docker exec -it homerack-backend alembic revision --autogenerate -m "description"

# Run migrations
docker exec -it homerack-backend alembic upgrade head

# Rollback migration
docker exec -it homerack-backend alembic downgrade -1
```

### Log Management

```bash
# View logs
./deploy/monitoring.sh logs

# Service-specific logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Log rotation (Docker)
# Edit /etc/docker/daemon.json:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Health Monitoring

```bash
# Kubernetes-style health checks
curl http://lampadas.local:8080/api/health/live      # Liveness
curl http://lampadas.local:8080/api/health/ready     # Readiness
curl http://lampadas.local:8080/api/health/startup   # Startup
curl http://lampadas.local:8080/api/health/detailed  # Detailed
```

### Certificate Renewal (if using HTTPS)

```bash
# Let's Encrypt auto-renewal is configured
# Manual renewal if needed:
sudo certbot renew
sudo systemctl reload nginx
```

## Production Checklist

Before going live:

- [ ] All `CHANGE_ME` values replaced in `.env`
- [ ] Strong passwords generated (min 32 characters)
- [ ] SSL/TLS configured (if public-facing)
- [ ] Firewall rules configured
- [ ] Monitoring stack running
- [ ] Backup cron job configured
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Documentation reviewed
- [ ] Rollback procedure tested

## Support & Resources

### Log Locations

- **Application**: `docker-compose logs`
- **Nginx**: `/var/log/nginx/`
- **Backups**: `/var/backups/homerack/`

### Configuration Files

- **Environment**: `.env`
- **Docker Compose**: `docker-compose.prod.yml`
- **Nginx**: `deploy/nginx.conf`, `deploy/nginx-ssl.conf`
- **Monitoring**: `monitoring/prometheus.yml`

### Useful Commands

```bash
# Deployment
./deploy/deploy.sh          # Initial deployment
./deploy/update.sh          # Update deployment
./deploy/rollback.sh        # Rollback deployment

# Monitoring
./deploy/monitoring.sh start    # Start monitoring
./deploy/monitoring.sh status   # Check status
./deploy/monitoring.sh urls     # Show URLs

# Backup
sudo ./deploy/backup.sh     # Manual backup

# Logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Performance Benchmarks

Expected performance on recommended hardware:

- **API Latency (p95)**: <100ms
- **API Latency (p99)**: <500ms
- **Concurrent Users**: 100+
- **Requests/sec**: 500+
- **Optimization Time**: <2s for typical rack

## Scaling

### Horizontal Scaling

For high-traffic deployments:

1. **Load Balancer**: Add Nginx load balancer
2. **Multiple Backend Instances**: Deploy on multiple servers
3. **Shared Database**: Use external PostgreSQL cluster
4. **Shared Cache**: Use external Redis cluster
5. **Shared Storage**: Use S3/MinIO for uploads

### Vertical Scaling

Increase resources on single server:
- Add more CPU cores → increase WORKERS
- Add more RAM → increase DB_POOL_SIZE
- Add faster disk → improve database performance

## License

See [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
