#!/bin/bash

# ============================================================================
# SSL Certificate Generation Script
# ============================================================================
# Generates self-signed SSL certificates for development/testing
# For production, use Let's Encrypt or a trusted CA
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSL_DIR="${SSL_DIR:-./nginx/ssl}"
DOMAIN="${DOMAIN:-localhost}"
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORG="Arcana Cloud"
OU="Engineering"
DAYS=365

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SSL Certificate Generator${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Domain: ${GREEN}${DOMAIN}${NC}"
echo -e "Output: ${GREEN}${SSL_DIR}${NC}"
echo ""

# Create SSL directory
mkdir -p "${SSL_DIR}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --dir)
            SSL_DIR="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            exit 1
            ;;
    esac
done

# Generate private key
echo -e "${YELLOW}Generating private key...${NC}"
openssl genrsa -out "${SSL_DIR}/key.pem" 2048 2>/dev/null

# Generate certificate signing request
echo -e "${YELLOW}Generating certificate signing request...${NC}"
openssl req -new \
    -key "${SSL_DIR}/key.pem" \
    -out "${SSL_DIR}/csr.pem" \
    -subj "/C=${COUNTRY}/ST=${STATE}/L=${CITY}/O=${ORG}/OU=${OU}/CN=${DOMAIN}" \
    2>/dev/null

# Generate self-signed certificate
echo -e "${YELLOW}Generating self-signed certificate...${NC}"
openssl x509 -req \
    -days ${DAYS} \
    -in "${SSL_DIR}/csr.pem" \
    -signkey "${SSL_DIR}/key.pem" \
    -out "${SSL_DIR}/cert.pem" \
    -extfile <(printf "subjectAltName=DNS:${DOMAIN},DNS:*.${DOMAIN},DNS:localhost,IP:127.0.0.1") \
    2>/dev/null

# Set permissions
chmod 600 "${SSL_DIR}/key.pem"
chmod 644 "${SSL_DIR}/cert.pem"

# Display certificate info
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Certificate Generated Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Files created in: ${GREEN}${SSL_DIR}${NC}"
echo -e "  - ${BLUE}key.pem${NC}  (Private key)"
echo -e "  - ${BLUE}cert.pem${NC} (Certificate)"
echo -e "  - ${BLUE}csr.pem${NC}  (Certificate signing request)"
echo ""
echo -e "Certificate valid for: ${GREEN}${DAYS} days${NC}"
echo ""

# Display certificate details
echo -e "${YELLOW}Certificate Details:${NC}"
openssl x509 -in "${SSL_DIR}/cert.pem" -noout -text | grep -A 2 "Subject:"
openssl x509 -in "${SSL_DIR}/cert.pem" -noout -text | grep -A 1 "Validity"
openssl x509 -in "${SSL_DIR}/cert.pem" -noout -text | grep "DNS:"

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "1. ${BLUE}For Kubernetes deployment:${NC}"
echo -e "   kubectl create secret tls arcana-cloud-tls \\"
echo -e "     --cert=${SSL_DIR}/cert.pem \\"
echo -e "     --key=${SSL_DIR}/key.pem \\"
echo -e "     -n arcana-cloud"
echo ""
echo -e "2. ${BLUE}For Docker Compose:${NC}"
echo -e "   docker-compose -f docker-compose-nginx-ssl.yml up -d"
echo ""
echo -e "3. ${BLUE}For production (Let's Encrypt):${NC}"
echo -e "   ./scripts/setup-letsencrypt.sh --domain ${DOMAIN}"
echo ""
echo -e "${YELLOW}⚠️  Note: This is a self-signed certificate for development only!${NC}"
echo -e "${YELLOW}   For production, use Let's Encrypt or a trusted CA.${NC}"
echo ""
