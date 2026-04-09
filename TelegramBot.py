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
ADMIN_USER_IDS = os.getenv('ADMIN_USER_IDS', '').split(',')  # Admin user IDs for bot control


class StoryGenerator:
    """Handle story generation tasks"""
    
    def __init__(self):
        self.active_jobs = {}
        self.job_processes = {}  # Track process objects
        self.retry_counts = {}  # Track retry counts per job
    
    async def monitor_retries(self, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE, log_file: str):
        """Monitor log file for excessive retries and alert user"""
        last_retry_count = 0
        retry_warning_sent = False
        
        while user_id in self.active_jobs:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if not os.path.exists(log_file):
                    continue
                
                # Count retry attempts in log
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    retry_count = content.count('Reattempting Output')
                    retry_count += content.count('JSON Error during parsing')
                
                # Check if stuck in retry loop
                if retry_count > last_retry_count:
                    last_retry_count = retry_count
                    
                    # Alert if too many retries
                    if retry_count >= 5 and not retry_warning_sent:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⚠️ Cảnh báo: Đã thử lại {retry_count} lần!\n\n"
                                 "Bot có thể đang gặp vấn đề với context quá dài.\n\n"
                                 "💡 Dùng /kill để dừng và thử lại với prompt ngắn hơn."
                        )
                        retry_warning_sent = True
                    
                    # Critical alert
                    if retry_count >= 10:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"🚨 CẢNH BÁO NGHIÊM TRỌNG!\n\n"
                                 f"Bot đã thử lại {retry_count} lần và có thể bị treo.\n\n"
                                 "Đề xuất:\n"
                                 "1. Dùng /kill để dừng ngay\n"
                                 "2. Thử lại với prompt ngắn hơn\n"
                                 "3. Hoặc đợi bot tự dừng sau 10 lần thử"
                        )
                        break
                        
            except Exception as e:
                logger.error(f"Error monitoring retries: {e}")
                break
    
    async def generate_story(self, prompt: str, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Generate story from prompt"""
        try:
            # Create temporary prompt file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Prepare output filename
            output_file = f"Stories/Telegram_{user_id}_{chat_id}"
            
            # Build command - use Ollama llama3
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
                '-TranslatorModel', 'ollama://llama3',
                '-NoChapterRevision'  # Disable revisions to speed up
            ]
            
            # Send status update
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏳ Đang tạo story... Quá trình này có thể mất vài phút đến vài giờ tùy độ dài story.\n\n"
                     "💡 Dùng /log để xem tiến trình\n"
                     "💡 Dùng /kill để dừng nếu cần"
            )
            
            # Run the story generator with real-time output
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT  # Combine stderr with stdout
            )
            
            # Store process for kill command
            self.job_processes[user_id] = process
            
            # Find log file and start monitoring
            import glob
            await asyncio.sleep(5)  # Wait for log file to be created
            log_files = glob.glob("Logs/Generation_*/Main.log")
            if log_files:
                latest_log = max(log_files, key=os.path.getmtime)
                # Start retry monitoring in background
                asyncio.create_task(self.monitor_retries(user_id, chat_id, context, latest_log))
            
            # Read output in real-time and log it
            output_lines = []
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_text = line.decode('utf-8').strip()
                output_lines.append(line_text)
                logger.info(f"Write.py: {line_text}")
            
            await process.wait()
            stdout = '\n'.join(output_lines).encode('utf-8')
            stderr = b''
            
            # Clean up
            os.unlink(prompt_file)
            if user_id in self.job_processes:
                del self.job_processes[user_id]
            
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
            elif process.returncode == -9 or process.returncode == -15:
                # Process was killed
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⛔ Story generation đã bị dừng bởi lệnh /kill"
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
        finally:
            # Cleanup
            if user_id in self.job_processes:
                del self.job_processes[user_id]


# Initialize generator
generator = StoryGenerator()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Xin chào! Tôi là AI Story Writer Bot.\n\n"
        "📝 Dùng lệnh /prompt để tạo story!\n\n"
        "Các lệnh:\n"
        "/start - Bắt đầu\n"
        "/help - Hướng dẫn\n"
        "/prompt <text> - Tạo story từ prompt\n"
        "/example - Xem ví dụ prompt\n"
        "/log - Xem tiến trình tạo story\n"
        "/status - Xem trạng thái bot\n"
        "/kill - [Admin] Dừng story đang gen\n"
        "/restart - [Admin] Restart bot\n\n"
        "Ví dụ:\n"
        "/prompt Write a short story about a magical cat"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📚 Hướng dẫn sử dụng:\n\n"
        "1. Dùng lệnh /prompt theo sau là nội dung prompt\n"
        "2. Đợi bot xử lý (có thể mất vài phút đến vài giờ)\n"
        "3. Dùng /log để xem tiến trình\n"
        "4. Nhận file story (.md) qua Telegram\n\n"
        "💡 Tips:\n"
        "- Prompt càng chi tiết, story càng hay\n"
        "- Mô tả rõ nhân vật, bối cảnh, cốt truyện\n"
        "- Có thể yêu cầu thể loại, phong cách cụ thể\n\n"
        "Ví dụ:\n"
        "/prompt Write a sci-fi story about AI discovering emotions"
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


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /log command - show recent generation logs"""
    user_id = update.effective_user.id
    
    # Check if user has active job
    if user_id not in generator.active_jobs:
        await update.message.reply_text(
            "ℹ️ Bạn không có story nào đang được tạo."
        )
        return
    
    # Find the latest log file for this user
    try:
        import glob
        import os
        
        # Look for log files in Logs directory
        log_pattern = "Logs/Generation_*/Main.log"
        log_files = glob.glob(log_pattern)
        
        if not log_files:
            await update.message.reply_text(
                "ℹ️ Chưa có log file nào. Story đang được khởi tạo...\n\n"
                "💡 Thử lại sau vài giây."
            )
            return
        
        # Get the most recent log file
        latest_log = max(log_files, key=os.path.getmtime)
        
        # Read last 50 lines from the log file
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        # Filter for important progress messages
        relevant_lines = []
        for line in recent_lines:
            line = line.strip()
            # Look for progress indicators
            if any(keyword in line.lower() for keyword in [
                'chapter', 'outline', 'generating', 'writing', 
                'stage', 'scene', 'found', 'using model', 'done',
                'feedback', 'revision', 'scrub', 'translat'
            ]):
                # Clean up the line - remove timestamps and log levels
                # Format: [level] [timestamp] message
                parts = line.split(']', 2)
                if len(parts) >= 3:
                    msg = parts[2].strip()
                    relevant_lines.append(msg)
                elif len(parts) == 2:
                    msg = parts[1].strip()
                    relevant_lines.append(msg)
                else:
                    relevant_lines.append(line)
        
        if relevant_lines:
            # Get last 20 relevant lines
            log_text = '\n'.join(relevant_lines[-20:])
            await update.message.reply_text(
                f"📋 Tiến trình gần đây:\n\n```\n{log_text[:3500]}\n```\n\n"
                f"📁 Log file: {os.path.basename(os.path.dirname(latest_log))}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "ℹ️ Chưa có logs chi tiết. Story đang được khởi tạo...\n\n"
                "💡 Thử lại sau vài giây."
            )
            
    except FileNotFoundError:
        await update.message.reply_text(
            "❌ Không tìm thấy log file.\n\n"
            "💡 Story có thể chưa bắt đầu hoặc đã hoàn thành."
        )
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        await update.message.reply_text(
            f"❌ Lỗi khi đọc logs: {str(e)}\n\n"
            "💡 Vui lòng thử lại sau."
        )


async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /prompt command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Get prompt from command arguments
    prompt_text = ' '.join(context.args)
    
    if not prompt_text:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp prompt!\n\n"
            "Cách dùng:\n"
            "/prompt Your story prompt here\n\n"
            "Ví dụ:\n"
            "/prompt Write a short story about a magical cat"
        )
        return
    
    # Check if user is allowed (if whitelist is configured)
    if ALLOWED_USER_IDS and ALLOWED_USER_IDS[0] != '':
        if str(user_id) not in ALLOWED_USER_IDS:
            await update.message.reply_text(
                "❌ Bạn không có quyền sử dụng bot này."
            )
            return
    
    # Validate prompt length
    if len(prompt_text) > MAX_PROMPT_LENGTH:
        await update.message.reply_text(
            f"❌ Prompt quá dài! Tối đa {MAX_PROMPT_LENGTH} ký tự.\n"
            f"Prompt của bạn: {len(prompt_text)} ký tự"
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
        f"📝 Prompt: {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}\n\n"
        "⏳ Bắt đầu tạo story...\n\n"
        "💡 Dùng /log để xem tiến trình"
    )
    
    # Generate story in background
    try:
        await generator.generate_story(prompt_text, user_id, chat_id, context)
    finally:
        # Remove from active jobs
        if user_id in generator.active_jobs:
            del generator.active_jobs[user_id]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - now just show help"""
    await update.message.reply_text(
        "ℹ️ Để tạo story, vui lòng dùng lệnh /prompt\n\n"
        "Ví dụ:\n"
        "/prompt Write a short story about a magical cat\n\n"
        "Các lệnh khác:\n"
        "/help - Xem hướng dẫn\n"
        "/example - Xem ví dụ prompt\n"
        "/log - Xem tiến trình"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show bot status"""
    active_count = len(generator.active_jobs)
    
    status_text = "🤖 Trạng thái Bot:\n\n"
    
    if active_count == 0:
        status_text += "✅ Bot đang rảnh, sẵn sàng nhận request\n"
    else:
        status_text += f"⏳ Đang xử lý {active_count} story\n\n"
        status_text += "Danh sách:\n"
        for user_id in generator.active_jobs:
            status_text += f"- User ID: {user_id}\n"
    
    # Check system resources
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        status_text += f"\n💻 Tài nguyên:\n"
        status_text += f"- CPU: {cpu_percent}%\n"
        status_text += f"- RAM: {memory.percent}%\n"
    except:
        pass
    
    await update.message.reply_text(status_text)


async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kill command - stop current story generation"""
    user_id = update.effective_user.id
    
    if user_id not in generator.active_jobs:
        await update.message.reply_text(
            "ℹ️ Bạn không có story nào đang được tạo."
        )
        return
    
    # Kill the process
    if user_id in generator.job_processes:
        process = generator.job_processes[user_id]
        try:
            process.kill()
            await update.message.reply_text(
                "⛔ Đã dừng story generation!\n\n"
                "Bạn có thể tạo story mới bằng /prompt"
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi khi dừng process: {str(e)}"
            )
    else:
        await update.message.reply_text(
            "⚠️ Không tìm thấy process để dừng."
        )
    
    # Clean up
    if user_id in generator.active_jobs:
        del generator.active_jobs[user_id]
    if user_id in generator.job_processes:
        del generator.job_processes[user_id]


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restart command - restart the bot"""
    await update.message.reply_text(
        "🔄 Đang restart bot...\n\n"
        "Bot sẽ offline trong vài giây."
    )
    
    # Kill all active jobs first
    for user_id in list(generator.job_processes.keys()):
        try:
            generator.job_processes[user_id].kill()
        except:
            pass
    
    # Exit the bot - systemd or supervisor should restart it
    logger.info("Bot restart requested by user")
    os._exit(0)


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
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("kill", kill_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("prompt", prompt_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
