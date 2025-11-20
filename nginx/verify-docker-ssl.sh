#!/bin/bash

# ============================================================================
# Quick Docker SSL Deployment Verification
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Docker SSL Deployment Quick Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Generate SSL certificates
echo -e "${YELLOW}Step 1: Generating SSL Certificates...${NC}"
if [ ! -f "./nginx/ssl/cert.pem" ]; then
    ./scripts/generate-ssl-certs.sh
else
    echo -e "${GREEN}✓${NC} SSL certificates already exist"
fi
echo ""

# Step 2: Build uWSGI images
echo -e "${YELLOW}Step 2: Building uWSGI Images...${NC}"
./scripts/build-uwsgi-images.sh
echo -e "${GREEN}✓${NC} Images built successfully"
echo ""

# Step 3: Start services
echo -e "${YELLOW}Step 3: Starting Docker Compose Services...${NC}"
docker-compose -f docker-compose-nginx-ssl.yml up -d
echo -e "${GREEN}✓${NC} Services started"
echo ""

# Step 4: Wait for services
echo -e "${YELLOW}Step 4: Waiting for services to be ready (30s)...${NC}"
sleep 30
echo -e "${GREEN}✓${NC} Wait complete"
echo ""

# Step 5: Verify services
echo -e "${YELLOW}Step 5: Verifying Services...${NC}"
echo ""

echo -e "${BLUE}→${NC} Checking container status..."
docker-compose -f docker-compose-nginx-ssl.yml ps
echo ""

echo -e "${BLUE}→${NC} Testing HTTPS health endpoint..."
curl -k https://localhost/health
echo ""
echo ""

echo -e "${BLUE}→${NC} Testing HTTPS API endpoint..."
curl -k https://localhost/api/v1/health
echo ""
echo ""

echo -e "${BLUE}→${NC} Checking SSL certificate..."
echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | grep -A 2 "subject="
echo ""

echo -e "${BLUE}→${NC} Verifying HSTS header..."
curl -k -I https://localhost/health | grep -i "Strict-Transport-Security"
echo ""

echo -e "${BLUE}→${NC} Testing HTTP → HTTPS redirect..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
echo "HTTP response code: $HTTP_CODE (should be 301 or 302)"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Verification Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Services are accessible at:"
echo -e "  ${BLUE}HTTPS Health:${NC} https://localhost/health"
echo -e "  ${BLUE}HTTPS API:${NC} https://localhost/api/v1/health"
echo ""
echo -e "${YELLOW}To view logs:${NC} docker-compose -f docker-compose-nginx-ssl.yml logs -f"
echo -e "${YELLOW}To stop:${NC} docker-compose -f docker-compose-nginx-ssl.yml down"
echo ""
