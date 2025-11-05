#!/bin/bash

# HK Immigration Assistant - Local Deployment Script (No Docker)
# This script deploys the application locally without Docker

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
    
    # Check Python
    if ! command -v python3.11 &> /dev/null && ! command -v python3.12 &> /dev/null; then
        print_error "Python 3.11 or 3.12 is not installed. Please install Python first."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check pnpm
    if ! command -v pnpm &> /dev/null; then
        print_warning "pnpm is not installed. Installing pnpm..."
        npm install -g pnpm
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        print_error ".env file not found. Please create .env file with required variables."
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
    
    print_info "All required environment variables are set ✓"
}

install_agent_dependencies() {
    print_info "Installing agent dependencies..."
    
    cd agent
    
    # Check if poetry is installed
    if command -v poetry &> /dev/null; then
        print_info "Using Poetry to install dependencies..."
        poetry install --no-root
    else
        print_info "Poetry not found. Using pip to install dependencies..."
        
        # Use python3.11 or python3.12
        if command -v python3.12 &> /dev/null; then
            PYTHON_CMD=python3.12
        else
            PYTHON_CMD=python3.11
        fi
        
        # Install required packages
        $PYTHON_CMD -m pip install --upgrade pip
        $PYTHON_CMD -m pip install \
            langchain \
            langchain-openai \
            langgraph \
            fastapi \
            uvicorn \
            python-dotenv \
            aiohttp \
            copilotkit
    fi
    
    cd ..
    print_info "Agent dependencies installed ✓"
}

install_ui_dependencies() {
    print_info "Installing UI dependencies..."
    
    cd ui
    pnpm install
    cd ..
    
    print_info "UI dependencies installed ✓"
}

start_agent() {
    print_info "Starting agent service..."
    
    cd agent
    
    # Determine Python command
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD=python3.12
    else
        PYTHON_CMD=python3.11
    fi
    
    # Start agent in background
    nohup $PYTHON_CMD -c "from immigration.demo import main; main()" > ../agent.log 2>&1 &
    AGENT_PID=$!
    echo $AGENT_PID > ../agent.pid
    
    cd ..
    
    print_info "Agent started with PID: $AGENT_PID"
}

start_ui() {
    print_info "Starting UI service..."
    
    cd ui
    
    # Start UI in background
    nohup pnpm dev > ../ui.log 2>&1 &
    UI_PID=$!
    echo $UI_PID > ../ui.pid
    
    cd ..
    
    print_info "UI started with PID: $UI_PID"
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
            print_info "Check logs with: tail -f agent.log"
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
            print_info "Check logs with: tail -f ui.log"
            exit 1
        fi
        
        sleep 2
    done
}

show_status() {
    print_info "Deployment Status:"
    echo ""
    
    if [ -f agent.pid ]; then
        AGENT_PID=$(cat agent.pid)
        echo "  Agent PID: $AGENT_PID"
    fi
    
    if [ -f ui.pid ]; then
        UI_PID=$(cat ui.pid)
        echo "  UI PID: $UI_PID"
    fi
    
    echo ""
    print_info "Application URLs:"
    echo "  - Agent API: http://localhost:8000"
    echo "  - Agent Docs: http://localhost:8000/docs"
    echo "  - UI: http://localhost:3000"
    echo ""
    print_info "View logs:"
    echo "  - Agent: tail -f agent.log"
    echo "  - UI: tail -f ui.log"
    echo ""
    print_info "Stop services:"
    echo "  - ./stop-local.sh"
    echo ""
}

# Main deployment flow
main() {
    echo "=========================================="
    echo "HK Immigration Assistant - Local Deployment"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    check_env_variables
    install_agent_dependencies
    install_ui_dependencies
    start_agent
    start_ui
    check_health
    show_status
    
    print_info "Deployment completed successfully! 🎉"
}

# Run main function
main
