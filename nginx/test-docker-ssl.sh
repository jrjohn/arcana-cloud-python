#!/bin/bash

# ============================================================================
# Docker Compose SSL Deployment Test Script
# ============================================================================
# Tests and verifies the Nginx SSL proxy + uWSGI deployment
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose-nginx-ssl.yml"
SSL_DIR="./nginx/ssl"
TEST_TIMEOUT=60
HEALTH_ENDPOINT="https://localhost/health"
API_ENDPOINT="https://localhost/api/v1/health"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_test() {
    echo -e "${BLUE}→${NC} Testing: $1"
}

# Test 1: Check prerequisites
test_prerequisites() {
    print_header "Test 1: Checking Prerequisites"

    print_test "Docker is running"
    if docker info > /dev/null 2>&1; then
        print_success "Docker is running"
    else
        print_error "Docker is not running"
        return 1
    fi

    print_test "docker-compose is installed"
    if command -v docker-compose &> /dev/null; then
        print_success "docker-compose is installed ($(docker-compose --version))"
    else
        print_error "docker-compose is not installed"
        return 1
    fi

    print_test "Compose file exists"
    if [ -f "$COMPOSE_FILE" ]; then
        print_success "Compose file exists: $COMPOSE_FILE"
    else
        print_error "Compose file not found: $COMPOSE_FILE"
        return 1
    fi

    echo ""
}

# Test 2: SSL certificates
test_ssl_certificates() {
    print_header "Test 2: SSL Certificates"

    print_test "SSL directory exists"
    if [ -d "$SSL_DIR" ]; then
        print_success "SSL directory exists: $SSL_DIR"
    else
        print_info "SSL directory not found, generating certificates..."
        ./scripts/generate-ssl-certs.sh
        if [ -d "$SSL_DIR" ]; then
            print_success "SSL certificates generated successfully"
        else
            print_error "Failed to generate SSL certificates"
            return 1
        fi
    fi

    print_test "Certificate files exist"
    if [ -f "$SSL_DIR/cert.pem" ] && [ -f "$SSL_DIR/key.pem" ]; then
        print_success "Certificate files found (cert.pem, key.pem)"
    else
        print_error "Certificate files missing"
        return 1
    fi

    print_test "Certificate is valid"
    if openssl x509 -in "$SSL_DIR/cert.pem" -noout -text > /dev/null 2>&1; then
        # Get certificate expiration
        EXPIRY=$(openssl x509 -in "$SSL_DIR/cert.pem" -noout -enddate | cut -d= -f2)
        print_success "Certificate is valid (expires: $EXPIRY)"
    else
        print_error "Certificate is invalid"
        return 1
    fi

    print_test "Private key is valid"
    if openssl rsa -in "$SSL_DIR/key.pem" -check -noout > /dev/null 2>&1; then
        print_success "Private key is valid"
    else
        print_error "Private key is invalid"
        return 1
    fi

    print_test "Certificate and key match"
    CERT_MODULUS=$(openssl x509 -noout -modulus -in "$SSL_DIR/cert.pem" | openssl md5)
    KEY_MODULUS=$(openssl rsa -noout -modulus -in "$SSL_DIR/key.pem" | openssl md5)
    if [ "$CERT_MODULUS" == "$KEY_MODULUS" ]; then
        print_success "Certificate and private key match"
    else
        print_error "Certificate and private key do not match"
        return 1
    fi

    echo ""
}

# Test 3: Build images
test_build_images() {
    print_header "Test 3: Building uWSGI Images"

    print_test "Building uWSGI Docker images"
    if ./scripts/build-uwsgi-images.sh > /dev/null 2>&1; then
        print_success "uWSGI images built successfully"
    else
        print_error "Failed to build uWSGI images"
        return 1
    fi

    print_test "Verifying controller image"
    if docker images | grep -q "arcana-cloud-controller-uwsgi"; then
        print_success "Controller image exists"
    else
        print_error "Controller image not found"
        return 1
    fi

    print_test "Verifying service image"
    if docker images | grep -q "arcana-cloud-service-uwsgi"; then
        print_success "Service image exists"
    else
        print_error "Service image not found"
        return 1
    fi

    print_test "Verifying repository image"
    if docker images | grep -q "arcana-cloud-repository-uwsgi"; then
        print_success "Repository image exists"
    else
        print_error "Repository image not found"
        return 1
    fi

    echo ""
}

# Test 4: Start services
test_start_services() {
    print_header "Test 4: Starting Services"

    print_test "Stopping any existing containers"
    docker-compose -f "$COMPOSE_FILE" down -v > /dev/null 2>&1 || true
    print_success "Cleaned up existing containers"

    print_test "Starting Docker Compose services"
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        return 1
    fi

    echo ""
}

# Test 5: Container health
test_container_health() {
    print_header "Test 5: Container Health Checks"

    print_info "Waiting for containers to start (max ${TEST_TIMEOUT}s)..."
    sleep 10

    # Get all container names
    CONTAINERS=$(docker-compose -f "$COMPOSE_FILE" ps --services)

    for container in $CONTAINERS; do
        print_test "Container: $container"

        # Check if container is running
        STATUS=$(docker-compose -f "$COMPOSE_FILE" ps "$container" | tail -n +2 | awk '{print $3}')
        if echo "$STATUS" | grep -q "Up"; then
            print_success "$container is running"
        else
            print_error "$container is not running (status: $STATUS)"
            continue
        fi

        # Check container logs for errors (last 50 lines)
        ERROR_COUNT=$(docker-compose -f "$COMPOSE_FILE" logs --tail=50 "$container" 2>&1 | grep -i "error" | grep -v "error_log" | wc -l)
        if [ "$ERROR_COUNT" -eq 0 ]; then
            print_success "$container has no errors in recent logs"
        else
            print_error "$container has $ERROR_COUNT errors in recent logs"
        fi
    done

    echo ""
}

# Test 6: Network connectivity
test_network_connectivity() {
    print_header "Test 6: Network Connectivity"

    print_test "Nginx can reach controller-layer"
    if docker-compose -f "$COMPOSE_FILE" exec -T nginx-proxy wget -q -O- http://controller-layer:5000/health > /dev/null 2>&1; then
        print_success "Nginx → Controller connectivity OK"
    else
        print_error "Nginx cannot reach controller-layer"
    fi

    print_test "Controller can reach service-layer"
    if docker-compose -f "$COMPOSE_FILE" exec -T controller-layer wget -q -O- http://service-layer:5001/health > /dev/null 2>&1; then
        print_success "Controller → Service connectivity OK"
    else
        print_error "Controller cannot reach service-layer"
    fi

    print_test "Service can reach repository-layer"
    if docker-compose -f "$COMPOSE_FILE" exec -T service-layer wget -q -O- http://repository-layer:5002/health > /dev/null 2>&1; then
        print_success "Service → Repository connectivity OK"
    else
        print_error "Service cannot reach repository-layer"
    fi

    print_test "Repository can reach MySQL"
    if docker-compose -f "$COMPOSE_FILE" exec -T repository-layer nc -z mysql-db 3306; then
        print_success "Repository → MySQL connectivity OK"
    else
        print_error "Repository cannot reach MySQL"
    fi

    print_test "Services can reach Redis"
    if docker-compose -f "$COMPOSE_FILE" exec -T controller-layer nc -z redis-cache 6379; then
        print_success "Services → Redis connectivity OK"
    else
        print_error "Services cannot reach Redis"
    fi

    echo ""
}

# Test 7: SSL/TLS configuration
test_ssl_configuration() {
    print_header "Test 7: SSL/TLS Configuration"

    print_info "Waiting for services to be fully ready..."
    sleep 10

    print_test "HTTP redirects to HTTPS"
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -L http://localhost/health)
    if [ "$HTTP_RESPONSE" == "200" ]; then
        print_success "HTTP → HTTPS redirect works (status: 200)"
    else
        print_error "HTTP redirect failed (status: $HTTP_RESPONSE)"
    fi

    print_test "HTTPS endpoint is accessible"
    if curl -k -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        print_success "HTTPS endpoint is accessible"
    else
        print_error "HTTPS endpoint is not accessible"
    fi

    print_test "TLSv1.2 is supported"
    if curl --tlsv1.2 -k -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        print_success "TLSv1.2 is supported"
    else
        print_error "TLSv1.2 is not supported"
    fi

    print_test "TLSv1.3 is supported"
    if curl --tlsv1.3 -k -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        print_success "TLSv1.3 is supported"
    else
        print_info "TLSv1.3 may not be supported (system-dependent)"
    fi

    print_test "HSTS header is present"
    HSTS_HEADER=$(curl -k -s -I "$HEALTH_ENDPOINT" | grep -i "Strict-Transport-Security")
    if [ -n "$HSTS_HEADER" ]; then
        print_success "HSTS header present: $HSTS_HEADER"
    else
        print_error "HSTS header is missing"
    fi

    print_test "Security headers are present"
    HEADERS=$(curl -k -s -I "$HEALTH_ENDPOINT")

    if echo "$HEADERS" | grep -q "X-Frame-Options"; then
        print_success "X-Frame-Options header present"
    else
        print_error "X-Frame-Options header missing"
    fi

    if echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
        print_success "X-Content-Type-Options header present"
    else
        print_error "X-Content-Type-Options header missing"
    fi

    echo ""
}

# Test 8: Application endpoints
test_application_endpoints() {
    print_header "Test 8: Application Endpoints"

    print_test "Health endpoint responds"
    HEALTH_RESPONSE=$(curl -k -s "$HEALTH_ENDPOINT")
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok"; then
        print_success "Health endpoint returns healthy status"
    else
        print_error "Health endpoint response unexpected: $HEALTH_RESPONSE"
    fi

    print_test "API v1 health endpoint responds"
    API_RESPONSE=$(curl -k -s "$API_ENDPOINT")
    if [ -n "$API_RESPONSE" ]; then
        print_success "API v1 health endpoint responds"
    else
        print_error "API v1 health endpoint does not respond"
    fi

    print_test "Response content type is JSON"
    CONTENT_TYPE=$(curl -k -s -I "$API_ENDPOINT" | grep -i "Content-Type")
    if echo "$CONTENT_TYPE" | grep -q "application/json"; then
        print_success "Response content type is JSON"
    else
        print_error "Response content type is not JSON: $CONTENT_TYPE"
    fi

    echo ""
}

# Test 9: uWSGI stats
test_uwsgi_stats() {
    print_header "Test 9: uWSGI Stats Endpoints"

    print_test "Controller stats endpoint"
    CONTROLLER_STATS=$(docker-compose -f "$COMPOSE_FILE" exec -T controller-layer curl -s http://localhost:9191)
    if echo "$CONTROLLER_STATS" | grep -q "version\|workers"; then
        VERSION=$(echo "$CONTROLLER_STATS" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        print_success "Controller stats available (uWSGI version: $VERSION)"
    else
        print_error "Controller stats endpoint not responding"
    fi

    print_test "Service stats endpoint"
    SERVICE_STATS=$(docker-compose -f "$COMPOSE_FILE" exec -T service-layer curl -s http://localhost:9191)
    if echo "$SERVICE_STATS" | grep -q "version\|workers"; then
        print_success "Service stats available"
    else
        print_error "Service stats endpoint not responding"
    fi

    print_test "Repository stats endpoint"
    REPO_STATS=$(docker-compose -f "$COMPOSE_FILE" exec -T repository-layer curl -s http://localhost:9191)
    if echo "$REPO_STATS" | grep -q "version\|workers"; then
        print_success "Repository stats available"
    else
        print_error "Repository stats endpoint not responding"
    fi

    echo ""
}

# Test 10: Performance and rate limiting
test_performance() {
    print_header "Test 10: Performance and Rate Limiting"

    print_test "Response time is acceptable"
    RESPONSE_TIME=$(curl -k -s -o /dev/null -w "%{time_total}" "$HEALTH_ENDPOINT")
    if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
        print_success "Response time: ${RESPONSE_TIME}s (< 2s)"
    else
        print_error "Response time too slow: ${RESPONSE_TIME}s (> 2s)"
    fi

    print_test "Gzip compression is enabled"
    if curl -k -s -I -H "Accept-Encoding: gzip" "$API_ENDPOINT" | grep -q "Content-Encoding: gzip"; then
        print_success "Gzip compression is enabled"
    else
        print_info "Gzip compression may not be enabled (depends on response size)"
    fi

    print_test "CORS headers are present"
    CORS_HEADER=$(curl -k -s -I -H "Origin: https://example.com" "$API_ENDPOINT" | grep -i "Access-Control-Allow")
    if [ -n "$CORS_HEADER" ]; then
        print_success "CORS headers present"
    else
        print_info "CORS headers not present (may require OPTIONS request)"
    fi

    echo ""
}

# Test 11: Database connectivity
test_database_connectivity() {
    print_header "Test 11: Database Connectivity"

    print_test "MySQL is accessible"
    if docker-compose -f "$COMPOSE_FILE" exec -T mysql-db mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-root}"  # NOSONAR secrets:S6697 - CI test script > /dev/null 2>&1; then
        print_success "MySQL is accessible and responding"
    else
        print_error "MySQL is not accessible"
    fi

    print_test "Database exists"
    DB_EXISTS=$(docker-compose -f "$COMPOSE_FILE" exec -T mysql-db mysql -u root -p"${MYSQL_ROOT_PASSWORD:-root}"  # NOSONAR secrets:S6697 - CI test script -e "SHOW DATABASES LIKE 'arcana_cloud';" 2>/dev/null | wc -l)
    if [ "$DB_EXISTS" -gt 1 ]; then
        print_success "Database 'arcana_cloud' exists"
    else
        print_info "Database 'arcana_cloud' not found (may need initialization)"
    fi

    print_test "Redis is accessible"
    if docker-compose -f "$COMPOSE_FILE" exec -T redis-cache redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is accessible and responding"
    else
        print_error "Redis is not accessible"
    fi

    echo ""
}

# Test 12: Container logs
test_container_logs() {
    print_header "Test 12: Container Logs Review"

    print_info "Checking recent logs for critical issues..."

    for container in $(docker-compose -f "$COMPOSE_FILE" ps --services); do
        CRITICAL_ERRORS=$(docker-compose -f "$COMPOSE_FILE" logs --tail=100 "$container" 2>&1 | grep -i "critical\|fatal" | wc -l)

        if [ "$CRITICAL_ERRORS" -eq 0 ]; then
            print_success "$container: No critical errors"
        else
            print_error "$container: $CRITICAL_ERRORS critical errors found"
        fi
    done

    echo ""
}

# Cleanup function
cleanup() {
    print_header "Cleanup"

    print_info "Do you want to stop the services? (y/N)"
    read -r -t 10 RESPONSE || RESPONSE="n"

    if [[ "$RESPONSE" =~ ^[Yy]$ ]]; then
        print_info "Stopping services..."
        docker-compose -f "$COMPOSE_FILE" down
        print_success "Services stopped"
    else
        print_info "Services left running for manual inspection"
        echo ""
        print_info "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
        print_info "To stop: docker-compose -f $COMPOSE_FILE down"
    fi
}

# Summary function
print_summary() {
    print_header "Test Summary"

    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

    echo -e "${BLUE}Total Tests:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
    echo -e "${RED}Failed:${NC} $TESTS_FAILED"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}All Tests Passed! ✓${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${GREEN}SSL/TLS deployment is working correctly!${NC}"
        echo ""
        echo -e "Services are accessible at:"
        echo -e "  ${BLUE}HTTPS:${NC} https://localhost/api/v1/health"
        echo -e "  ${BLUE}Health:${NC} https://localhost/health"
        echo ""
        return 0
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}Some Tests Failed ✗${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo -e "Check logs for details:"
        echo -e "  docker-compose -f $COMPOSE_FILE logs -f"
        echo ""
        return 1
    fi
}

# Main execution
main() {
    clear
    print_header "Docker Compose SSL Deployment Test"
    echo -e "${YELLOW}Testing: $COMPOSE_FILE${NC}"
    echo ""

    # Run all tests
    test_prerequisites
    test_ssl_certificates
    test_build_images
    test_start_services
    test_container_health
    test_network_connectivity
    test_ssl_configuration
    test_application_endpoints
    test_uwsgi_stats
    test_performance
    test_database_connectivity
    test_container_logs

    # Print summary
    print_summary
    RESULT=$?

    # Cleanup
    echo ""
    cleanup

    exit $RESULT
}

# Trap Ctrl+C
trap 'echo -e "\n${YELLOW}Test interrupted by user${NC}"; cleanup; exit 130' INT

# Run main
main
