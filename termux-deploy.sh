#!/bin/bash

# ============================================================
# Trip Finances Management System - Termux Deployment Script
# ============================================================
# This script prepares Termux, clones the repo, installs
# dependencies, and runs the app.
#
# Usage:
#   1. Open Termux
#   2. Run: bash -c "$(curl -fsSL https://raw.githubusercontent.com/sriramvarma0/Trip-Finances-Management-System/main/termux-deploy.sh)"
#   OR
#   2. Download this file and run: bash termux-deploy.sh
# ============================================================

set -e  # Exit on error

echo "=========================================="
echo "Trip Finances - Termux Deployment"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_step() {
    echo -e "${YELLOW}→${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Update package manager
print_step "Updating package manager..."
pkg update -y > /dev/null 2>&1 && pkg upgrade -y > /dev/null 2>&1
print_status "Package manager updated"

# Step 2: Install dependencies
print_step "Installing dependencies..."
if ! command -v python &> /dev/null; then
    pkg install -y python pip git > /dev/null 2>&1
    print_status "Python, pip, and git installed"
else
    print_status "Python already installed"
fi

# Step 3: Clone repository
print_step "Cloning repository..."
cd $HOME

if [ -d "Trip-Finances-Management-System" ]; then
    print_status "Repository already exists, updating..."
    cd Trip-Finances-Management-System
    git pull origin main > /dev/null 2>&1
else
    git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git > /dev/null 2>&1
    cd Trip-Finances-Management-System
    print_status "Repository cloned"
fi

# Step 4: Install Python requirements
print_step "Installing Python dependencies..."
pip install --quiet flask flask-cors
print_status "Dependencies installed"

# Step 5: Create startup helper script
print_step "Setting up startup helper..."
mkdir -p ~/.termux/boot

cat > ~/.termux/boot/start-tripapp.sh << 'EOF'
#!/bin/bash
cd $HOME/Trip-Finances-Management-System
python app.py
EOF

chmod +x ~/.termux/boot/start-tripapp.sh
print_status "Startup helper created"

# Step 6: Get local IP
print_step "Getting device IP address..."
IP=$(ifconfig 2>/dev/null | grep -A1 "wlan0" | grep "inet addr" | awk '{print $2}' | cut -d: -f2)
if [ -z "$IP" ]; then
    IP=$(hostname -I | awk '{print $1}')
fi
if [ -z "$IP" ]; then
    IP="<your-device-ip>"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Your device IP: $IP"
echo ""
echo "To start the app, run:"
echo "  cd ~/Trip-Finances-Management-System"
echo "  python app.py"
echo ""
echo "Then open in browser:"
echo "  Local:  http://localhost:8000"
echo "  Remote: http://$IP:8000"
echo ""
echo "To run app in background:"
echo "  1. Install Termux:Boot from Play Store"
echo "  2. Allow notifications for Termux"
echo "  3. Reboot phone - app will auto-start"
echo ""
echo "=========================================="
echo ""

# Ask user if they want to start now
read -p "Start app now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Starting app..."
    echo ""
    python app.py
else
    print_status "Setup complete. You can start the app anytime with: python app.py"
fi
