# Hướng dẫn cài đặt Telegram Bot cho AIStoryWriter

## Bước 1: Tạo Telegram Bot

1. Mở Telegram và tìm `@BotFather`
2. Gửi lệnh `/newbot`
3. Đặt tên cho bot (ví dụ: "AI Story Writer")
4. Đặt username cho bot (phải kết thúc bằng `bot`, ví dụ: `mystorywriter_bot`)
5. BotFather sẽ gửi cho bạn một TOKEN, copy token này

## Bước 2: Cấu hình trên Server

### 2.1. Cập nhật file .env

```bash
cd /srv/projects-deploy/AIStoryWriter
cp .env.example .env
nano .env
```

Thêm vào file `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALLOWED_USER_IDS=123456789,987654321
```

Để lấy User ID của bạn:
- Mở Telegram và tìm bot `@userinfobot`
- Gửi bất kỳ tin nhắn nào, bot sẽ trả về User ID của bạn

### 2.2. Cài đặt dependencies

```bash
source venv/bin/activate
pip install python-telegram-bot
```

## Bước 3: Chạy Bot

### Chạy trực tiếp (test):
```bash
python TelegramBot.py
```

### Chạy như service (production):

Tạo systemd service:
```bash
sudo nano /etc/systemd/system/aistorywriter-bot.service
```

Nội dung file:
```ini
[Unit]
Description=AI Story Writer Telegram Bot
After=network.target

[Service]
Type=simple
User=nguyenvanthanh
WorkingDirectory=/srv/projects-deploy/AIStoryWriter
Environment="PATH=/srv/projects-deploy/AIStoryWriter/venv/bin"
ExecStart=/srv/projects-deploy/AIStoryWriter/venv/bin/python TelegramBot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aistorywriter-bot
sudo systemctl start aistorywriter-bot
sudo systemctl status aistorywriter-bot
```

Xem logs:
```bash
sudo journalctl -u aistorywriter-bot -f
```

## Bước 4: Sử dụng Bot

1. Mở Telegram và tìm bot của bạn (username bạn đã tạo)
2. Gửi `/start` để bắt đầu
3. Gửi prompt của bạn
4. Đợi bot tạo story (có thể mất vài phút đến vài giờ)
5. Nhận file story qua Telegram

## Các lệnh Bot:

- `/start` - Bắt đầu sử dụng bot
- `/help` - Xem hướng dẫn
- `/example` - Xem ví dụ prompt

## Lưu ý:

- Bot chỉ cho phép 1 job/user tại một thời điểm
- Prompt tối đa 2000 ký tự
- Cần đảm bảo Ollama đang chạy trên server
- File story sẽ được lưu trong thư mục `Stories/`
- Có thể giới hạn user được phép dùng bot qua `ALLOWED_USER_IDS`

## Troubleshooting:

### Bot không phản hồi:
```bash
sudo systemctl status aistorywriter-bot
sudo journalctl -u aistorywriter-bot -n 50
```

### Kiểm tra Ollama:
```bash
systemctl status ollama
ollama list
```

### Test bot locally:
```bash
cd /srv/projects-deploy/AIStoryWriter
source venv/bin/activate
python TelegramBot.py
```

## Tùy chỉnh:

### Thay đổi model:
Sửa file `TelegramBot.py`, tìm dòng:
```python
'-InitialOutlineModel', 'ollama://llama3',
```
Thay `llama3` bằng model khác.

### Thay đổi giới hạn prompt:
Sửa trong `TelegramBot.py`:
```python
MAX_PROMPT_LENGTH = 2000  # Thay đổi số này
```
