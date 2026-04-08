# Scripts

Các script hỗ trợ deployment và quản lý project.

## check-env.sh

Script kiểm tra và tạo file `.env` từ templates.

### Sử dụng:

```bash
./scripts/check-env.sh
```

### Chức năng:

1. Kiểm tra xem `.env` đã tồn tại chưa
2. Nếu chưa có, hiển thị danh sách templates có sẵn:
   - `.env.example` - Template mặc định
   - `.env.prod` - Production configuration
   - `.env.dev` - Development configuration
   - `.env.local` - Local configuration
   - Các file `.env.*` khác
3. Cho phép chọn template để copy vào `.env`
4. Hiển thị các biến môi trường đã được set (ẩn giá trị)

### Ví dụ:

```bash
$ ./scripts/check-env.sh

ℹ Available environment templates:

  [1] .env.example (default template)
  [2] .env.prod (production)
  [3] .env.dev (development)
  [0] Create empty .env file

? Choose a template (0-3):
2

✓ .env file created from .env.prod

ℹ Current .env configuration:

  GOOGLE_API_KEY = (empty)
  TELEGRAM_BOT_TOKEN = ***
  ALLOWED_USER_IDS = ***

ℹ Remember to edit .env with your actual values if needed
```

## Tạo template .env mới

Bạn có thể tạo template riêng cho môi trường của mình:

```bash
# Tạo template cho staging
cp .env.example .env.staging
nano .env.staging

# Script sẽ tự động phát hiện và hiển thị trong danh sách
./scripts/check-env.sh
```

## Lưu ý

- File `.env` và `.env.local` sẽ KHÔNG được commit vào Git (đã có trong .gitignore)
- Các file template (`.env.example`, `.env.prod`, `.env.dev`) CÓ THỂ commit
- Không bao giờ commit API keys hoặc tokens thật vào Git
