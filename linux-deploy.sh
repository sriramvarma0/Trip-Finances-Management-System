#!/bin/bash

# ============================================================
# Trip Finances Management System - Linux/Mac Deployment
# ============================================================
# This script prepares your system, clones the repo, installs
# dependencies, and runs the app.
#
# Usage:
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/sriramvarma0/Trip-Finances-Management-System/main/linux-deploy.sh)"
#   OR
#   bash linux-deploy.sh
# ============================================================

set -e

echo "=========================================="
echo "Trip Finances - Linux/Mac Deployment"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_step() {
    echo -e "${YELLOW}→${NC} $1"
}

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    PKG_MANAGER=""
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    PKG_MANAGER="brew"
else
    echo "Unsupported OS"
    exit 1
fi

print_status "Detected OS: $OS"

# Step 1: Install Python if needed
print_step "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_step "Installing Python..."
    case $PKG_MANAGER in
        apt)
            sudo apt update && sudo apt install -y python3 python3-pip git
            ;;
        brew)
            brew install python3 git
            ;;
        yum)
            sudo yum install -y python3 python3-pip git
            ;;
        pacman)
            sudo pacman -S python pip git
            ;;
    esac
fi
print_status "Python is installed"

# Step 2: Clone repository
print_step "Cloning repository..."
cd $HOME

if [ -d "Trip-Finances-Management-System" ]; then
    print_status "Repository exists, pulling updates..."
    cd Trip-Finances-Management-System
    git pull origin main
else
    git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
    cd Trip-Finances-Management-System
fi
print_status "Repository ready"

# Step 3: Create virtual environment
print_step "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Step 4: Activate and install dependencies
print_step "Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
print_status "Dependencies installed"

# Step 5: Get local IP
print_step "Getting local IP address..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
else
    IP=$(hostname -I | awk '{print $1}')
fi
[ -z "$IP" ] && IP="<your-local-ip>"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "To start the app:"
echo "  1. cd ~/Trip-Finances-Management-System"
echo "  2. source venv/bin/activate"
echo "  3. python app.py"
echo ""
echo "Access the app:"
echo "  Local:  http://localhost:8000"
echo "  Remote: http://$IP:8000"
echo ""
echo "To keep running in background:"
echo "  nohup python app.py &"
echo ""
echo "=========================================="
echo ""

read -p "Start app now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python app.py
fi
