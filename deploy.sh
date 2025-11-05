#!/bin/bash

# HK Immigration Assistant - Deployment Script
# This script automates the deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        print_error ".env file not found. Please copy .env.example to .env and fill in your values."
        exit 1
    fi
    
    print_info "All prerequisites met ✓"
}

check_env_variables() {
    print_info "Checking environment variables..."
    
    source .env
    
    required_vars=(
        "AZURE_OPENAI_API_KEY"
        "AZURE_OPENAI_ENDPOINT"
        "AZURE_OPENAI_DEPLOYMENT"
    )
    
    # Optional variables (warn if missing)
    optional_vars=(
        "GOOGLE_MAPS_API_KEY"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    # Check optional variables
    missing_optional=()
    for var in "${optional_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_optional+=("$var")
        fi
    done
    
    if [ ${#missing_optional[@]} -ne 0 ]; then
        print_warning "Optional environment variables not set:"
        for var in "${missing_optional[@]}"; do
            echo "  - $var"
        done
        echo ""
    fi
    
    print_info "All required environment variables are set ✓"
}

build_images() {
    print_info "Building Docker images..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
    else
        docker compose build --no-cache
    fi
    
    print_info "Docker images built successfully ✓"
}

start_services() {
    print_info "Starting services..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    print_info "Services started successfully ✓"
}

check_health() {
    print_info "Waiting for services to be healthy..."
    
    # Wait for agent
    print_info "Checking agent health..."
    max_retries=30
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
            print_info "Agent is healthy ✓"
            break
        fi
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -eq $max_retries ]; then
            print_error "Agent failed to start"
            print_info "Check logs with: docker logs hk-immigration-agent"
            exit 1
        fi
        
        sleep 2
    done
    
    # Wait for UI
    print_info "Checking UI health..."
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -f http://localhost:3000 > /dev/null 2>&1; then
            print_info "UI is healthy ✓"
            break
        fi
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -eq $max_retries ]; then
            print_error "UI failed to start"
            print_info "Check logs with: docker logs hk-immigration-ui"
            exit 1
        fi
        
        sleep 2
    done
}

show_status() {
    print_info "Deployment Status:"
    echo ""
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    
    echo ""
    print_info "Application URLs:"
    echo "  - Agent API: http://localhost:8000"
    echo "  - Agent Docs: http://localhost:8000/docs"
    echo "  - UI: http://localhost:3000"
    echo ""
    print_info "View logs:"
    echo "  - Agent: docker logs -f hk-immigration-agent"
    echo "  - UI: docker logs -f hk-immigration-ui"
    echo ""
}

# Main deployment flow
main() {
    echo "=========================================="
    echo "HK Immigration Assistant - Deployment"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    check_env_variables
    build_images
    start_services
    check_health
    show_status
    
    print_info "Deployment completed successfully! 🎉"
}

# Run main function
main
