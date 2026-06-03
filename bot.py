import logging
import re
import requests
import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── 0. MÁY CHỦ WEB ẢO ĐỂ LÁCH LUẬT RENDER FREE ─────────────────────────────
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"May chu Bot dang hoat dong binh thuong!")

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# ── 1. CẤU HÌNH TOKEN BOT ──────────────────────────────────────────────────
TOKEN = "8094659505:AAGg1bHEObkQWnJ5-BfL-55jTIeu4ZtWRqE"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_video_keyboard():
    keyboard = [['🎬 Hướng dẫn lấy link', 'ℹ️ Trạng thái Bot']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Dán văn bản chia sẻ Douyin vào đây...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Bot Tải Video Douyin/TikTok Siêu Tốc!**\n\n"
        "📥 Dán nguyên đoạn văn bản chia sẻ vào đây, mình sẽ lấy video không logo về ngay lập tức!",
        parse_mode="Markdown",
        reply_markup=get_video_keyboard()
    )

# ── 2. XỬ LÝ LẤY LINK VÀ TẢI VIDEO TỪ TIKWM (CHUẨN QUỐC TẾ) ───────────────
def extract_video_url(text):
    match = re.search(r'(https?://[a-zA-Z0-9./\-_?=]+)', text)
    if match:
        url = match.group(1)
        if url.endswith('/'): url = url[:-1]
        return url
    return None

def resolve_url(url):
    try:
        # BÍ KÍP Ở ĐÂY: Đeo mặt nạ iPhone để Douyin không chặn đường
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        })
        response = session.head(url, allow_redirects=True, timeout=15)
        return response.url
    except Exception:
        return url

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if user_text == '🎬 Hướng dẫn lấy link':
        await update.message.reply_text("Vào app ➔ Bấm Chia sẻ ➔ Chọn Sao chép liên kết ➔ Dán thẳng vào đây.")
        return
    elif user_text == 'ℹ️ Trạng thái Bot':
        await update.message.reply_text("🟢 Bot đang chạy trên Render. Tốc độ cao, không bị chặn!")
        return

    clean_url = extract_video_url(user_text)
    if not clean_url:
        await update.message.reply_text("⚠️ Không tìm thấy link hợp lệ. Vui lòng thử lại.")
        return

    status_msg = await update.message.reply_text("🔄 Đang nạp dữ liệu video...")

    try:
        real_url = resolve_url(clean_url)
        
        api_url = "https://tikwm.com/api/"
        response = requests.get(api_url, params={"url": real_url, "hd": "1"}, timeout=15)
        res_json = response.json()

        if res_json.get("code") != 0:
            await status_msg.edit_text(f"❌ Web nguồn từ chối phân tích: {res_json.get('msg', 'Lỗi không xác định')}")
            return

        data = res_json.get("data", {})
        video_url = data.get("hdplay") or data.get("play")
        video_title = data.get("title", "Video Downloader")

        if not video_url:
            await status_msg.edit_text("❌ Không tìm thấy file video.")
            return

        await status_msg.edit_text("🚀 Đang bắn video qua Telegram cho bạn...")
        await update.message.reply_video(
            video=video_url,
            caption=f"🎬 **{video_title}**",
            parse_mode="Markdown"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Lỗi đường truyền: {str(e)}")

# ── 3. KHỞI CHẠY BOT ───────────────────────────────────────────────────────
def main():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot đang chạy ổn định...")
    app.run_polling()

if __name__ == '__main__':
    main()
