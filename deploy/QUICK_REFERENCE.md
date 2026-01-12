# HomeRack Deployment - Quick Reference

## Access URLs

- **Application**: http://lampadas.local:8080
- **API Docs**: http://lampadas.local:8080/docs
- **Health**: http://lampadas.local:8080/health

## Essential Commands

### From Local Machine

```bash
cd /home/calounx/repositories/homerack

# Deploy/Update
./deploy/deploy.sh      # Full deployment
./deploy/update.sh      # Update only
./deploy/rollback.sh    # Rollback
./deploy/monitor.sh     # Status check
```

### On lampadas.local

```bash
# Service Control
sudo systemctl start|stop|restart|status homerack

# View Logs
docker logs -f homerack-backend
docker logs -f homerack-frontend
cd /opt/homerack && docker compose -f docker-compose.prod.yml logs -f

# Container Management
cd /opt/homerack
docker ps                                              # List containers
docker compose -f docker-compose.prod.yml restart      # Restart all
docker compose -f docker-compose.prod.yml down         # Stop all
docker compose -f docker-compose.prod.yml up -d        # Start all

# Database Backup
docker exec homerack-backend tar czf /tmp/backup.tar.gz -C /app/data .
docker cp homerack-backend:/tmp/backup.tar.gz ./homerack-backup-$(date +%Y%m%d).tar.gz

# Quick Health Check
curl http://localhost:8080/health
```

## Troubleshooting

```bash
# Check container status
ssh calounx@lampadas.local "docker ps --filter name=homerack"

# View errors
ssh calounx@lampadas.local "docker logs --tail 50 homerack-backend | grep -i error"

# Restart everything
ssh calounx@lampadas.local "sudo systemctl restart homerack"
```

## File Locations

- **Deployment**: /opt/homerack/
- **Database**: Docker volume homerack_homerack-data
- **Uploads**: Docker volume homerack_homerack-uploads
- **Systemd**: /etc/systemd/system/homerack.service

## Key Features

- Auto-restart on failure (systemd + Docker)
- Health checks every 30s
- Zero-downtime updates
- Persistent data (Docker volumes)
- Production logging (JSON format)

---

For detailed documentation, see: `/home/calounx/repositories/homerack/deploy/DEPLOYMENT_SUCCESS.md`
