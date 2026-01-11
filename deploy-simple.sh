#!/bin/bash
# Simple deployment without Docker (uses system Python and Redis)

set -e

REMOTE_HOST="192.168.50.135"
REMOTE_USER="calounx"
REMOTE_DIR="/home/calounx/homerack"
LOCAL_DIR="/home/calounx/repositories/homerack"

echo "========================================="
echo "HomeRack Simple Deployment (No Docker)"
echo "Target: $REMOTE_USER@$REMOTE_HOST"
echo "========================================="

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[1/7] Installing system dependencies...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip redis-server \
    tesseract-ocr poppler-utils
sudo systemctl enable redis-server
sudo systemctl start redis-server
ENDSSH
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${BLUE}[2/7] Creating remote directory...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}✓ Directory created${NC}"

echo -e "${BLUE}[3/7] Copying project files...${NC}"
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
    $LOCAL_DIR/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
echo -e "${GREEN}✓ Files copied${NC}"

echo -e "${BLUE}[4/7] Setting up Python virtual environment...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
cd $REMOTE_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ENDSSH
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo -e "${BLUE}[5/7] Initializing database...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /home/calounx/homerack/backend
source venv/bin/activate
python init_db.py << EOF
y
EOF
ENDSSH
echo -e "${GREEN}✓ Database initialized${NC}"

echo -e "${BLUE}[6/7] Creating systemd service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cat << 'EOF' | sudo tee /etc/systemd/system/homerack.service
[Unit]
Description=HomeRack API Server
After=network.target redis-server.service

[Service]
Type=simple
User=calounx
WorkingDirectory=/home/calounx/homerack/backend
Environment="PATH=/home/calounx/homerack/backend/venv/bin"
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
sleep 2
sudo systemctl status homerack --no-pager
ENDSSH
echo -e "${GREEN}✓ Service started${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "API is available at: http://192.168.50.135:8000"
echo "API Docs: http://192.168.50.135:8000/docs"
echo ""
echo "Service management:"
echo "  Status: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl status homerack'"
echo "  Logs: ssh $REMOTE_USER@$REMOTE_HOST 'sudo journalctl -u homerack -f'"
echo "  Restart: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl restart homerack'"
echo "  Stop: ssh $REMOTE_USER@$REMOTE_HOST 'sudo systemctl stop homerack'"
echo ""
