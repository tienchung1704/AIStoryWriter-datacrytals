#!/bin/bash
# Script to restart AIStoryWriter Telegram Bot

echo "🔄 Restarting AIStoryWriter Bot..."

# Kill existing bot process
pkill -f "TelegramBot.py"
echo "✅ Killed old bot process"

# Wait a moment
sleep 2

# Start bot in background
cd ~/AIStoryWriter-datacrytals
nohup ./venv/bin/python TelegramBot.py > bot.log 2>&1 &

# Wait and check
sleep 3

# Check if bot is running
if pgrep -f "TelegramBot.py" > /dev/null; then
    echo "✅ Bot started successfully!"
    echo "📋 Process ID: $(pgrep -f TelegramBot.py)"
    echo "📄 Log file: ~/AIStoryWriter-datacrytals/bot.log"
else
    echo "❌ Bot failed to start. Check bot.log for errors:"
    tail -20 bot.log
fi
