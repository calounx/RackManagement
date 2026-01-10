#!/bin/bash
# Management script for HomeRack on remote server

REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
REMOTE_DIR="/home/calounx/homerack"

case "$1" in
    status)
        echo "Checking service status..."
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose ps"
        ;;
    logs)
        echo "Viewing logs (Ctrl+C to exit)..."
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose logs -f ${2:-backend}"
        ;;
    restart)
        echo "Restarting services..."
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose restart"
        echo "✓ Services restarted"
        ;;
    stop)
        echo "Stopping services..."
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose down"
        echo "✓ Services stopped"
        ;;
    start)
        echo "Starting services..."
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose up -d"
        sleep 2
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose ps"
        echo "✓ Services started"
        ;;
    update)
        echo "Updating code..."
        rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
            /home/calounx/repositories/homerack/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
        echo "✓ Code updated"
        echo "Restarting services..."
        ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose restart backend"
        echo "✓ Services restarted"
        ;;
    shell)
        echo "Opening shell in backend container..."
        ssh -t $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose exec backend /bin/bash"
        ;;
    db-shell)
        echo "Opening database shell..."
        ssh -t $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose exec backend python -c 'from app.database import SessionLocal; from app.models import *; db = SessionLocal(); print(\"Database shell ready. Use db to query.\")'"
        ;;
    test)
        echo "Testing API..."
        echo -n "Health check: "
        curl -s http://lampadas.local:8000/health | jq .
        echo -n "API root: "
        curl -s http://lampadas.local:8000/ | jq .name
        ;;
    *)
        echo "HomeRack Management Script"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  status    - Show service status"
        echo "  logs      - View logs (optionally specify service: logs backend)"
        echo "  restart   - Restart services"
        echo "  stop      - Stop services"
        echo "  start     - Start services"
        echo "  update    - Update code and restart"
        echo "  shell     - Open shell in backend container"
        echo "  db-shell  - Open database shell"
        echo "  test      - Test API endpoints"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 logs backend"
        echo "  $0 update"
        ;;
esac
