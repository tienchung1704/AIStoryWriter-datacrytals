#!/bin/bash
# Setup sudoers for journalctl access without password

echo "Setting up sudoers for AIStoryWriter bot..."

# Create sudoers file
sudo tee /etc/sudoers.d/aistorywriter-bot > /dev/null <<EOF
# Allow netviet user to run journalctl for aistorywriter-bot without password
netviet ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u aistorywriter-bot *
EOF

# Set correct permissions
sudo chmod 0440 /etc/sudoers.d/aistorywriter-bot

# Verify
if sudo visudo -c -f /etc/sudoers.d/aistorywriter-bot; then
    echo "✅ Sudoers setup successfully!"
    echo "Bot can now run: sudo journalctl -u aistorywriter-bot -n 80"
else
    echo "❌ Error in sudoers file!"
    sudo rm /etc/sudoers.d/aistorywriter-bot
fi
