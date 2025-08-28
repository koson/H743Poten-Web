#!/bin/bash

# H743Poten Web Interface Docker Development Scripts
# Quick start commands for Docker development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[H743Poten Docker]${NC} $1"
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

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker is running"
}

# Build the Docker images
build() {
    print_status "Building H743Poten Docker images..."
    docker build -t h743poten-web:latest -f Dockerfile .
    docker build -t h743poten-web:dev -f Dockerfile.dev .
    print_success "Docker images built successfully"
}

# Run development environment
dev() {
    print_status "Starting H743Poten development environment..."
    docker-compose --profile dev up -d h743poten-dev
    print_success "Development server is running at http://localhost:5000"
    print_status "Use 'docker-compose logs -f h743poten-dev' to view logs"
}

# Run production environment
start() {
    print_status "Starting H743Poten production environment..."
    docker-compose up -d h743poten-web
    print_success "Production server is running at http://localhost:8080"
    print_status "Use 'docker-compose logs -f h743poten-web' to view logs"
}

# Stop the containers
stop() {
    print_status "Stopping H743Poten containers..."
    docker-compose down
    print_success "Containers stopped"
}

# Restart the containers
restart() {
    print_status "Restarting H743Poten containers..."
    docker-compose restart
    print_success "Containers restarted"
}

# View logs
logs() {
    if [ "$1" == "dev" ]; then
        docker-compose logs -f h743poten-dev
    else
        docker-compose logs -f h743poten-web
    fi
}

# Run a one-off development container
run-dev() {
    print_status "Running H743Poten development container..."
    docker run --rm -it -p 5000:8080 -v "$(pwd):/app" h743poten-web:dev
}

# Run a one-off production container
run-prod() {
    print_status "Running H743Poten production container..."
    docker run --rm -it -p 8080:8080 --privileged -v /dev:/dev h743poten-web:latest
}

# Clean up Docker resources
clean() {
    print_warning "This will remove all H743Poten Docker containers and images"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up Docker resources..."
        docker-compose down --rmi all --volumes --remove-orphans
        docker image prune -f
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Shell into running container
shell() {
    if [ "$1" == "dev" ]; then
        print_status "Opening shell in development container..."
        docker-compose exec h743poten-dev /bin/bash
    else
        print_status "Opening shell in production container..."
        docker-compose exec h743poten-web /bin/bash
    fi
}

# Show status
status() {
    print_status "Docker container status:"
    docker-compose ps
    echo
    print_status "Recent logs:"
    docker-compose logs --tail=10
}

# Deploy to Raspberry Pi
deploy-rpi() {
    print_status "Deploying to Raspberry Pi..."
    print_warning "Make sure you have configured SSH access to your Raspberry Pi"
    
    if [ -z "$1" ]; then
        print_error "Please provide Raspberry Pi IP address"
        echo "Usage: $0 deploy-rpi <raspberry-pi-ip>"
        exit 1
    fi
    
    RPI_IP="$1"
    
    # Create deployment archive
    print_status "Creating deployment archive..."
    tar --exclude='logs' --exclude='.git' --exclude='__pycache__' -czf h743poten-web.tar.gz .
    
    # Copy to Raspberry Pi
    print_status "Copying files to Raspberry Pi ($RPI_IP)..."
    scp h743poten-web.tar.gz pi@$RPI_IP:~/
    
    # Deploy on Raspberry Pi
    print_status "Deploying on Raspberry Pi..."
    ssh pi@$RPI_IP << 'EOF'
        # Stop existing containers
        cd ~/h743poten-web 2>/dev/null && docker-compose down 2>/dev/null || true
        
        # Extract new files
        rm -rf ~/h743poten-web
        mkdir ~/h743poten-web
        cd ~/h743poten-web
        tar -xzf ~/h743poten-web.tar.gz
        rm ~/h743poten-web.tar.gz
        
        # Build and start
        docker-compose build
        docker-compose up -d h743poten-web
        
        echo "Deployment completed successfully!"
EOF
    
    # Cleanup local archive
    rm h743poten-web.tar.gz
    
    print_success "Deployment to Raspberry Pi completed!"
    print_status "H743Poten Web Interface is now running at http://$RPI_IP:8080"
}

# Show help
show_help() {
    echo "H743Poten Web Interface Docker Commands"
    echo "======================================"
    echo
    echo "Usage: $0 [command] [options]"
    echo
    echo "Development Commands:"
    echo "  build         Build Docker images"
    echo "  dev           Start development environment (mock hardware)"
    echo "  run-dev       Run one-off development container"
    echo
    echo "Production Commands:"
    echo "  start         Start production environment"
    echo "  run-prod      Run one-off production container"
    echo
    echo "Management Commands:"
    echo "  stop          Stop all containers"
    echo "  restart       Restart containers"
    echo "  logs [dev]    View container logs (add 'dev' for development logs)"
    echo "  shell [dev]   Open shell in container (add 'dev' for development container)"
    echo "  status        Show container status and recent logs"
    echo "  clean         Remove all Docker resources"
    echo
    echo "Deployment Commands:"
    echo "  deploy-rpi <ip>  Deploy to Raspberry Pi"
    echo
    echo "Examples:"
    echo "  $0 dev                      # Start development environment"
    echo "  $0 start                    # Start production environment"
    echo "  $0 logs dev                 # View development logs"
    echo "  $0 shell                    # Open shell in production container"
    echo "  $0 deploy-rpi 192.168.1.100 # Deploy to Raspberry Pi"
    echo
}

# Main command handling
main() {
    case "${1:-}" in
        build)
            check_docker
            build
            ;;
        dev)
            check_docker
            dev
            ;;
        start)
            check_docker
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs "$2"
            ;;
        run-dev)
            check_docker
            build
            run-dev
            ;;
        run-prod)
            check_docker
            build
            run-prod
            ;;
        shell)
            shell "$2"
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        deploy-rpi)
            deploy-rpi "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
