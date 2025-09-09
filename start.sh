#!/bin/bash

# Nexus6 Healthcare Data Generator - Cross-Platform Startup Script
# Handles dependency installation and launches web interface
# Hello Optura!
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    print_status "Detected OS: $OS"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    else
        print_error "Python is not installed or not in PATH"
        print_error "Please install Python 3.9+ from https://python.org"
        exit 1
    fi
    
    # Check Python version (require 3.9+)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        print_error "Python $PYTHON_VERSION detected. Python 3.9+ is required."
        print_error "Please upgrade Python from https://python.org"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found"
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip installation..."
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        print_error "pip is not installed"
        print_error "Please install pip: $PYTHON_CMD -m ensurepip --upgrade"
        exit 1
    fi
    
    print_success "pip found"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Try to install dependencies
    if $PIP_CMD install -r requirements.txt; then
        print_success "Dependencies installed successfully"
    else
        print_warning "Failed to install some dependencies. Trying with --user flag..."
        if $PIP_CMD install --user -r requirements.txt; then
            print_success "Dependencies installed with --user flag"
        else
            print_error "Failed to install dependencies"
            print_error "Try running: $PIP_CMD install --upgrade pip"
            print_error "Then run this script again"
            exit 1
        fi
    fi
}

# Check if server is running
wait_for_server() {
    print_status "Waiting for server to start..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:5000 > /dev/null 2>&1; then
            print_success "Server is ready!"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            print_status "Still waiting for server... (attempt $attempt/$max_attempts)"
        fi
        
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_warning "Server may not be ready yet, but continuing..."
    return 1
}

# Open browser based on OS
open_browser() {
    local url="http://localhost:5000"
    print_status "Opening browser to $url"
    
    case $OS in
        "linux")
            if command -v xdg-open &> /dev/null; then
                xdg-open "$url" &
                print_success "Browser opened"
            else
                print_warning "xdg-open not found. Please open $url manually"
            fi
            ;;
        "macos")
            if command -v open &> /dev/null; then
                open "$url"
                print_success "Browser opened"
            else
                print_warning "open command not found. Please open $url manually"
            fi
            ;;
        "windows")
            if command -v start &> /dev/null; then
                start "$url"
                print_success "Browser opened"
            elif command -v cmd &> /dev/null; then
                cmd /c start "$url"
                print_success "Browser opened"
            else
                print_warning "Cannot open browser automatically. Please open $url manually"
            fi
            ;;
        *)
            print_warning "Unknown OS. Please open $url manually"
            ;;
    esac
}

# Start the web server
start_server() {
    print_status "Starting Nexus6 Healthcare Data Generator web server..."
    
    # Check if integrated_chatbot_server.py exists
    if [ ! -f "integrated_chatbot_server.py" ]; then
        print_error "integrated_chatbot_server.py not found"
        exit 1
    fi
    
    # Start server in background and capture PID
    $PYTHON_CMD integrated_chatbot_server.py &
    SERVER_PID=$!
    
    print_status "Server started with PID: $SERVER_PID"
    
    # Wait a moment for server to initialize
    sleep 3
    
    # Check if server is still running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        print_error "Server failed to start"
        exit 1
    fi
    
    # Wait for server to be ready and open browser
    if wait_for_server; then
        sleep 1  # Give server a moment more
        open_browser
    else
        print_warning "Server might not be fully ready, but opening browser anyway"
        open_browser
    fi
    
    print_success "Nexus6 Healthcare Data Generator is running!"
    echo ""
    echo "🌐 Web Interface: http://localhost:5000"
    echo "📊 Upload CSV/Excel files to analyze healthcare data"
    echo "🤖 Chat with AI models about your data"
    echo ""
    print_status "Press Ctrl+C to stop the server"
    
    # Wait for server process
    wait $SERVER_PID
}

# Cleanup function
cleanup() {
    print_status "Shutting down server..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    print_success "Server stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo "🏥 Nexus6 Healthcare Data Generator"
    echo "=================================="
    echo ""
    
    detect_os
    check_python
    check_pip
    install_dependencies
    
    echo ""
    print_status "Setup complete! Starting web server..."
    echo ""
    
    start_server
}

# Run main function
main "$@"
