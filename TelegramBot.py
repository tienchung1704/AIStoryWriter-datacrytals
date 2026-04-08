#!/usr/bin/env python3
"""
Telegram Bot for AIStoryWriter
Allows users to generate stories via Telegram
"""

import os
import sys
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import subprocess
import tempfile
import json

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Telegram Bot Token from .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Configuration
MAX_PROMPT_LENGTH = 2000
ALLOWED_USER_IDS = os.getenv('ALLOWED_USER_IDS', '').split(',')  # Comma-separated user IDs


class StoryGenerator:
    """Handle story generation tasks"""
    
    def __init__(self):
        self.active_jobs = {}
    
    async def generate_story(self, prompt: str, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Generate story from prompt"""
        try:
            # Create temporary prompt file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Prepare output filename
            output_file = f"Stories/Telegram_{user_id}_{chat_id}"
            
            # Build command
            cmd = [
                'python', 'Write.py',
                '-Prompt', prompt_file,
                '-Output', output_file,
                '-InitialOutlineModel', 'ollama://llama3',
                '-ChapterOutlineModel', 'ollama://llama3',
                '-ChapterS1Model', 'ollama://llama3',
                '-ChapterS2Model', 'ollama://llama3',
                '-ChapterS3Model', 'ollama://llama3',
                '-ChapterS4Model', 'ollama://llama3',
                '-ChapterRevisionModel', 'ollama://llama3',
                '-RevisionModel', 'ollama://llama3',
                '-EvalModel', 'ollama://llama3',
                '-InfoModel', 'ollama://llama3',
                '-ScrubModel', 'ollama://llama3',
                '-CheckerModel', 'ollama://llama3',
                '-TranslatorModel', 'ollama://llama3'
            ]
            
            # Send status update
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏳ Đang tạo story... Quá trình này có thể mất vài phút đến vài giờ tùy độ dài story."
            )
            
            # Run the story generator
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Clean up temp file
            os.unlink(prompt_file)
            
            if process.returncode == 0:
                # Story generated successfully
                story_file = f"{output_file}.md"
                json_file = f"{output_file}.json"
                
                # Read story info
                story_info = {}
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        story_info = json.load(f)
                
                # Send story file
                if os.path.exists(story_file):
                    with open(story_file, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=chat_id,
                            document=f,
                            filename=f"{story_info.get('Title', 'Story')}.md",
                            caption=f"✅ Story đã hoàn thành!\n\n📖 {story_info.get('Title', 'Untitled')}\n\n{story_info.get('Summary', '')}"
                        )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Lỗi: Không tìm thấy file story sau khi tạo."
                    )
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Lỗi khi tạo story:\n{error_msg[:500]}"
                )
                
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Lỗi: {str(e)}"
            )


# Initialize generator
generator = StoryGenerator()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Xin chào! Tôi là AI Story Writer Bot.\n\n"
        "📝 Gửi cho tôi một prompt và tôi sẽ tạo story cho bạn!\n\n"
        "Các lệnh:\n"
        "/start - Bắt đầu\n"
        "/help - Hướng dẫn\n"
        "/example - Xem ví dụ prompt\n\n"
        "Chỉ cần gửi text prompt của bạn để bắt đầu!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📚 Hướng dẫn sử dụng:\n\n"
        "1. Gửi prompt của bạn (tối đa 2000 ký tự)\n"
        "2. Đợi bot xử lý (có thể mất vài phút đến vài giờ)\n"
        "3. Nhận file story (.md) qua Telegram\n\n"
        "💡 Tips:\n"
        "- Prompt càng chi tiết, story càng hay\n"
        "- Mô tả rõ nhân vật, bối cảnh, cốt truyện\n"
        "- Có thể yêu cầu thể loại, phong cách cụ thể"
    )


async def example_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /example command"""
    example = (
        "📝 Ví dụ prompt:\n\n"
        "\"Please write a story set in the Genshin Impact universe, "
        "where Alhaitham invents computers, and subsequently discovers "
        "that he is living inside of a video game. Have him then hack "
        "the game and get an API like access to the game where he can "
        "begin to control things, and cover how this affects the story "
        "that the traveler (Aether) sees.\""
    )
    await update.message.reply_text(example)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages as prompts"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    prompt = update.message.text
    
    # Check if user is allowed (if whitelist is configured)
    if ALLOWED_USER_IDS and ALLOWED_USER_IDS[0] != '':
        if str(user_id) not in ALLOWED_USER_IDS:
            await update.message.reply_text(
                "❌ Bạn không có quyền sử dụng bot này."
            )
            return
    
    # Validate prompt length
    if len(prompt) > MAX_PROMPT_LENGTH:
        await update.message.reply_text(
            f"❌ Prompt quá dài! Tối đa {MAX_PROMPT_LENGTH} ký tự.\n"
            f"Prompt của bạn: {len(prompt)} ký tự"
        )
        return
    
    # Check if user already has an active job
    if user_id in generator.active_jobs:
        await update.message.reply_text(
            "⚠️ Bạn đang có một story đang được tạo. Vui lòng đợi hoàn thành."
        )
        return
    
    # Mark job as active
    generator.active_jobs[user_id] = True
    
    # Acknowledge receipt
    await update.message.reply_text(
        "✅ Đã nhận prompt!\n\n"
        f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
        "⏳ Bắt đầu tạo story..."
    )
    
    # Generate story in background
    try:
        await generator.generate_story(prompt, user_id, chat_id, context)
    finally:
        # Remove from active jobs
        if user_id in generator.active_jobs:
            del generator.active_jobs[user_id]


def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env file!")
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("example", example_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
