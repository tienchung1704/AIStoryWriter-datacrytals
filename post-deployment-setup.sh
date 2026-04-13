#!/bin/bash

# Script chạy trên server MỚI sau khi deploy AIStoryWriter
# Chạy trên: netviet@192.168.1.20
# Location: /data/subtitle/AIStoryWriter/

set -e

PROJECT_DIR="/home/netviet/projects/AIStoryWriter"

echo "=========================================="
echo "AIStoryWriter Post-Deployment Setup"
echo "=========================================="

cd "$PROJECT_DIR"

# Kiểm tra Python
echo ""
echo "[1/6] Checking Python..."
python3 --version
pip3 --version

# Tạo virtual environment
echo ""
echo "[2/6] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Cài dependencies
echo ""
echo "[3/6] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo "✓ Dependencies installed"

# Tạo thư mục Logs
echo ""
echo "[4/6] Creating Logs directory..."
mkdir -p Logs
echo "✓ Logs directory created"

# Kiểm tra PM2
echo ""
echo "[5/6] Checking PM2..."
if ! command -v pm2 &> /dev/null; then
    echo "PM2 not found. Installing..."
    sudo npm install -g pm2
else
    echo "✓ PM2 is installed: $(pm2 --version)"
fi

# Set permissions
echo ""
echo "[6/6] Setting permissions..."
chmod +x deploy.sh 2>/dev/null || true
chmod +x restart-bot.sh 2>/dev/null || true
chmod +x setup-sudoers.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
echo "✓ Permissions set"

echo ""
echo "=========================================="
echo "✓ Setup completed!"
echo "=========================================="
echo ""
echo "IMPORTANT: Create .env file:"
echo "  cd $PROJECT_DIR"
echo "  cp .env.template .env"
echo "  nano .env"
echo ""
echo "Required environment variables:"
echo "  - TELEGRAM_BOT_TOKEN"
echo "  - OPENROUTER_API_KEY (or other LLM API keys)"
echo "  - Other API keys as needed"
echo ""
echo "Start the bot:"
echo "  pm2 start ecosystem.config.js"
echo "  pm2 save"
echo "  pm2 startup  # Run the command it shows"
echo ""
echo "Check status:"
echo "  pm2 status"
echo "  pm2 logs AIStoryWriter"
echo "=========================================="
