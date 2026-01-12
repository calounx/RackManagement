# HomeRack Deployment Guide

Complete deployment automation for HomeRack with production-grade features.

## Overview

This deployment solution provides:
- **Production-optimized Docker containers** with security hardening
- **Multiple Gunicorn workers** (4 workers with Uvicorn ASGI)
- **PostgreSQL + Redis** for reliability and performance
- **Automated deployment scripts** with health checks
- **Zero-downtime updates** with rollback capability
- **Comprehensive monitoring** (Prometheus + Grafana)
- **Automated backups** with retention policy
- **SSL/TLS support** (HTTPS ready)
- **Security hardening** (rate limiting, headers, container security)
- **Automatic startup** via systemd

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 lampadas.local:8080                      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Frontend Container (Nginx)                        │ │
│  │  - React SPA serving                               │ │
│  │  - Static asset caching                            │ │
│  │  - API proxying to backend                         │ │
│  │  - Security headers                                │ │
│  │  Port: 80 (internal) → 8080 (external)             │ │
│  └─────────────────────┬──────────────────────────────┘ │
│                        │                                 │
│  ┌─────────────────────▼──────────────────────────────┐ │
│  │  Backend Container (FastAPI + Gunicorn)            │ │
│  │  - Python 3.11 + 4 Gunicorn workers                │ │
│  │  - Uvicorn ASGI workers                            │ │
│  │  - Health checks (liveness, readiness, startup)    │ │
│  │  - Prometheus metrics endpoint                     │ │
│  │  - Security: non-root user, dropped capabilities   │ │
│  │  Port: 8000 (internal only)                        │ │
│  └──────────────┬──────────────┬──────────────────────┘ │
│                 │              │                         │
│  ┌──────────────▼─────────┐  ┌▼────────────────────┐   │
│  │  PostgreSQL Container  │  │  Redis Container    │   │
│  │  - Version 15          │  │  - Version 7        │   │
│  │  - Connection pooling  │  │  - LRU caching      │   │
│  │  - Health checks       │  │  - Persistence      │   │
│  │  Port: 5432            │  │  Port: 6379         │   │
│  └────────────────────────┘  └─────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Persistent Volumes                                │ │
│  │  - postgres-data (Database)                        │ │
│  │  - redis-data (Cache persistence)                  │ │
│  │  - homerack-uploads (Brand logos, files)           │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Monitoring Stack (Optional)                 │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────┐ │
│  │ Prometheus │  │  Grafana  │  │ Node/cAdvisor      │ │
│  │ :9090      │  │  :3000    │  │ :9100 / :8081      │ │
│  └────────────┘  └───────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- SSH access to lampadas.local as user calounx (passwordless sudo)
- SSH key-based authentication configured
- Network connectivity between local machine and lampadas.local
- rsync installed on local machine

## Quick Start

### 1. Generate Secure Passwords

```bash
cd /home/calounx/repositories/homerack
./deploy/generate_passwords.sh
# Save output to .env.generated
# Review and customize, then: mv .env.generated .env
```

### 2. Deploy Application

```bash
./deploy/deploy.sh
```

### 3. Start Monitoring (Optional)

```bash
./deploy/monitoring.sh start
```

### 4. Setup Automated Backups

```bash
# Test backup
sudo ./deploy/backup.sh

# Configure daily backups (2 AM)
sudo crontab -e
# Add: 0 2 * * * /home/calounx/repositories/homerack/deploy/backup.sh
```

### Access Points

- **Frontend**: http://lampadas.local:8080
- **API Docs**: http://lampadas.local:8080/docs
- **Health Check**: http://lampadas.local:8080/api/health/detailed
- **Grafana**: http://lampadas.local:3000 (admin/[generated])
- **Prometheus**: http://lampadas.local:9090

## Deployment Files

### Docker Configurations

- `/backend/Dockerfile.prod` - Production-optimized backend container
  - Multi-stage build for smaller image size
  - Non-root user for security
  - Health checks configured
  - 4 uvicorn workers for performance

- `/frontend/Dockerfile` - Production frontend container
  - Multi-stage build (Node.js builder + nginx runtime)
  - Static asset optimization
  - Nginx reverse proxy configuration
  - Health checks configured

- `/docker-compose.prod.yml` - Production orchestration
  - Service dependencies and health checks
  - Persistent volumes for data
  - Network isolation
  - Environment configuration

### Deployment Scripts

- `/deploy/deploy.sh` - Initial deployment
  - Installs Docker if needed
  - Copies application files
  - Builds and starts containers
  - Installs systemd service
  - Verifies health checks

- `/deploy/update.sh` - Zero-downtime updates
  - Syncs updated files
  - Rebuilds containers
  - Rolling restart
  - Health verification

- `/deploy/rollback.sh` - Emergency rollback
  - Stops current deployment
  - Restores previous version
  - Quick recovery

- `/deploy/monitor.sh` - Real-time monitoring
  - Container status
  - Health checks
  - Resource usage
  - Recent logs

### Systemd Service

- `/deploy/homerack.service` - Automatic startup
  - Starts on boot
  - Automatic restart on failure
  - Proper dependency management

## Initial Deployment

### Step 1: Run Deployment Script

From the repository root:

```bash
cd /home/calounx/repositories/homerack
./deploy/deploy.sh
```

The script will:
1. Verify SSH connectivity
2. Install Docker if needed
3. Create deployment directory at `/opt/homerack`
4. Copy application files
5. Build Docker images
6. Start containers
7. Configure systemd for automatic startup
8. Verify health checks

### Step 2: Verify Deployment

```bash
# Check container status
ssh calounx@lampadas.local "docker ps"

# Check health
curl http://lampadas.local:8080/health

# Run monitoring script
./deploy/monitor.sh
```

## Access URLs

After successful deployment:

- **Frontend Application**: http://lampadas.local:8080
- **Backend API Root**: http://lampadas.local:8080/api
- **API Documentation**: http://lampadas.local:8080/docs
- **Health Check**: http://lampadas.local:8080/health
- **Uploaded Files**: http://lampadas.local:8080/uploads/

## Management Commands

### On Local Machine

```bash
# Deploy initial version
./deploy/deploy.sh

# Update running application
./deploy/update.sh

# Rollback to previous version
./deploy/rollback.sh

# Monitor application status
./deploy/monitor.sh
```

### On lampadas.local

```bash
# View logs (all services)
cd /opt/homerack
docker compose -f docker-compose.prod.yml logs -f

# View backend logs only
docker logs -f homerack-backend

# View frontend logs only
docker logs -f homerack-frontend

# Restart application
sudo systemctl restart homerack

# Stop application
sudo systemctl stop homerack

# Start application
sudo systemctl start homerack

# Check service status
sudo systemctl status homerack

# View container status
docker ps

# Check resource usage
docker stats

# Execute commands in backend container
docker exec -it homerack-backend bash

# Execute commands in frontend container
docker exec -it homerack-frontend sh
```

## Updating the Application

### Standard Update Process

1. Make changes to code locally
2. Commit changes (optional but recommended)
3. Run update script:

```bash
./deploy/update.sh
```

This performs a rolling update with minimal downtime.

### Manual Update Process

If you prefer manual control:

```bash
# SSH to server
ssh calounx@lampadas.local

# Navigate to deployment directory
cd /opt/homerack

# Pull latest changes (if using git on server)
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
ssh calounx@lampadas.local "cd /opt/homerack && docker compose -f docker-compose.prod.yml logs"

# Check specific service
ssh calounx@lampadas.local "docker logs homerack-backend"
ssh calounx@lampadas.local "docker logs homerack-frontend"
```

### Health Check Failures

```bash
# Test backend directly
ssh calounx@lampadas.local "docker exec homerack-backend curl http://localhost:8000/health"

# Test frontend directly
ssh calounx@lampadas.local "docker exec homerack-frontend curl http://localhost:80/"

# Check container status
ssh calounx@lampadas.local "docker inspect homerack-backend"
```

### Permission Issues

```bash
# Fix deployment directory ownership
ssh calounx@lampadas.local "sudo chown -R calounx:calounx /opt/homerack"

# Fix volume permissions
ssh calounx@lampadas.local "docker compose -f /opt/homerack/docker-compose.prod.yml down -v"
ssh calounx@lampadas.local "cd /opt/homerack && docker compose -f docker-compose.prod.yml up -d"
```

### Network Issues

```bash
# Check Docker network
ssh calounx@lampadas.local "docker network inspect homerack_homerack-network"

# Test connectivity between containers
ssh calounx@lampadas.local "docker exec homerack-frontend ping -c 3 backend"
ssh calounx@lampadas.local "docker exec homerack-frontend curl -v http://backend:8000/health"
```

### Database Issues

```bash
# Check database file
ssh calounx@lampadas.local "docker exec homerack-backend ls -lah /app/data/"

# Access database directly
ssh calounx@lampadas.local "docker exec -it homerack-backend python -c 'from app.database import engine; print(engine.url)'"

# Backup database
ssh calounx@lampadas.local "docker cp homerack-backend:/app/data/homerack.db /tmp/homerack-backup.db"
```

## Data Persistence

### Database Backup

```bash
# Create backup
ssh calounx@lampadas.local "docker exec homerack-backend tar czf /tmp/backup.tar.gz /app/data"
scp calounx@lampadas.local:/tmp/backup.tar.gz ./homerack-backup-$(date +%Y%m%d).tar.gz

# Restore backup
scp ./homerack-backup.tar.gz calounx@lampadas.local:/tmp/
ssh calounx@lampadas.local "docker exec -i homerack-backend tar xzf /tmp/backup.tar.gz -C /"
ssh calounx@lampadas.local "cd /opt/homerack && docker compose -f docker-compose.prod.yml restart backend"
```

### Volume Management

```bash
# List volumes
ssh calounx@lampadas.local "docker volume ls"

# Inspect volume
ssh calounx@lampadas.local "docker volume inspect homerack_homerack-data"

# Backup volume
ssh calounx@lampadas.local "docker run --rm -v homerack_homerack-data:/data -v /tmp:/backup alpine tar czf /backup/data-backup.tar.gz /data"

# Clean up unused volumes (DANGER: Data loss!)
ssh calounx@lampadas.local "docker volume prune -f"
```

## Security Considerations

### Current Security Features

1. **Non-root Container User**: Backend runs as non-root user (uid 1000)
2. **Security Headers**: Frontend nginx adds security headers
3. **Network Isolation**: Containers communicate via private network
4. **Health Checks**: Automatic restart on failure
5. **Minimal Images**: Using slim/alpine base images
6. **Secret Management**: Environment variables for secrets

### Production Hardening (Recommended)

For production deployment, consider:

1. **HTTPS/TLS**: Use Let's Encrypt with nginx reverse proxy
2. **Secrets Management**: Use Docker secrets or external secret store
3. **Image Scanning**: Scan images for vulnerabilities
4. **Resource Limits**: Add CPU/memory limits to containers
5. **Firewall**: Restrict ports using UFW or iptables
6. **Authentication**: Add API authentication/authorization
7. **Rate Limiting**: Configure rate limiting in nginx
8. **Monitoring**: Add Prometheus/Grafana for metrics
9. **Backup Automation**: Schedule regular backups
10. **Log Aggregation**: Send logs to centralized logging

## Performance Tuning

### Backend Optimization

Edit `/backend/Dockerfile.prod` to adjust workers:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Workers = (2 × CPU cores) + 1 is a good starting point.

### Frontend Optimization

Nginx caching is already configured in `/frontend/docker/nginx.conf`. To adjust:

```nginx
# Increase cache time for static assets
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;  # Adjust as needed
}
```

## Monitoring and Alerting

### Basic Monitoring

Use the monitoring script:

```bash
./deploy/monitor.sh
```

### Advanced Monitoring Setup

For production, consider adding:

1. **Prometheus + Grafana**
2. **Container metrics exporters**
3. **Application performance monitoring (APM)**
4. **Log aggregation (ELK stack)**
5. **Uptime monitoring (external service)**

## CI/CD Integration

This deployment can be integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Deploy to Test
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to lampadas.local
        env:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ./deploy/deploy.sh
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Review logs for errors
2. **Monthly**: Update base images and rebuild
3. **Quarterly**: Review and update dependencies
4. **As needed**: Database backups before major changes

### Getting Help

- Check logs: `./deploy/monitor.sh`
- Review this README
- Check Docker documentation
- Contact system administrator

## License

Same license as HomeRack application.

## Changelog

- v1.0.0 (2026-01-12): Initial deployment configuration
  - Production Docker containers
  - Automated deployment scripts
  - Systemd service integration
  - Health monitoring
  - Comprehensive documentation
