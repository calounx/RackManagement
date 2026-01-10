#!/bin/bash
# Deployment script for HomeRack to remote server

set -e  # Exit on error

REMOTE_HOST="192.168.50.135"
REMOTE_USER="calounx"
REMOTE_DIR="/home/calounx/homerack"
LOCAL_DIR="/home/calounx/repositories/homerack"

echo "========================================="
echo "HomeRack Deployment Script"
echo "Target: $REMOTE_USER@$REMOTE_HOST"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[1/6] Installing Docker and Docker Compose...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
# Check if Docker is already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

docker --version
docker-compose --version
ENDSSH

echo -e "${GREEN}✓ Docker installed${NC}"

echo -e "${BLUE}[2/6] Creating remote directory...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}✓ Directory created${NC}"

echo -e "${BLUE}[3/6] Copying project files...${NC}"
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
    $LOCAL_DIR/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
echo -e "${GREEN}✓ Files copied${NC}"

echo -e "${BLUE}[4/6] Building Docker images...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
cd $REMOTE_DIR
docker-compose build
ENDSSH
echo -e "${GREEN}✓ Docker images built${NC}"

echo -e "${BLUE}[5/6] Initializing database...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /home/calounx/homerack
# Start database temporarily to initialize
docker-compose up -d redis
sleep 2

# Run database initialization in backend container
docker-compose run --rm backend python init_db.py << EOF
y
EOF
ENDSSH
echo -e "${GREEN}✓ Database initialized${NC}"

echo -e "${BLUE}[6/6] Starting services...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
cd $REMOTE_DIR
docker-compose up -d
sleep 3
docker-compose ps
ENDSSH
echo -e "${GREEN}✓ Services started${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "API is available at: http://192.168.50.135:8000"
echo "API Docs: http://192.168.50.135:8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && docker-compose logs -f'"
echo "  Restart: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && docker-compose restart'"
echo "  Stop: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && docker-compose down'"
echo ""
