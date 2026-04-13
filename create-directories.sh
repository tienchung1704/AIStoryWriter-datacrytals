#!/bin/bash

# Script tạo thư mục trên server mới
# Chạy script này TRƯỚC khi deploy

SERVER="netviet@192.168.1.20"

echo "=========================================="
echo "Creating directories on server"
echo "Server: $SERVER"
echo "=========================================="

echo ""
echo "Creating directories..."
echo "You will be prompted for password..."

ssh -t $SERVER << 'EOF'
# Tạo thư mục
sudo mkdir -p /data/subtitle/AIStoryWriter
sudo mkdir -p /data/subtitle/NovelClaw

# Chuyển quyền sở hữu
sudo chown -R netviet:netviet /data/subtitle/

# Kiểm tra
echo ""
echo "Directories created:"
ls -lh /data/subtitle/

echo ""
echo "Disk space:"
df -h /data/subtitle/
EOF

echo ""
echo "=========================================="
echo "✓ Directories created successfully!"
echo "=========================================="
echo ""
echo "Now you can run the deployment scripts:"
echo "  cd AIStoryWriter && bash deploy-to-new-server.sh"
echo "  cd NovelClaw && bash deploy-to-new-server.sh"
echo "=========================================="
