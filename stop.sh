#!/bin/bash

# HK Immigration Assistant - Stop Script

set -e

GREEN='\033[0;32m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_info "Stopping HK Immigration Assistant services..."

if command -v docker-compose &> /dev/null; then
    docker-compose down
else
    docker compose down
fi

print_info "Services stopped successfully ✓"
