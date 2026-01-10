#!/bin/bash
# Auto-detecting deployment script

set -e

REMOTE_HOST="lampadas.local"
REMOTE_USER="calounx"
REMOTE_DIR="/home/calounx/homerack"
LOCAL_DIR="/home/calounx/repositories/homerack"

echo "========================================="
echo "HomeRack Auto-Deploy"
echo "Target: $REMOTE_USER@$REMOTE_HOST"
echo "========================================="

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}[1/7] Installing system dependencies...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip \
    tesseract-ocr poppler-utils curl jq

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

echo -e "${BLUE}[2/7] Creating remote directory...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR/backend"
echo -e "${GREEN}✓ Directory created${NC}"

echo -e "${BLUE}[3/7] Copying project files...${NC}"
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
    --exclude 'homerack.db' \
    $LOCAL_DIR/backend/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/backend/
rsync -avz $LOCAL_DIR/README.md $LOCAL_DIR/SETUP.md \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
echo -e "${GREEN}✓ Files copied${NC}"

echo -e "${BLUE}[4/7] Setting up Python virtual environment...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
cd $REMOTE_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
ENDSSH
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo -e "${BLUE}[5/7] Initializing database...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /home/calounx/homerack/backend
source venv/bin/activate
echo "y" | python init_db.py
deactivate
ENDSSH
echo -e "${GREEN}✓ Database initialized${NC}"

echo -e "${BLUE}[6/7] Creating systemd service...${NC}"
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
ExecStart=/home/calounx/homerack/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable homerack
ENDSSH
echo -e "${GREEN}✓ Systemd service created${NC}"

echo -e "${BLUE}[7/7] Starting service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
sudo systemctl start homerack
sleep 3
sudo systemctl status homerack --no-pager | head -15
ENDSSH
echo -e "${GREEN}✓ Service started${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Testing API..."
sleep 2
curl -s http://lampadas.local:8000/health && echo "" || echo "Warning: API not responding yet"
curl -s http://lampadas.local:8000/ | jq -r .name 2>/dev/null || echo ""

echo ""
echo "API URLs:"
echo "  - Main: http://lampadas.local:8000"
echo "  - Docs: http://lampadas.local:8000/docs"
echo "  - Health: http://lampadas.local:8000/health"
echo ""
echo "Service management:"
echo "  Status: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl status homerack'"
echo "  Logs: ssh $REMOTE_USER@$REMOTE_HOST 'sudo journalctl -u homerack -f'"
echo "  Restart: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl restart homerack'"
echo "  Stop: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl stop homerack'"
echo ""
echo "Or use: ./scripts/manage.sh {status|logs|restart|stop|start|update|test}"
echo ""
