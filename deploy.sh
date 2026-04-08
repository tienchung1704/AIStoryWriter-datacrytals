#!/bin/bash

# AIStoryWriter Server Deployment Script
# Quick deployment for servers with dependencies already installed

set -e  # Exit on error

echo "================================================"
echo "   AI Story Writer - Server Deploy"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

# Step 1: Check and setup .env file
print_step "Step 1: Setting up .env file..."
./scripts/check-env.sh

# Step 2: Activate venv and update dependencies
print_step "Step 2: Updating Python dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    print_success "Dependencies updated"
else
    print_error "Virtual environment not found. Please create it first: python3 -m venv venv"
    exit 1
fi

# Step 3: Quick health check
print_step "Step 3: Running health checks..."

# Check Python
if command -v python3 &> /dev/null; then
    print_success "Python: $(python3 --version)"
else
    print_error "Python not found"
    exit 1
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    print_success "Ollama: $(ollama --version)"
else
    print_error "Ollama not found"
    exit 1
fi

# Check Ollama service
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_success "Ollama service is running"
else
    print_error "Ollama service not running. Start it with: sudo systemctl start ollama"
    exit 1
fi

# Step 4: Create necessary directories
print_step "Step 4: Creating directories..."
mkdir -p Stories Prompts Logs EvalLogs
print_success "Directories ready"

# Step 5: Restart services (if running)
print_step "Step 5: Checking services..."
if systemctl is-active --quiet aistorywriter-bot 2>/dev/null; then
    print_info "Restarting Telegram Bot service..."
    sudo systemctl restart aistorywriter-bot
    print_success "Telegram Bot restarted"
else
    print_info "Telegram Bot service not running (this is OK if not using bot)"
fi

# Final summary
echo ""
echo "================================================"
echo "   Deployment Complete!"
echo "================================================"
echo ""
print_success "AIStoryWriter deployed successfully!"
echo ""
echo "Service Status:"
if systemctl is-active --quiet aistorywriter-bot 2>/dev/null; then
    echo "  Telegram Bot: Running ✓"
else
    echo "  Telegram Bot: Not running"
fi
echo ""
echo "To start Telegram Bot manually:"
echo "  python TelegramBot.py"
echo ""
echo "To check logs:"
echo "  sudo journalctl -u aistorywriter-bot -f"
echo ""
