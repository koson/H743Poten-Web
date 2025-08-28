#!/bin/bash

# H743Poten Web Interface - Docker Test Script
# Quick test to verify Docker setup is working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test Docker installation
test_docker() {
    print_status "Testing Docker installation..."
    if command -v docker &> /dev/null; then
        if docker info > /dev/null 2>&1; then
            print_success "Docker is installed and running"
        else
            print_error "Docker is installed but not running"
            return 1
        fi
    else
        print_error "Docker is not installed"
        return 1
    fi
}

# Test Docker Compose installation
test_docker_compose() {
    print_status "Testing Docker Compose installation..."
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is installed"
    else
        print_error "Docker Compose is not installed"
        return 1
    fi
}

# Test building development image
test_build_dev() {
    print_status "Testing development image build..."
    if docker build -t h743poten-web:test -f Dockerfile.dev . > /dev/null 2>&1; then
        print_success "Development image built successfully"
        docker rmi h743poten-web:test > /dev/null 2>&1
    else
        print_error "Failed to build development image"
        return 1
    fi
}

# Test building production image
test_build_prod() {
    print_status "Testing production image build..."
    if docker build -t h743poten-web:test-prod -f Dockerfile . > /dev/null 2>&1; then
        print_success "Production image built successfully"
        docker rmi h743poten-web:test-prod > /dev/null 2>&1
    else
        print_error "Failed to build production image"
        return 1
    fi
}

# Test Docker Compose configuration
test_docker_compose_config() {
    print_status "Testing Docker Compose configuration..."
    if docker-compose config > /dev/null 2>&1; then
        print_success "Docker Compose configuration is valid"
    else
        print_error "Docker Compose configuration is invalid"
        return 1
    fi
}

# Test starting development environment
test_dev_environment() {
    print_status "Testing development environment startup..."
    
    # Start development environment
    if docker-compose --profile dev up -d h743poten-dev > /dev/null 2>&1; then
        sleep 5  # Wait for startup
        
        # Check if container is running
        if docker-compose ps | grep -q "h743poten-dev.*Up"; then
            print_success "Development environment started successfully"
            
            # Test HTTP endpoint
            sleep 2
            if curl -f http://localhost:5000/ > /dev/null 2>&1; then
                print_success "Web interface is responding"
            else
                print_error "Web interface is not responding"
            fi
            
            # Stop the environment
            docker-compose down > /dev/null 2>&1
        else
            print_error "Development container failed to start"
            docker-compose logs h743poten-dev
            docker-compose down > /dev/null 2>&1
            return 1
        fi
    else
        print_error "Failed to start development environment"
        return 1
    fi
}

# Test file permissions
test_file_permissions() {
    print_status "Testing file permissions..."
    
    if [ -x "docker-dev.sh" ]; then
        print_success "docker-dev.sh is executable"
    else
        print_error "docker-dev.sh is not executable"
        return 1
    fi
    
    if [ -x "setup_raspberry_pi.sh" ]; then
        print_success "setup_raspberry_pi.sh is executable"
    else
        print_error "setup_raspberry_pi.sh is not executable"
        return 1
    fi
}

# Test environment files
test_environment_files() {
    print_status "Testing environment files..."
    
    if [ -f ".env.example" ]; then
        print_success ".env.example exists"
    else
        print_error ".env.example is missing"
        return 1
    fi
    
    if [ -f ".env.development" ]; then
        print_success ".env.development exists"
    else
        print_error ".env.development is missing"
        return 1
    fi
}

# Main test runner
main() {
    echo "H743Poten Web Interface - Docker Test Suite"
    echo "==========================================="
    echo
    
    local failed=0
    
    test_docker || failed=1
    test_docker_compose || failed=1
    test_file_permissions || failed=1
    test_environment_files || failed=1
    test_docker_compose_config || failed=1
    test_build_dev || failed=1
    test_build_prod || failed=1
    test_dev_environment || failed=1
    
    echo
    if [ $failed -eq 0 ]; then
        print_success "All tests passed! Docker setup is ready."
        echo
        echo "Next steps:"
        echo "1. Start development environment: ./docker-dev.sh dev"
        echo "2. Start production environment: ./docker-dev.sh start"
        echo "3. Deploy to Raspberry Pi: ./setup_raspberry_pi.sh"
    else
        print_error "Some tests failed. Please check the errors above."
        exit 1
    fi
}

main "$@"
