#!/bin/bash

# Script deploy AIStoryWriter sang server mới (dùng SCP thay vì rsync)
# Server: netviet@192.168.1.20
# Target: /data/subtitle/AIStoryWriter/

set -e

SERVER="netviet@192.168.1.20"
TARGET_DIR="/home/netviet/projects/AIStoryWriter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="/tmp/aistorywriter_deploy_$$"

echo "=========================================="
echo "AIStoryWriter Deployment (using SCP)"
echo "Server: $SERVER"
echo "Target: $TARGET_DIR"
echo "=========================================="

# Bước 1: Tạo thư mục tạm để chuẩn bị files
echo ""
echo "[1/5] Preparing files..."
mkdir -p "$TEMP_DIR"

# Copy toàn bộ project, loại trừ các thư mục không cần
echo "Copying files to temp directory..."
rsync -a --exclude='.git/' --exclude='__pycache__/' --exclude='*.pyc' \
  --exclude='.env' --exclude='Logs/' --exclude='.venv/' --exclude='venv/' \
  --exclude='*.log' --exclude='deploy-to-new-server.sh' --exclude='deploy-with-scp.sh' --exclude='create-directories.sh' \
  "$SCRIPT_DIR/" "$TEMP_DIR/" 2>/dev/null || \
cp -r "$SCRIPT_DIR"/* "$TEMP_DIR/" 2>/dev/null

# Xóa các thư mục không cần trong temp
rm -rf "$TEMP_DIR/.git" "$TEMP_DIR/__pycache__" "$TEMP_DIR/Logs" "$TEMP_DIR/.venv" "$TEMP_DIR/venv" 2>/dev/null || true
find "$TEMP_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✓ Files prepared in $TEMP_DIR"

# Bước 2: Tạo thư mục trên server
echo ""
echo "[2/5] Creating directory on server..."
ssh $SERVER "mkdir -p $TARGET_DIR"

# Bước 3: Tạo archive và upload
echo ""
echo "[3/5] Creating archive..."
cd "$TEMP_DIR"
tar czf ../aistorywriter.tar.gz .
echo "✓ Archive created"

# Bước 4: Upload archive
echo ""
echo "[4/5] Uploading to server..."
scp /tmp/aistorywriter.tar.gz $SERVER:/tmp/

# Bước 5: Extract trên server
echo ""
echo "[5/5] Extracting on server..."
ssh $SERVER << EOF
cd $TARGET_DIR
tar xzf /tmp/aistorywriter.tar.gz
rm /tmp/aistorywriter.tar.gz
ls -lh | head -20
EOF

# Cleanup
echo ""
echo "Cleaning up..."
rm -rf "$TEMP_DIR"
rm -f /tmp/aistorywriter.tar.gz

echo ""
echo "=========================================="
echo "✓ AIStoryWriter deployed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH to server: ssh $SERVER"
echo "2. Go to project: cd $TARGET_DIR"
echo "3. Run post-deployment setup:"
echo "   chmod +x post-deployment-setup.sh"
echo "   ./post-deployment-setup.sh"
echo "4. Create .env file:"
echo "   cp .env.template .env"
echo "   nano .env"
echo "5. Start with PM2:"
echo "   pm2 start ecosystem.config.js"
echo "=========================================="
