# HomeRack Deployment - SUCCESS

## Deployment Summary

The HomeRack application has been successfully deployed to **lampadas.local** on **2026-01-12**.

## Access Information

### Application URLs

- **Frontend Application**: http://lampadas.local:8080
- **Backend API**: http://lampadas.local:8080/api
- **API Documentation (Swagger)**: http://lampadas.local:8080/docs
- **API Documentation (ReDoc)**: http://lampadas.local:8080/redoc
- **Health Check Endpoint**: http://lampadas.local:8080/health
- **Uploaded Files**: http://lampadas.local:8080/uploads/

### Container Information

| Container | Image | Status | Ports |
|-----------|-------|--------|-------|
| homerack-frontend | homerack-frontend:latest | Healthy | 8080:80 |
| homerack-backend | homerack-backend:latest | Healthy | 8000 (internal) |

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    lampadas.local:8080                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Frontend Container (Nginx + React)                  │  │
│  │  - Serves React SPA                                  │  │
│  │  - Proxies /api/* to backend                         │  │
│  │  - Proxies /uploads/* to backend                     │  │
│  │  - Static asset caching enabled                      │  │
│  │  - Security headers configured                       │  │
│  │  Port: 80 (internal) → 8080 (host)                  │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │ reverse proxy                         │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Backend Container (Python + FastAPI + uvicorn)     │  │
│  │  - FastAPI application                               │  │
│  │  - Single worker process                             │  │
│  │  - Health checks enabled                             │  │
│  │  - Non-root user (appuser)                          │  │
│  │  Port: 8000 (internal only - not exposed to host)   │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Persistent Docker Volumes                           │  │
│  │  - homerack_homerack-data (SQLite database)         │  │
│  │  - homerack_homerack-uploads (brand logos, files)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Network: homerack_homerack-network (bridge)               │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Configuration

### Environment

- **Environment**: production
- **Debug Mode**: disabled
- **Log Level**: INFO
- **Log Format**: JSON

### Data Persistence

- **Database**: SQLite at `/app/data/homerack.db` (in homerack_homerack-data volume)
- **Uploads**: `/app/uploads` (in homerack_homerack-uploads volume)
- **Backup Strategy**: Docker volume backups (see management commands below)

### Security Features

1. **Backend Container**:
   - Runs as non-root user (appuser, uid 1000)
   - No privileged access
   - Minimal dependencies installed
   - Multi-stage build reduces attack surface

2. **Frontend Container**:
   - Security headers enabled (X-Frame-Options, X-Content-Type-Options, etc.)
   - API requests proxied (no direct backend exposure)
   - Static asset caching with proper headers

3. **Network**:
   - Backend not exposed to host network
   - Only frontend port 8080 accessible externally
   - Containers communicate via internal Docker network

### Reliability Features

- **Health Checks**: Both containers have health check probes
- **Auto-Restart**: Containers restart on failure
- **Circuit Breaker**: Enabled in backend configuration
- **Rate Limiting**: Enabled in backend configuration
- **Request Timeouts**: Configured for all operations

## Management Commands

### On Local Machine

```bash
# Navigate to repository
cd /home/calounx/repositories/homerack

# Deploy/redeploy application
./deploy/deploy.sh

# Update running application (zero downtime)
./deploy/update.sh

# Rollback to previous version
./deploy/rollback.sh

# Monitor application status
./deploy/monitor.sh
```

### On lampadas.local

#### Service Management (systemd)

```bash
# Start application
sudo systemctl start homerack

# Stop application
sudo systemctl stop homerack

# Restart application
sudo systemctl restart homerack

# Check service status
sudo systemctl status homerack

# View service logs
sudo journalctl -u homerack -f
```

#### Docker Management

```bash
# Navigate to deployment directory
cd /opt/homerack

# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View container logs
docker logs -f homerack-backend
docker logs -f homerack-frontend

# View last 100 lines
docker logs --tail 100 homerack-backend

# Execute commands in backend container
docker exec -it homerack-backend bash

# Execute commands in frontend container
docker exec -it homerack-frontend sh

# Restart containers
docker compose -f docker-compose.prod.yml restart

# Stop containers
docker compose -f docker-compose.prod.yml stop

# Start containers
docker compose -f docker-compose.prod.yml up -d

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build --force-recreate
```

#### Database Management

```bash
# Initialize database (already done during deployment)
docker exec homerack-backend python /app/scripts/init_database.py

# Backup database
docker exec homerack-backend tar czf /tmp/backup.tar.gz -C /app/data .
docker cp homerack-backend:/tmp/backup.tar.gz ./homerack-db-backup-$(date +%Y%m%d-%H%M%S).tar.gz

# Restore database (CAUTION: This will overwrite existing data)
docker cp ./homerack-db-backup.tar.gz homerack-backend:/tmp/
docker exec homerack-backend tar xzf /tmp/backup.tar.gz -C /app/data
docker compose -f /opt/homerack/docker-compose.prod.yml restart backend

# Access database directly (SQLite)
docker exec -it homerack-backend sqlite3 /app/data/homerack.db
# Once in sqlite: .tables, .schema, SELECT * FROM racks;, .quit
```

#### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect homerack_homerack-data
docker volume inspect homerack_homerack-uploads

# Backup volume to tar file
docker run --rm \
  -v homerack_homerack-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/homerack-data-$(date +%Y%m%d).tar.gz -C /data .

# Restore volume from tar file (CAUTION: Overwrites existing data)
docker run --rm \
  -v homerack_homerack-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/homerack-data-YYYYMMDD.tar.gz -C /data"
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker logs homerack-backend
docker logs homerack-frontend

# Check if port is already in use
netstat -tulnp | grep 8080
# or
ss -tulnp | grep 8080

# Check container health
docker inspect homerack-backend | jq '.[0].State.Health'
```

### Application Not Accessible

```bash
# Test from server itself
curl http://localhost:8080

# Test from local machine
curl http://lampadas.local:8080

# Check if containers are running
docker ps --filter name=homerack

# Check Docker network
docker network inspect homerack_homerack-network

# Test backend health directly
docker exec homerack-backend curl http://localhost:8000/health

# Test frontend can reach backend
docker exec homerack-frontend curl http://backend:8000/health
```

### Database Issues

```bash
# Check if database file exists
docker exec homerack-backend ls -lah /app/data/

# Check database file permissions
docker exec homerack-backend ls -l /app/data/homerack.db

# Reinitialize database (CAUTION: Deletes all data)
docker exec homerack-backend rm -f /app/data/homerack.db
docker exec homerack-backend python /app/scripts/init_database.py
docker compose -f /opt/homerack/docker-compose.prod.yml restart backend
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check container logs for errors
docker logs --tail 100 homerack-backend | grep -i error

# Check disk space
df -h

# Check backend worker count (currently using single worker)
docker exec homerack-backend ps aux | grep uvicorn
```

### Network Issues

```bash
# Verify containers can communicate
docker exec homerack-frontend ping -c 3 backend
docker exec homerack-frontend nslookup backend

# Check nginx configuration
docker exec homerack-frontend cat /etc/nginx/conf.d/default.conf

# Test nginx config syntax
docker exec homerack-frontend nginx -t

# Reload nginx
docker exec homerack-frontend nginx -s reload
```

## Monitoring and Maintenance

### Regular Maintenance Tasks

1. **Daily**: Check logs for errors
   ```bash
   docker logs --since 24h homerack-backend | grep -i error
   docker logs --since 24h homerack-frontend | grep -i error
   ```

2. **Weekly**: Backup database
   ```bash
   docker exec homerack-backend tar czf /tmp/backup.tar.gz -C /app/data .
   docker cp homerack-backend:/tmp/backup.tar.gz ./backups/homerack-db-$(date +%Y%m%d).tar.gz
   ```

3. **Monthly**: Review disk usage and clean up old logs
   ```bash
   docker system df
   docker system prune -f  # Remove unused containers, networks, images
   ```

4. **As Needed**: Update application
   ```bash
   cd /home/calounx/repositories/homerack
   git pull  # If using git
   ./deploy/update.sh
   ```

### Health Monitoring

The application includes built-in health check endpoints:

- **Backend Health**: http://lampadas.local:8080/health
- **API Health**: http://lampadas.local:8080/api/health

Health checks run every 30 seconds with 3 retry attempts.

### Log Locations

- **Container Logs**: `docker logs homerack-backend` or `docker logs homerack-frontend`
- **Systemd Logs**: `journalctl -u homerack`
- **Application Logs**: JSON format to stdout (captured by Docker)

## Known Issues and Limitations

1. **Single Worker**: Backend runs with single uvicorn worker to avoid Pydantic schema multiprocessing issues. This is suitable for test/development but may need adjustment for heavy production loads.

2. **SQLite Database**: Using SQLite for simplicity. For production with high concurrency, consider PostgreSQL or MySQL.

3. **No Redis**: Caching and rate limiting using in-memory storage. For multi-instance deployments, configure Redis.

4. **No HTTPS**: Application serves HTTP only. For production, add nginx reverse proxy with SSL/TLS certificates.

5. **No Authentication**: API endpoints are open. Add authentication/authorization for production use.

## Next Steps

### Optional Enhancements

1. **Add HTTPS/SSL**:
   - Install certbot for Let's Encrypt certificates
   - Configure nginx reverse proxy with SSL termination
   - Update CORS origins in docker-compose.prod.yml

2. **Add Redis** for distributed caching:
   ```yaml
   # Add to docker-compose.prod.yml
   redis:
     image: redis:7-alpine
     volumes:
       - redis-data:/data
   ```

3. **Add PostgreSQL** for better concurrency:
   ```yaml
   # Add to docker-compose.prod.yml
   postgres:
     image: postgres:16-alpine
     environment:
       POSTGRES_DB: homerack
       POSTGRES_USER: homerack
       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
     volumes:
       - postgres-data:/var/lib/postgresql/data
   ```

4. **Add Monitoring**:
   - Prometheus + Grafana for metrics
   - ELK stack for log aggregation
   - Uptime monitoring service

5. **Automate Backups**:
   - Cron job for daily database backups
   - Off-site backup storage
   - Automated backup testing

## Support

For issues or questions:

1. Check this documentation
2. Review logs: `./deploy/monitor.sh`
3. Check Docker status: `docker ps`
4. Review deployment README: `/home/calounx/repositories/homerack/deploy/README.md`

## Changelog

- **2026-01-12**: Initial production deployment
  - Deployed to lampadas.local:8080
  - Frontend and backend containers running
  - Database initialized
  - Systemd service installed
  - Health checks passing
  - All features operational

---

**Deployment Status**: SUCCESSFUL ✓

**Deployed By**: Automated deployment script

**Deployment Date**: 2026-01-12

**Application Version**: 1.0.1
