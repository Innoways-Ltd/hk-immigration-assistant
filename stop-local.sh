#!/bin/bash

# HK Immigration Assistant - Stop Local Services

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info "Stopping HK Immigration Assistant services..."

# Stop agent
if [ -f agent.pid ]; then
    AGENT_PID=$(cat agent.pid)
    if ps -p $AGENT_PID > /dev/null 2>&1; then
        kill $AGENT_PID
        print_info "Agent stopped (PID: $AGENT_PID)"
    else
        print_warning "Agent process not found (PID: $AGENT_PID)"
    fi
    rm agent.pid
else
    print_warning "agent.pid file not found"
fi

# Stop UI
if [ -f ui.pid ]; then
    UI_PID=$(cat ui.pid)
    if ps -p $UI_PID > /dev/null 2>&1; then
        kill $UI_PID
        print_info "UI stopped (PID: $UI_PID)"
    else
        print_warning "UI process not found (PID: $UI_PID)"
    fi
    rm ui.pid
else
    print_warning "ui.pid file not found"
fi

# Kill any remaining processes on ports 8000 and 3000
print_info "Checking for remaining processes on ports 8000 and 3000..."

# Port 8000 (agent)
AGENT_PORT_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$AGENT_PORT_PID" ]; then
    kill $AGENT_PORT_PID
    print_info "Killed process on port 8000 (PID: $AGENT_PORT_PID)"
fi

# Port 3000 (UI)
UI_PORT_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$UI_PORT_PID" ]; then
    kill $UI_PORT_PID
    print_info "Killed process on port 3000 (PID: $UI_PORT_PID)"
fi

print_info "Services stopped successfully ✓"
