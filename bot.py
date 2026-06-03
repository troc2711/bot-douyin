import logging
import re
import requests
import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB ẢO LÁCH LUẬT RENDER ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()
threading.Thread(target=keep_alive, daemon=True).start()

TOKEN = "8094659505:AAGg1bHEObkQWnJ5-BfL-55jTIeu4ZtWRqE"

def extract_video_url(text):
    match = re.search(r'https?://v\.douyin\.com/[a-zA-Z0-9]+', text)
    return match.group(0) if match else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    clean_url = extract_video_url(text)
    
    if not clean_url:
        await update.message.reply_text("⚠️ Gửi link Douyin đi bạn!")
        return

    status = await update.message.reply_text("🔄 Đang chuyển link sang hệ thống ZSangTao...")

    try:
        # GỌI TRỰC TIẾP API CỦA ZSANGTAO (Cái này web họ dùng)
        api_url = "https://backend.zsangtao.com/api/v1/douyin/download"
        payload = {"url": clean_url}
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://zsangtao.com/"
        }
        
        # Gửi request
        res = requests.post(api_url, json=payload, headers=headers, timeout=20).json()

        if res.get("status") == "success":
            video_url = res["data"].get("video_nowatermark")
            await update.message.reply_video(video=video_url, caption="🎬 Đã tải qua ZSangTao!")
            await status.delete()
        else:
            await status.edit_text(f"❌ Web ZSangTao từ chối: {res.get('message', 'Lỗi không xác định')}")
    except Exception as e:
        await status.edit_text(f"❌ Lỗi kết nối ZSangTao: {str(e)}")

def main():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
