#!/bin/bash
# Auto-detecting deployment script for HomeRack v1.0.1
# Deploys both backend (FastAPI) and frontend (React) to lampadas.local

set -e

REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
REMOTE_DIR="/home/calounx/homerack"
LOCAL_DIR="/home/calounx/repositories/homerack"

echo "========================================="
echo "HomeRack v1.0.1 Auto-Deploy"
echo "Target: $REMOTE_USER@$REMOTE_HOST"
echo "========================================="

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}[1/10] Building frontend locally...${NC}"
cd $LOCAL_DIR/frontend
npm run build
echo -e "${GREEN}✓ Frontend built${NC}"

echo -e "${BLUE}[2/10] Installing system dependencies...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip \
    tesseract-ocr poppler-utils curl jq nginx

# Install Redis
if ! command -v redis-server &> /dev/null; then
    sudo apt-get install -y redis || sudo apt-get install -y redis-server || true
fi

# Start Redis if available
if command -v redis-server &> /dev/null; then
    sudo systemctl enable redis-server 2>/dev/null || sudo systemctl enable redis 2>/dev/null || true
    sudo systemctl start redis-server 2>/dev/null || sudo systemctl start redis 2>/dev/null || true
    echo "Redis installed and started"
else
    echo "Warning: Redis not available, caching will be disabled"
fi

python3 --version
ENDSSH
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${BLUE}[3/10] Creating remote directories...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR/backend $REMOTE_DIR/frontend"
echo -e "${GREEN}✓ Directories created${NC}"

echo -e "${BLUE}[4/10] Copying project files...${NC}"
# Copy backend files
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
    --exclude 'homerack.db' \
    $LOCAL_DIR/backend/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/backend/

# Copy frontend built files
rsync -avz --delete \
    $LOCAL_DIR/frontend/dist/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/frontend/dist/

# Copy documentation
rsync -avz $LOCAL_DIR/README.md $LOCAL_DIR/SETUP.md \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
echo -e "${GREEN}✓ Files copied${NC}"

echo -e "${BLUE}[5/10] Setting up Python virtual environment...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
cd $REMOTE_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
ENDSSH
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo -e "${BLUE}[6/10] Initializing database...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /home/calounx/homerack/backend
source venv/bin/activate
echo "y" | python init_db.py
deactivate
ENDSSH
echo -e "${GREEN}✓ Database initialized${NC}"

echo -e "${BLUE}[7/10] Creating systemd service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cat << 'EOF' | sudo tee /etc/systemd/system/homerack.service > /dev/null
[Unit]
Description=HomeRack API Server
After=network.target

[Service]
Type=simple
User=calounx
WorkingDirectory=/home/calounx/homerack/backend
Environment="PATH=/home/calounx/homerack/backend/venv/bin:/usr/bin:/bin"
Environment="DATABASE_URL=sqlite:////home/calounx/homerack/backend/homerack.db"
ExecStart=/home/calounx/homerack/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable homerack
ENDSSH
echo -e "${GREEN}✓ Systemd service created${NC}"

echo -e "${BLUE}[8/10] Configuring Nginx...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cat << 'EOF' | sudo tee /etc/nginx/sites-available/homerack > /dev/null
upstream homerack_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name lampadas.local 192.168.50.135;

    # Frontend root
    root /home/calounx/homerack/frontend/dist;
    index index.html;

    # API proxy - strip /api prefix before forwarding
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://homerack_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Frontend routes - SPA fallback
    location / {
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Disable logging for static assets
    location ~* \.(css|js|svg|png|jpg|jpeg|gif|ico|woff|woff2)$ {
        access_log off;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/homerack /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
ENDSSH
echo -e "${GREEN}✓ Nginx configured${NC}"

echo -e "${BLUE}[9/10] Starting backend service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
sudo systemctl restart homerack
sleep 3
sudo systemctl status homerack --no-pager | head -15
ENDSSH
echo -e "${GREEN}✓ Backend service started${NC}"

echo -e "${BLUE}[10/10] Verifying deployment...${NC}"
sleep 2

# Test backend health (through Nginx proxy)
echo "Testing backend API..."
curl -s http://lampadas.local/api/health && echo "" || echo "Warning: Backend API not responding"

# Test frontend
echo "Testing frontend..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://lampadas.local/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "Frontend: OK"
else
    echo "Warning: Frontend returned HTTP $HTTP_CODE"
fi

# Test API docs
echo "Testing API docs..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://lampadas.local/api/docs)
if [ "$HTTP_CODE" = "200" ]; then
    echo "API Docs: OK"
else
    echo "Warning: API Docs returned HTTP $HTTP_CODE"
fi

echo ""
echo "========================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Application URLs:"
echo "  - Frontend: http://lampadas.local/"
echo "  - API Docs: http://lampadas.local/api/docs"
echo "  - Health: http://lampadas.local/api/health"
echo ""
echo "Service management:"
echo "  Backend: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl {status|restart|stop|start} homerack'"
echo "  Nginx: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl {status|restart|stop|start} nginx'"
echo "  Backend Logs: ssh $REMOTE_USER@$REMOTE_HOST 'sudo journalctl -u homerack -f'"
echo ""
