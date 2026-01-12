# SSL/TLS Setup Guide for HomeRack

This guide explains how to configure HTTPS for HomeRack in production environments.

## Overview

HomeRack supports two SSL/TLS certificate options:
1. **Self-signed certificates** - For testing and internal networks
2. **Let's Encrypt** - For production with publicly accessible domains

## Current Setup

**lampadas.local** is currently running HTTP only. This is appropriate for local network access. If you need HTTPS, follow the instructions below.

## Prerequisites

- Root/sudo access on the server
- Domain name (for Let's Encrypt)
- DNS properly configured (for Let's Encrypt)
- Ports 80 and 443 open in firewall

## Option 1: Self-Signed Certificate (Testing/Internal)

### Generate Certificate

```bash
sudo ./deploy/generate_ssl_cert.sh
# Choose option 1 (Self-signed)
# Enter domain: lampadas.local
```

This creates a certificate valid for 1 year at `/etc/ssl/homerack/`.

### Configure Nginx

1. Update `deploy/nginx-ssl.conf`:
```nginx
server_name lampadas.local;

ssl_certificate /etc/ssl/homerack/fullchain.pem;
ssl_certificate_key /etc/ssl/homerack/privkey.pem;
ssl_trusted_certificate /etc/ssl/homerack/chain.pem;
```

2. Deploy with SSL configuration:
```bash
# Copy SSL Nginx config
sudo cp deploy/nginx-ssl.conf /etc/nginx/sites-available/homerack

# Enable site
sudo ln -sf /etc/nginx/sites-available/homerack /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Browser Warning

Self-signed certificates will show a security warning in browsers. To avoid this:

1. **Add to system trust store** (Linux):
```bash
sudo cp /etc/ssl/homerack/fullchain.pem /usr/local/share/ca-certificates/homerack.crt
sudo update-ca-certificates
```

2. **Add exception in browser** (Firefox/Chrome):
   - Visit `https://lampadas.local`
   - Click "Advanced" → "Accept the Risk and Continue"

## Option 2: Let's Encrypt (Production)

### Prerequisites

- Publicly accessible domain (e.g., `homerack.example.com`)
- DNS A record pointing to your server
- Ports 80 and 443 open

### Generate Certificate

```bash
sudo ./deploy/generate_ssl_cert.sh
# Choose option 2 (Let's Encrypt)
# Enter domain: homerack.example.com
# Enter email: admin@example.com
```

This will:
- Install certbot if needed
- Obtain certificate from Let's Encrypt
- Set up automatic renewal (checks twice daily)
- Store certificate at `/etc/letsencrypt/live/YOUR_DOMAIN/`

### Configure Nginx

1. Update `deploy/nginx-ssl.conf`:
```nginx
server_name homerack.example.com;

ssl_certificate /etc/letsencrypt/live/homerack.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/homerack.example.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/homerack.example.com/chain.pem;
```

2. Deploy with SSL configuration:
```bash
# Copy SSL Nginx config
sudo cp deploy/nginx-ssl.conf /etc/nginx/sites-available/homerack

# Enable site
sudo ln -sf /etc/nginx/sites-available/homerack /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Update Environment Variables

Update `.env` with HTTPS URLs:

```bash
CORS_ORIGINS=["https://homerack.example.com"]
ALLOWED_HOSTS=homerack.example.com
```

Restart backend:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Automatic Renewal

Let's Encrypt certificates are valid for 90 days. The setup script configures automatic renewal via cron.

**Verify renewal is configured:**
```bash
sudo crontab -l | grep certbot
```

**Test renewal (dry run):**
```bash
sudo certbot renew --dry-run
```

**Manual renewal (if needed):**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Docker Compose with Nginx

If you want to run Nginx in a Docker container:

### Create docker-compose.nginx.yml

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:1.25-alpine
    container_name: homerack-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot:ro
    depends_on:
      - backend
      - frontend
    networks:
      - homerack-network

networks:
  homerack-network:
    external: true
```

### Deploy

```bash
docker-compose -f docker-compose.prod.yml -f docker-compose.nginx.yml up -d
```

## Security Best Practices

### 1. TLS Configuration

The provided `nginx-ssl.conf` uses modern TLS settings:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS header (force HTTPS)
- OCSP stapling
- Session caching

### 2. Test SSL Configuration

Use SSL Labs to test your configuration:
```bash
# Online test
https://www.ssllabs.com/ssltest/analyze.html?d=homerack.example.com

# Command line test
docker run --rm -it nmap/nmap --script ssl-enum-ciphers -p 443 homerack.example.com
```

### 3. Security Headers

The Nginx configuration includes security headers:
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`
- `Content-Security-Policy`

### 4. Certificate Monitoring

Monitor certificate expiration:
```bash
echo | openssl s_client -servername homerack.example.com -connect homerack.example.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Troubleshooting

### Certificate Not Valid

**Problem:** Browser shows "Certificate not valid"

**Solutions:**
- Check domain name matches certificate
- Verify certificate files exist
- Check file permissions (readable by nginx user)
- Ensure correct paths in nginx config

### Let's Encrypt Rate Limits

**Problem:** "too many certificates already issued"

**Solutions:**
- Let's Encrypt has rate limits (50 certs/week per domain)
- Use staging environment for testing:
  ```bash
  certbot certonly --staging -d homerack.example.com
  ```
- Wait for rate limit to reset (weekly)

### Nginx Cannot Read Certificate

**Problem:** "Permission denied" reading certificate files

**Solutions:**
```bash
# Fix permissions
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 644 /etc/letsencrypt/live/*/chain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem

# Check nginx user can read
sudo -u www-data cat /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem
```

### HTTP to HTTPS Redirect Not Working

**Problem:** HTTP traffic not redirecting to HTTPS

**Solutions:**
- Check nginx configuration has redirect server block
- Verify port 80 is open
- Test redirect: `curl -I http://homerack.example.com`

## Migration from HTTP to HTTPS

### Step-by-Step Migration

1. **Generate certificate** (without stopping service):
```bash
sudo ./deploy/generate_ssl_cert.sh
```

2. **Test SSL configuration**:
```bash
sudo nginx -t -c /path/to/nginx-ssl.conf
```

3. **Deploy SSL configuration**:
```bash
sudo cp deploy/nginx-ssl.conf /etc/nginx/sites-available/homerack
sudo systemctl reload nginx
```

4. **Update application configuration**:
```bash
# Update .env
CORS_ORIGINS=["https://homerack.example.com"]

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend
```

5. **Test HTTPS**:
```bash
curl -I https://homerack.example.com
```

6. **Monitor logs**:
```bash
sudo tail -f /var/log/nginx/error.log
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Testing](https://www.ssllabs.com/ssltest/)

## Support

For issues specific to HomeRack SSL setup:
1. Check logs: `/var/log/nginx/error.log`
2. Verify DNS: `dig homerack.example.com`
3. Test connectivity: `telnet homerack.example.com 443`
4. Review Nginx config: `sudo nginx -t`
