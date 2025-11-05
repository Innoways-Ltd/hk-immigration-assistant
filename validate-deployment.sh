#!/bin/bash

# HK Immigration Assistant - Deployment Validation Script
# This script validates the deployment configuration without actually deploying

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo "=========================================="
echo "HK Immigration Assistant"
echo "Deployment Configuration Validation"
echo "=========================================="
echo ""

# Check files
echo "Checking deployment files..."
echo ""

files_to_check=(
    "deploy.sh:Docker deployment script"
    "deploy-local.sh:Local deployment script"
    "stop.sh:Docker stop script"
    "stop-local.sh:Local stop script"
    "docker-compose.yml:Docker Compose configuration"
    ".env.example:Environment variables template"
    "agent/Dockerfile:Agent Dockerfile"
    "ui/Dockerfile:UI Dockerfile"
    "agent/.dockerignore:Agent Docker ignore"
    "ui/.dockerignore:UI Docker ignore"
)

for item in "${files_to_check[@]}"; do
    file="${item%%:*}"
    desc="${item##*:}"
    if [ -f "$file" ]; then
        print_info "$desc ($file)"
    else
        print_error "$desc ($file) - MISSING"
    fi
done

echo ""
echo "Checking environment configuration..."
echo ""

if [ -f ".env" ]; then
    print_info ".env file exists"
    
    source .env
    
    # Check required variables
    if [ ! -z "$AZURE_OPENAI_API_KEY" ]; then
        print_info "AZURE_OPENAI_API_KEY is set"
    else
        print_error "AZURE_OPENAI_API_KEY is not set"
    fi
    
    if [ ! -z "$AZURE_OPENAI_ENDPOINT" ]; then
        print_info "AZURE_OPENAI_ENDPOINT is set"
    else
        print_error "AZURE_OPENAI_ENDPOINT is not set"
    fi
    
    if [ ! -z "$AZURE_OPENAI_DEPLOYMENT" ]; then
        print_info "AZURE_OPENAI_DEPLOYMENT is set"
    else
        print_error "AZURE_OPENAI_DEPLOYMENT is not set"
    fi
    
    # Check optional variables
    if [ ! -z "$GOOGLE_MAPS_API_KEY" ]; then
        print_info "GOOGLE_MAPS_API_KEY is set (optional)"
    else
        print_warning "GOOGLE_MAPS_API_KEY is not set (optional)"
    fi
else
    print_error ".env file not found"
    print_info "Copy .env.example to .env and fill in your values"
fi

echo ""
echo "Checking deployment prerequisites..."
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    print_info "Docker is installed ($(docker --version))"
    
    if command -v docker-compose &> /dev/null; then
        print_info "Docker Compose is installed ($(docker-compose --version))"
    elif docker compose version &> /dev/null; then
        print_info "Docker Compose is installed ($(docker compose version))"
    else
        print_warning "Docker Compose is not installed"
    fi
else
    print_warning "Docker is not installed (required for deploy.sh)"
fi

# Check Python
if command -v python3.11 &> /dev/null; then
    print_info "Python 3.11 is installed ($(python3.11 --version))"
elif command -v python3.12 &> /dev/null; then
    print_info "Python 3.12 is installed ($(python3.12 --version))"
else
    print_warning "Python 3.11/3.12 is not installed (required for deploy-local.sh)"
fi

# Check Node.js
if command -v node &> /dev/null; then
    print_info "Node.js is installed ($(node --version))"
else
    print_warning "Node.js is not installed (required for deploy-local.sh)"
fi

# Check pnpm
if command -v pnpm &> /dev/null; then
    print_info "pnpm is installed ($(pnpm --version))"
else
    print_warning "pnpm is not installed (required for deploy-local.sh)"
fi

echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""
echo "Deployment options available:"
echo ""

if command -v docker &> /dev/null; then
    echo "  1. Docker deployment (recommended for production)"
    echo "     Command: ./deploy.sh"
    echo ""
fi

if command -v python3.11 &> /dev/null || command -v python3.12 &> /dev/null; then
    if command -v node &> /dev/null; then
        echo "  2. Local deployment (for development)"
        echo "     Command: ./deploy-local.sh"
        echo ""
    fi
fi

if [ -f ".env" ]; then
    print_info "Ready to deploy!"
else
    print_error "Please create .env file before deploying"
    echo "  cp .env.example .env"
    echo "  # Edit .env and fill in your API keys"
fi

echo ""
