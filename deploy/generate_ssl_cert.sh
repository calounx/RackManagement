#!/bin/bash
# SSL Certificate Generation Script for HomeRack
# Supports both self-signed certificates (testing) and Let's Encrypt (production)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HomeRack SSL Certificate Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Display menu
echo "Choose SSL certificate type:"
echo "1) Self-signed certificate (testing/development)"
echo "2) Let's Encrypt certificate (production)"
echo ""
read -p "Enter choice [1-2]: " CERT_TYPE

case $CERT_TYPE in
    1)
        echo -e "\n${YELLOW}Generating self-signed certificate...${NC}"

        # Get domain name
        read -p "Enter domain name (e.g., lampadas.local): " DOMAIN

        # Certificate output directory
        CERT_DIR="/etc/ssl/homerack"
        mkdir -p "$CERT_DIR"

        # Generate self-signed certificate (valid for 1 year)
        openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
            -keyout "$CERT_DIR/privkey.pem" \
            -out "$CERT_DIR/fullchain.pem" \
            -subj "/C=US/ST=State/L=City/O=HomeRack/OU=IT/CN=$DOMAIN"

        # Create chain file (same as fullchain for self-signed)
        cp "$CERT_DIR/fullchain.pem" "$CERT_DIR/chain.pem"

        # Set proper permissions
        chmod 600 "$CERT_DIR/privkey.pem"
        chmod 644 "$CERT_DIR/fullchain.pem"
        chmod 644 "$CERT_DIR/chain.pem"

        echo -e "${GREEN}Self-signed certificate generated successfully!${NC}"
        echo -e "${YELLOW}Location: $CERT_DIR${NC}"
        echo ""
        echo -e "${YELLOW}Update nginx-ssl.conf with these paths:${NC}"
        echo "  ssl_certificate $CERT_DIR/fullchain.pem;"
        echo "  ssl_certificate_key $CERT_DIR/privkey.pem;"
        echo "  ssl_trusted_certificate $CERT_DIR/chain.pem;"
        echo ""
        echo -e "${YELLOW}Note: Browsers will show a security warning for self-signed certificates.${NC}"
        echo -e "${YELLOW}For production, use Let's Encrypt instead.${NC}"
        ;;

    2)
        echo -e "\n${YELLOW}Setting up Let's Encrypt certificate...${NC}"

        # Get domain and email
        read -p "Enter domain name (e.g., homerack.example.com): " DOMAIN
        read -p "Enter email address for Let's Encrypt notifications: " EMAIL

        # Check if certbot is installed
        if ! command -v certbot &> /dev/null; then
            echo -e "${YELLOW}Certbot not found. Installing...${NC}"

            # Detect OS and install certbot
            if [ -f /etc/debian_version ]; then
                apt-get update
                apt-get install -y certbot python3-certbot-nginx
            elif [ -f /etc/redhat-release ]; then
                yum install -y certbot python3-certbot-nginx
            else
                echo -e "${RED}Unsupported OS. Please install certbot manually.${NC}"
                exit 1
            fi
        fi

        # Stop nginx if running
        if systemctl is-active --quiet nginx; then
            echo -e "${YELLOW}Stopping nginx temporarily...${NC}"
            systemctl stop nginx
            RESTART_NGINX=true
        fi

        # Obtain certificate
        echo -e "${YELLOW}Requesting certificate from Let's Encrypt...${NC}"
        certbot certonly --standalone \
            -d "$DOMAIN" \
            --non-interactive \
            --agree-tos \
            --email "$EMAIL" \
            --preferred-challenges http

        # Restart nginx if it was running
        if [ "$RESTART_NGINX" = true ]; then
            echo -e "${YELLOW}Restarting nginx...${NC}"
            systemctl start nginx
        fi

        echo -e "${GREEN}Let's Encrypt certificate obtained successfully!${NC}"
        echo -e "${YELLOW}Certificate location: /etc/letsencrypt/live/$DOMAIN/${NC}"
        echo ""
        echo -e "${YELLOW}Update nginx-ssl.conf with these paths:${NC}"
        echo "  ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;"
        echo "  ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;"
        echo "  ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;"
        echo ""
        echo -e "${GREEN}Setting up automatic renewal...${NC}"

        # Create renewal cron job
        CRON_CMD="0 0,12 * * * root certbot renew --quiet --post-hook 'systemctl reload nginx'"

        if ! grep -q "certbot renew" /etc/crontab; then
            echo "$CRON_CMD" >> /etc/crontab
            echo -e "${GREEN}Automatic renewal configured (checks twice daily)${NC}"
        else
            echo -e "${YELLOW}Automatic renewal already configured${NC}"
        fi

        # Test renewal
        echo -e "${YELLOW}Testing certificate renewal...${NC}"
        certbot renew --dry-run

        echo -e "${GREEN}Certificate renewal test successful!${NC}"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update deploy/nginx-ssl.conf with your domain name"
echo "2. Update the SSL certificate paths in nginx-ssl.conf"
echo "3. Deploy with: docker-compose -f docker-compose.prod.yml up -d"
echo "4. Test HTTPS: curl -I https://$DOMAIN"
echo ""
