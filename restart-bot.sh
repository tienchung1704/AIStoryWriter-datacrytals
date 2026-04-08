#!/bin/bash
# Restart the Telegram bot service

echo "🔄 Restarting AIStoryWriter Telegram Bot..."
sudo systemctl restart aistorywriter-bot

echo "✅ Bot restarted!"
echo ""
echo "📋 Check status:"
echo "   sudo systemctl status aistorywriter-bot"
echo ""
echo "📊 View logs:"
echo "   sudo journalctl -u aistorywriter-bot -f"
