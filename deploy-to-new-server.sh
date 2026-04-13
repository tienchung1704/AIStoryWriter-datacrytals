#!/bin/bash

# Script deploy AIStoryWriter sang server mới
# Server: netviet@192.168.1.20
# Target: /data/subtitle/AIStoryWriter/

set -e

SERVER="netviet@192.168.1.20"
TARGET_DIR="/data/subtitle/AIStoryWriter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "AIStoryWriter Deployment"
echo "Server: $SERVER"
echo "Target: $TARGET_DIR"
echo "=========================================="

# Bước 1: Tạo thư mục trên server
echo ""
echo "[1/4] Creating directory on server..."
echo "Please run this command on the server first if directory doesn't exist:"
echo "  ssh $SERVER"
echo "  sudo mkdir -p $TARGET_DIR && sudo chown -R netviet:netviet $TARGET_DIR"
echo ""
read -p "Press Enter when ready to continue..."
ssh $SERVER "mkdir -p $TARGET_DIR"

# Bước 2: Sync project
echo ""
echo "[2/4] Syncing AIStoryWriter..."
rsync -avz --progress \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'Logs/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '*.log' \
  "$SCRIPT_DIR/" \
  "$SERVER:$TARGET_DIR/"

# Bước 3: Copy file .env template
echo ""
echo "[3/4] Copying environment template..."
if [ -f "$SCRIPT_DIR/.env.prod" ]; then
    scp "$SCRIPT_DIR/.env.prod" "$SERVER:$TARGET_DIR/.env.template"
    echo "Copied .env.prod as .env.template"
fi

# Bước 4: Kiểm tra kết quả
echo ""
echo "[4/4] Verifying deployment..."
ssh $SERVER "ls -lh $TARGET_DIR/ | head -20"

echo ""
echo "=========================================="
echo "✓ AIStoryWriter deployed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH to server: ssh $SERVER"
echo "2. Go to project: cd $TARGET_DIR"
echo "3. Create .env file:"
echo "   cp .env.template .env"
echo "   nano .env"
echo "4. Setup virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "5. Create Logs directory:"
echo "   mkdir -p Logs"
echo "6. Start with PM2:"
echo "   pm2 start ecosystem.config.js"
echo "   pm2 save"
echo "=========================================="
