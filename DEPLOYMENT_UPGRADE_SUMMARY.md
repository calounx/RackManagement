# HomeRack Production Deployment Upgrade Summary

## Overview

HomeRack has been upgraded from a basic single-worker deployment to a production-grade system with comprehensive monitoring, security hardening, and high availability features.

## Key Improvements

### 1. Multiple Worker Support

**Before:**
- Single Uvicorn worker
- Limited concurrency
- Single point of failure

**After:**
- 4 Gunicorn workers with Uvicorn ASGI workers
- Configurable worker count (via `WORKERS` environment variable)
- Worker management:
  - Automatic restart after 10,000 requests
  - Graceful shutdown (30s timeout)
  - Worker timeout: 120s
  - 1,000 concurrent connections per worker

**Configuration:**
```bash
# backend/Dockerfile.prod
CMD gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --max-requests 10000
```

### 2. Database Upgrade: PostgreSQL

**Before:**
- SQLite (single-file database)
- Limited concurrency
- No connection pooling

**After:**
- PostgreSQL 15 (production-grade RDBMS)
- Connection pooling (20 connections, 10 overflow)
- Connection retry logic
- Health checks
- Pre-ping for stale connections

**Benefits:**
- Better concurrent access
- ACID compliance
- Better performance at scale
- Production-ready reliability

### 3. Redis Cache Integration

**New Feature:**
- Redis 7 for caching and rate limiting
- LRU eviction policy
- 256MB memory limit
- Persistence enabled
- Health checks

**Use Cases:**
- API response caching
- Rate limiting state
- Session storage
- Thermal analysis caching
- Device spec caching

### 4. Comprehensive Health Checks

**New Endpoints:**

1. **`/health/live`** - Liveness probe
   - Checks if application is alive
   - Used by Kubernetes/orchestrators

2. **`/health/ready`** - Readiness probe
   - Checks database connectivity
   - Checks circuit breaker state
   - Returns 503 if not ready

3. **`/health/startup`** - Startup probe
   - Verifies application started successfully
   - Checks critical dependencies

4. **`/health/detailed`** - Comprehensive check
   - Database connectivity + latency
   - Redis connectivity + stats
   - Disk space usage (with thresholds)
   - Memory usage (with thresholds)
   - Circuit breaker states
   - Configuration status

**System Metrics Included:**
- Disk space (warning at 80%, critical at 90%)
- Memory usage (warning at 80%, critical at 90%)
- Database latency
- Redis stats

### 5. Monitoring Stack

**Components:**

1. **Prometheus** (http://lampadas.local:9090)
   - Metrics collection and storage
   - 30-day retention
   - Alert rules configured

2. **Grafana** (http://lampadas.local:3000)
   - Pre-built dashboards
   - Real-time visualization
   - Alert management

3. **Node Exporter** (http://lampadas.local:9100)
   - System metrics (CPU, memory, disk, network)

4. **cAdvisor** (http://lampadas.local:8081)
   - Container metrics
   - Resource usage per container

**Pre-configured Dashboards:**
- **Application Dashboard**: Request rates, latency (p95, p99), error rates, status codes
- **Infrastructure Dashboard**: CPU, memory, disk usage, container metrics

**Alert Rules:**
- Service down (2m)
- High memory usage (>85% for 5m)
- Critical memory usage (>95% for 2m)
- High CPU usage (>80% for 5m)
- Disk space warning (<20%)
- Disk space critical (<10%)
- Container restarts
- High API latency (>2s)
- High error rate (>10%)

**Management:**
```bash
./deploy/monitoring.sh start   # Start stack
./deploy/monitoring.sh status  # Check status
./deploy/monitoring.sh logs    # View logs
./deploy/monitoring.sh backup  # Backup data
```

### 6. Security Hardening

**Nginx Security:**
- Server version hidden (`server_tokens off`)
- Security headers:
  - `X-Frame-Options: SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Content-Security-Policy`
  - `Permissions-Policy`
  - `Strict-Transport-Security` (HTTPS only)
- Rate limiting:
  - API: 10 req/s (burst 10)
  - General: 30 req/s (burst 20)
- Connection limiting: 10 concurrent per IP
- Request size limit: 10MB
- Timeouts configured (12s body, 15s keepalive)

**Docker Security:**
- Non-root user (`appuser` UID 1000)
- Security options:
  - `no-new-privileges:true`
  - Dropped ALL capabilities
  - Added only `NET_BIND_SERVICE`
- Read-only filesystem where possible
- Temporary filesystem (`/tmp`) with size limit

**Environment Security:**
- Strong password generation script
- Secrets never committed to git
- `.env` file in `.gitignore`
- Separate production configuration template

### 7. SSL/TLS Support

**Prepared for HTTPS:**
- `nginx-ssl.conf` template with modern TLS settings
- Certificate generation script (`generate_ssl_cert.sh`)
- Support for:
  1. Self-signed certificates (testing/internal)
  2. Let's Encrypt (production)
- Automatic certificate renewal configured
- HTTP to HTTPS redirect
- HSTS header for security
- OCSP stapling
- TLS 1.2 and 1.3 only
- Strong cipher suites

**Current Setup:**
- HTTP on lampadas.local (appropriate for local network)
- HTTPS configuration ready for production deployment

### 8. Automated Backups

**Backup Script:** `deploy/backup.sh`

**Features:**
- Database backup (PostgreSQL dump or SQLite copy)
- Uploaded files backup (brand logos)
- Compressed archives (gzip)
- Retention policy (7 days default)
- Backup metadata included
- Restore instructions provided

**Usage:**
```bash
# Manual backup
sudo ./deploy/backup.sh

# Automated via cron (daily at 2 AM)
0 2 * * * /home/calounx/repositories/homerack/deploy/backup.sh
```

**Backup Location:** `/var/backups/homerack/`

**Restore Procedure:** See `PRODUCTION_SETUP.md`

### 9. Production Environment Configuration

**New `.env.production` Template:**

Categories:
1. Application settings (workers, timeouts)
2. Database configuration (PostgreSQL)
3. Redis configuration (cache, rate limiting)
4. Security settings (secrets, CORS, auth)
5. Logging configuration
6. Rate limiting
7. Reliability patterns (circuit breaker, retry)
8. File uploads
9. Monitoring & observability
10. External integrations
11. Backup configuration
12. Email notifications (optional)
13. Feature flags
14. Performance tuning

**Password Generation:**
```bash
./deploy/generate_passwords.sh
# Generates cryptographically secure passwords for all services
```

### 10. Enhanced Logging

**Features:**
- JSON structured logging
- Request ID tracking
- Log levels by environment
- Sensitive data filtering
- Log rotation ready

**Configuration:**
```bash
LOG_LEVEL=INFO       # Production
LOG_FORMAT=json      # Structured logging
```

**Docker Log Rotation:**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 11. Dependencies Added

**Backend (`requirements.txt`):**
```python
gunicorn==21.2.0           # Multi-worker process manager
psycopg2-binary==2.9.9     # PostgreSQL driver
psutil==5.9.8              # System metrics
prometheus-client==0.20.0   # Metrics export
```

## File Structure Changes

### New Files

```
/home/calounx/repositories/homerack/
├── .env.production                          # Production environment template
├── PRODUCTION_SETUP.md                      # Comprehensive production guide
├── docker-compose.monitoring.yml            # Monitoring stack
├── deploy/
│   ├── nginx.conf                          # HTTP Nginx config (current)
│   ├── nginx-ssl.conf                      # HTTPS Nginx config (template)
│   ├── generate_ssl_cert.sh               # SSL certificate generation
│   ├── backup.sh                          # Automated backup script
│   ├── monitoring.sh                      # Monitoring management
│   ├── generate_passwords.sh              # Password generation
│   └── SSL_SETUP.md                       # SSL setup guide
└── monitoring/
    ├── prometheus.yml                      # Prometheus config
    ├── alerts.yml                         # Alert rules
    └── grafana/
        ├── provisioning/
        │   ├── datasources/
        │   │   └── prometheus.yml         # Datasource config
        │   └── dashboards/
        │       └── default.yml            # Dashboard provisioning
        └── dashboards/
            ├── application.json           # Application metrics dashboard
            └── infrastructure.json        # Infrastructure metrics dashboard
```

### Modified Files

```
backend/Dockerfile.prod              # Added Gunicorn, multi-worker support
backend/requirements.txt             # Added psutil, prometheus-client, gunicorn
backend/app/api/health.py           # Enhanced with disk, memory, Redis checks
docker-compose.prod.yml             # Added PostgreSQL, Redis, worker config
deploy/README.md                    # Updated with new features
```

## Performance Improvements

### Concurrency
- **Before**: 1 worker → ~100 concurrent requests
- **After**: 4 workers → ~4,000 concurrent requests (1,000 per worker)

### Database Performance
- **Before**: SQLite with file locking
- **After**: PostgreSQL with connection pooling (20 connections)

### Caching
- **Before**: No caching
- **After**: Redis caching for:
  - Thermal analysis (5 min TTL)
  - Optimization results (10 min TTL)
  - Search results (60 min TTL)
  - Device specs (60 min TTL)

### Response Times
Expected on recommended hardware (4 cores, 8GB RAM):
- API latency p95: <100ms
- API latency p99: <500ms
- Concurrent users: 100+
- Requests/second: 500+

## Deployment Process Changes

### Initial Deployment

**Before:**
```bash
./deploy/deploy.sh
# Basic deployment, SQLite, single worker
```

**After:**
```bash
# 1. Generate passwords
./deploy/generate_passwords.sh

# 2. Review and customize .env
cp .env.generated .env
vim .env

# 3. Deploy with PostgreSQL + Redis
./deploy/deploy.sh

# 4. Start monitoring (optional)
./deploy/monitoring.sh start

# 5. Setup backups
sudo crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Health Check Process

**Before:**
```bash
curl http://lampadas.local:8080/health
```

**After:**
```bash
# Basic check
curl http://lampadas.local:8080/api/health

# Liveness (K8s-style)
curl http://lampadas.local:8080/api/health/live

# Readiness (K8s-style)
curl http://lampadas.local:8080/api/health/ready

# Detailed (all metrics)
curl http://lampadas.local:8080/api/health/detailed
```

## Migration Path

### From Current Setup to Production

1. **Backup current data:**
   ```bash
   sudo ./deploy/backup.sh
   ```

2. **Generate production configuration:**
   ```bash
   ./deploy/generate_passwords.sh
   cp .env.generated .env
   # Edit .env with your settings
   ```

3. **Deploy with PostgreSQL:**
   ```bash
   # Rebuild with new configuration
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

4. **Migrate data (if needed):**
   ```bash
   # Export from SQLite
   sqlite3 homerack.db .dump > dump.sql

   # Import to PostgreSQL
   docker exec -i homerack-postgres psql -U homerack homerack < dump.sql
   ```

5. **Start monitoring:**
   ```bash
   ./deploy/monitoring.sh start
   ```

6. **Verify deployment:**
   ```bash
   curl http://lampadas.local:8080/api/health/detailed
   ```

## Configuration Examples

### Worker Tuning

For different hardware:

```bash
# 2 CPU cores
WORKERS=2

# 4 CPU cores (recommended)
WORKERS=4

# 8 CPU cores
WORKERS=8

# 16+ CPU cores
WORKERS=12  # Don't use all cores, leave some for OS
```

### Memory Configuration

```bash
# PostgreSQL pool
DB_POOL_SIZE=20         # Base connections
DB_MAX_OVERFLOW=10      # Additional when needed

# Redis
# In docker-compose.yml:
--maxmemory 256mb       # Adjust based on available RAM
```

### Rate Limiting

```bash
# Nginx (requests per second)
limit_req_zone ... rate=10r/s;  # API
limit_req_zone ... rate=30r/s;  # General

# Connection limits
limit_conn conn_limit 10;  # Per IP
```

## Monitoring & Alerting

### Grafana Dashboards

Access: http://lampadas.local:3000

**Application Dashboard:**
- Request rate (req/s)
- Response time (p95, p99)
- HTTP status codes
- Error rate

**Infrastructure Dashboard:**
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Container metrics

### Prometheus Metrics

Access: http://lampadas.local:9090

**Available Metrics:**
- `up` - Service availability
- `http_requests_total` - Request count
- `http_request_duration_seconds` - Latency
- `node_memory_*` - Memory metrics
- `node_cpu_*` - CPU metrics
- `container_*` - Container metrics

### Alert Examples

Configure in `monitoring/alerts.yml`:

```yaml
- alert: HighAPILatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  annotations:
    summary: "High API latency detected"
```

## Troubleshooting

### Check Worker Count

```bash
docker exec homerack-backend ps aux | grep gunicorn
# Should show 1 master + 4 workers = 5 processes
```

### Database Connection

```bash
# Test PostgreSQL
docker exec -it homerack-postgres psql -U homerack -d homerack

# Check from backend
docker exec -it homerack-backend python -c \
  "from app.config import settings; print(settings.DATABASE_URL)"
```

### Redis Connection

```bash
# Test Redis
docker exec -it homerack-redis redis-cli ping

# Check stats
curl http://lampadas.local:8080/api/health/cache/stats
```

### Memory Issues

```bash
# Check container stats
docker stats

# Reduce workers if needed
# Edit .env: WORKERS=2
docker-compose -f docker-compose.prod.yml restart backend
```

## Documentation

### Primary Guides

1. **PRODUCTION_SETUP.md** - Comprehensive production deployment guide
2. **deploy/SSL_SETUP.md** - SSL/TLS configuration guide
3. **deploy/README.md** - Deployment scripts documentation

### Quick References

- **Generate passwords**: `./deploy/generate_passwords.sh --help`
- **Backup**: `sudo ./deploy/backup.sh`
- **Monitoring**: `./deploy/monitoring.sh --help`
- **SSL setup**: `sudo ./deploy/generate_ssl_cert.sh`

## Next Steps

1. **Current Setup (lampadas.local):**
   - Review `.env` configuration
   - Ensure PostgreSQL password is strong
   - Consider enabling monitoring stack

2. **For Production Deployment:**
   - Configure domain name in `.env`
   - Setup SSL/TLS with Let's Encrypt
   - Configure firewall rules
   - Setup automated backups
   - Configure log rotation
   - Load test the application
   - Setup alert notifications

3. **Optional Enhancements:**
   - Setup Nginx load balancer for multiple backends
   - Configure external PostgreSQL cluster
   - Setup Redis sentinel for HA
   - Implement database replication
   - Add application-level caching

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review health: `curl http://lampadas.local:8080/api/health/detailed`
3. Check monitoring: http://lampadas.local:3000
4. Review documentation in `/deploy/` directory

---

**Version:** 1.0.1
**Date:** 2026-01-12
**Status:** Production Ready
