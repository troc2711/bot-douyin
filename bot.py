import logging
import re
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── 1. CONFIG TOKEN ────────────────────────────────────────────────────────
TOKEN = "8094659505:AAGg1bHEObkQWnJ5-BfL-55jTIeu4ZtWRqE"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ── 2. MENU BÀN PHÍM ───────────────────────────────────────────────────────
def get_video_keyboard():
    keyboard = [['🎬 Hướng dẫn lấy link', 'ℹ️ Trạng thái Bot']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Dán văn bản chia sẻ Douyin vào đây...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Bot Tải Video Douyin Tự Động Qua ZSangTao!**\n\n"
        "📥 Bạn cứ dán nguyên đoạn text chia sẻ có chứa link Douyin vào đây, mình sẽ tự gửi sang web zsangtao.com để lấy video không logo về cho bạn!",
        parse_mode="Markdown",
        reply_markup=get_video_keyboard()
    )

# ── 3. BỘ LỌC TỰ ĐỘNG TÌM LINK ──────────────────────────────────────────────
def extract_video_url(text):
    match = re.search(r'(https?://[^\s]+)', text)
    if match:
        url = match.group(1)
        if url.endswith('/'): url = url[:-1]
        return url
    return None

# ── 4. TẬN DỤNG HỆ THỐNG ZSANGTAO.COM ───────────────────────────────────────
def get_video_from_zsangtao(douyin_url):
    try:
        # Gửi yêu cầu giải mã link sang cổng API ngầm của zsangtao.com
        api_url = "https://backend.zsangtao.com/api/v1/douyin/download"
        payload = {"url": douyin_url}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        res_json = response.json()
        
        # Bóc tách link video không logo từ kết quả web trả về
        if res_json.get("status") == "success" or "data" in res_json:
            data = res_json.get("data", {})
            # Thử lấy link video chất lượng cao nhất không logo
            video_url = data.get("video_nowatermark") or data.get("video")
            title = data.get("title", "Video Douyin")
            return video_url, title
    except Exception as e:
        print(f"Lỗi kết nối zsangtao: {e}")
    return None, None

# ── 5. XỬ LÝ TIN NHẮN ──────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if user_text == '🎬 Hướng dẫn lấy link':
        await update.message.reply_text("Vào app Douyin ➔ Bấm Chia sẻ ➔ Chọn Sao chép liên kết ➔ Dán thẳng vào đây.")
        return
    elif user_text == 'ℹ️ Trạng thái Bot':
        await update.message.reply_text("🟢 Bot kết nối ZSangTao ổn định 24/7!")
        return

    clean_url = extract_video_url(user_text)
    if not clean_url or "douyin.com" not in clean_url:
        await update.message.reply_text("⚠️ Không tìm thấy link Douyin hợp lệ. Vui lòng thử lại.")
        return

    status_msg = await update.message.reply_text("🔄 Đang gửi link sang zsangtao.com để xử lý, đợi tí nhé...")

    # Gọi hàm mượn web zsangtao tải hộ
    video_url, video_title = get_video_from_zsangtao(clean_url)

    if not video_url:
        await status_msg.edit_text("❌ Hệ thống zsangtao không phân tích được link này hoặc đang bảo trì rồi bạn ơi.")
        return

    try:
        await status_msg.edit_text("🚀 Đang tải video về Telegram của bạn...")
        await update.message.reply_video(
            video=video_url,
            caption=f"🎬 **Tiêu đề:** {video_title}\n\n📥 *Tận dụng thành công từ ZSangTao!*",
            parse_mode="Markdown"
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Lỗi gửi video từ Telegram: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot ZSangTao đang chạy...")
    app.run_polling()

if __name__ == '__main__':
    main()