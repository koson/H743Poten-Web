#!/bin/bash
# H743Poten Web Interface - Easy Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    echo "H743Poten Web Interface - Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Start development environment"
    echo "  prod        Start production environment"
    echo "  build       Build all Docker images"
    echo "  stop        Stop all containers"
    echo "  restart     Restart all containers"
    echo "  logs        Show container logs"
    echo "  status      Show container status"
    echo "  clean       Clean up Docker images and containers"
    echo "  test        Run import tests"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev      # Start development server on http://localhost:5000"
    echo "  $0 prod     # Start production server on http://localhost:8080"
    echo "  $0 logs     # View application logs"
    echo ""
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to build all images
build_images() {
    print_status "Building Docker images..."
    docker-compose build h743poten-web
    docker-compose --profile dev build h743poten-dev
    print_success "Docker images built successfully!"
}

# Function to start development environment
start_dev() {
    print_status "Starting development environment..."
    docker-compose --profile dev up h743poten-dev -d
    print_success "Development server started!"
    print_status "Web interface available at: http://localhost:5000"
    print_status "Use 'docker logs h743poten-dev -f' to view live logs"
}

# Function to start production environment
start_prod() {
    print_status "Starting production environment..."
    docker-compose up h743poten-web -d
    print_success "Production server started!"
    print_status "Web interface available at: http://localhost:8080"
    print_status "Use 'docker logs h743poten-web -f' to view live logs"
}

# Function to stop all containers
stop_containers() {
    print_status "Stopping all containers..."
    docker-compose --profile dev down
    docker-compose down
    print_success "All containers stopped!"
}

# Function to restart containers
restart_containers() {
    print_status "Restarting containers..."
    stop_containers
    sleep 2
    if [ "$1" = "dev" ]; then
        start_dev
    else
        start_prod
    fi
}

# Function to show logs
show_logs() {
    print_status "Container logs:"
    echo ""
    
    if docker ps --format "table {{.Names}}" | grep -q "h743poten-dev"; then
        print_status "Development container logs:"
        docker logs h743poten-dev --tail 50
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "h743poten-web"; then
        print_status "Production container logs:"
        docker logs h743poten-web --tail 50
    fi
}

# Function to show status
show_status() {
    print_status "Container status:"
    docker ps --filter "name=h743poten" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    if docker ps --format "table {{.Names}}" | grep -q "h743poten-dev"; then
        print_success "Development server is running at http://localhost:5000"
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "h743poten-web"; then
        print_success "Production server is running at http://localhost:8080"
    fi
}

# Function to clean up
clean_up() {
    print_warning "This will remove all H743Poten containers and images. Continue? (y/N)"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        print_status "Cleaning up containers and images..."
        docker-compose --profile dev down --rmi all --volumes --remove-orphans || true
        docker-compose down --rmi all --volumes --remove-orphans || true
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to run tests
run_tests() {
    print_status "Running import tests..."
    python test_imports.py
}

# Main script logic
case "${1:-help}" in
    "dev")
        check_docker
        start_dev
        ;;
    "prod")
        check_docker
        start_prod
        ;;
    "build")
        check_docker
        build_images
        ;;
    "stop")
        check_docker
        stop_containers
        ;;
    "restart")
        check_docker
        restart_containers "${2:-prod}"
        ;;
    "logs")
        check_docker
        show_logs
        ;;
    "status")
        check_docker
        show_status
        ;;
    "clean")
        check_docker
        clean_up
        ;;
    "test")
        run_tests
        ;;
    "help"|*)
        show_help
        ;;
esac
