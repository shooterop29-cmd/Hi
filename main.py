import os
import re
import time
import asyncio
import logging
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.error import TelegramError
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN", "7783693610:AAGi_vnGXIotfJf3bOU7VUGN7bBLRHGeCtQ")
ADMIN_ID = int(os.getenv("ADMIN_ID", 5436530930))
MAX_FILE_SIZE = 49 * 1024 * 1024  # 49 MB limit for non-premium bots

COOKIES_DIR = "cookies"
COOKIE_MAP = {
    "youtube": os.path.join(COOKIES_DIR, "youtube.txt"),
    "instagram": os.path.join(COOKIES_DIR, "instagram.txt"),
    "twitter": os.path.join(COOKIES_DIR, "twitter.txt"),
    "pinterest": os.path.join(COOKIES_DIR, "pinterest.txt"),
    "facebook": os.path.join(COOKIES_DIR, "facebook.txt"),
}

users = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

LANGUAGES = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिंदी",
    "ur": "🇵🇰 اردو",
    "ar": "🇸🇦 العربية",
    "es": "🇪🇸 Español",
    "ru": "🇷🇺 Русский",
}

TEXTS = {
    "en": {
        "welcome": "👋 Welcome to MultiSaver Pro Bot!\n\nPlease select your language:",
        "lang_set": "✅ Language set to English. Send any supported link (YouTube, Instagram, Facebook, X, Pinterest) to download.",
        "invalid": "⚠️ Please provide a valid URL link.",
        "init": "⚡ Initializing download...",
        "uploading": "📤 Uploading media...",
        "failed": "❌ Download failed: {}",
        "file_too_large": "⚠️ File exceeds the 49MB Telegram limit.",
    },
    "hi": {
        "welcome": "👋 MultiSaver Pro Bot में आपका स्वागत है!\n\nकृपया अपनी भाषा चुनें:",
        "lang_set": "✅ भाषा हिंदी सेट हो गई है। डाउनलोड करने के लिए कोई भी लिंक (YouTube, Instagram, Facebook, X, Pinterest आदि) भेजें।",
        "invalid": "⚠️ कृपया एक वैध URL लिंक भेजें।",
        "init": "⚡ डाउनलोड शुरू हो रहा है...",
        "uploading": "📤 मीडिया अपलोड हो रहा है...",
        "failed": "❌ डाउनलोड विफल: {}",
        "file_too_large": "⚠️ फ़ाइल 49MB से अधिक है, जो टेलीग्राम की सीमा से बाहर है।",
    },
    "ur": {
        "welcome": "👋 MultiSaver Pro Bot میں خوش آمدید!\n\nبراہ کرم اپنی زبان منتخب کریں:",
        "lang_set": "✅ زبان اردو منتخب ہو گئی ہے۔ ڈاؤنلوڈ کرنے کے لیے کوئی بھی لنک بھیجیں۔",
        "invalid": "⚠️ برائے مہربانی درست لنک فراہم کریں۔",
        "init": "⚡ ڈاؤنلوڈ شروع ہو رہا ہے۔۔۔",
        "uploading": "📤 میڈیا اپلوڈ ہو رہا ہے۔۔۔",
        "failed": "❌ ڈاؤنلوڈ ناکام: {}",
        "file_too_large": "⚠️ فائل 49MB کی حد سے بڑی ہے۔",
    },
    "ar": {
        "welcome": "👋 مرحبًا بك في MultiSaver Pro Bot!\n\nيرجى اختيار لغتك:",
        "lang_set": "✅ تم ضبط اللغة على العربية. أرسل أي رابط للتنزيل.",
        "invalid": "⚠️ يرجى إرسال رابط صالح.",
        "init": "⚡ جاري بدء التنزيل...",
        "uploading": "📤 جاري رفع الوسائط...",
        "failed": "❌ فشل التنزيل: {}",
        "file_too_large": "⚠️ حجم الملف يتجاوز 49 ميجابايت.",
    },
    "es": {
        "welcome": "👋 ¡Bienvenido a MultiSaver Pro Bot!\n\nPor favor seleccione su idioma:",
        "lang_set": "✅ Idioma configurado en Español. Envía cualquier enlace para descargar.",
        "invalid": "⚠️ Por favor, introduce un enlace válido.",
        "init": "⚡ Iniciando descarga...",
        "uploading": "📤 Subiendo archivo multimedia...",
        "failed": "❌ Descarga fallida: {}",
        "file_too_large": "⚠️ El archivo supera el límite de 49MB.",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в MultiSaver Pro Bot!\n\nПожалуйста, выберите язык:",
        "lang_set": "✅ Язык установлен на Русский. Отправьте ссылку для скачивания.",
        "invalid": "⚠️ Пожалуйста, укажите рабочую ссылку.",
        "init": "⚡ Запуск загрузки...",
        "uploading": "📤 Отправка медиа...",
        "failed": "❌ Ошибка загрузки: {}",
        "file_too_large": "⚠️ Размер файла превышает лимит 49 МБ.",
    },
}

def clean_ansi(text: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)

def get_text(user_id: int, key: str) -> str:
    lang = users.get(user_id, "en")
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"][key])

def get_cookie_for_url(url: str):
    domain = urlparse(url).netloc.lower()
    target_key = None
    if "youtube.com" in domain or "youtu.be" in domain:
        target_key = "youtube"
    elif "instagram.com" in domain:
        target_key = "instagram"
    elif "twitter.com" in domain or "x.com" in domain:
        target_key = "twitter"
    elif "pinterest.com" in domain or "pin.it" in domain:
        target_key = "pinterest"
    elif "facebook.com" in domain or "fb.watch" in domain:
        target_key = "facebook"

    if target_key and target_key in COOKIE_MAP:
        cookie_path = COOKIE_MAP[target_key]
        if os.path.exists(cookie_path):
            return cookie_path
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = "en"

    keyboard = [
        [
            InlineKeyboardButton(LANGUAGES["en"], callback_data="lang_en"),
            InlineKeyboardButton(LANGUAGES["hi"], callback_data="lang_hi"),
        ],
        [
            InlineKeyboardButton(LANGUAGES["ur"], callback_data="lang_ur"),
            InlineKeyboardButton(LANGUAGES["ar"], callback_data="lang_ar"),
        ],
        [
            InlineKeyboardButton(LANGUAGES["es"], callback_data="lang_es"),
            InlineKeyboardButton(LANGUAGES["ru"], callback_data="lang_ru"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_text(user_id, "welcome"), reply_markup=reply_markup
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.replace("lang_", "")
    user_id = query.from_user.id
    users[user_id] = lang_code
    await query.edit_message_text(get_text(user_id, "lang_set"))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"📊 **Bot Statistics:**\nTotal active users: {len(users)}",
        parse_mode="Markdown",
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("Usage: `/broadcast Your message here`", parse_mode="Markdown")
        return
    sent_count = 0
    for uid in list(users.keys()):
        try:
            await context.bot.send_message(chat_id=uid, text=message_text)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")

def sync_download(url: str, ydl_opts: dict):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = "en"

    if not ("http://" in text or "https://" in text):
        await update.message.reply_text(get_text(user_id, "invalid"))
        return

    try:
        await update.message.set_reaction(reaction="⚡")
    except Exception:
        pass

    status_msg = await update.message.reply_text(get_text(user_id, "init"))

    loop = asyncio.get_running_loop()
    progress_state = {"last_time": 0.0, "last_text": ""}

    def progress_hook(d):
        if d.get("status") == "downloading":
            now = time.time()
            if now - progress_state["last_time"] >= 4.0:
                percent = clean_ansi(d.get("_percent_str", "0%")).strip()
                speed = clean_ansi(d.get("_speed_str", "N/A")).strip()
                eta = clean_ansi(d.get("_eta_str", "N/A")).strip()
                total = clean_ansi(d.get("_total_bytes_str", d.get("_total_bytes_estimate_str", ""))).strip()

                msg = f"⏳ **Downloading:** `{percent}`\n⚡ **Speed:** `{speed}`\n⏱️ **ETA:** `{eta}`"
                if total:
                    msg += f"\n📦 **Size:** `{total}`"

                if msg != progress_state["last_text"]:
                    progress_state["last_text"] = msg
                    progress_state["last_time"] = now

                    async def safe_edit():
                        try:
                            await status_msg.edit_text(msg, parse_mode="Markdown")
                        except TelegramError:
                            pass

                    asyncio.run_coroutine_threadsafe(safe_edit(), loop)

    output_template = f"download_{user_id}_{int(time.time())}_%(id)s.%(ext)s"
    cookie_file = get_cookie_for_url(text)

    ydl_opts = {
        "format": "bestvideo[filesize<49M]+bestaudio/best[filesize<49M]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    file_path = None
    try:
        file_path, info = await asyncio.to_thread(sync_download, text, ydl_opts)

        if not os.path.exists(file_path):
            base_without_ext = os.path.splitext(file_path)[0]
            matched = [f for f in os.listdir(".") if f.startswith(os.path.basename(base_without_ext))]
            if matched:
                file_path = matched[0]

        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            await status_msg.edit_text(get_text(user_id, "file_too_large"))
            return

        await status_msg.edit_text(get_text(user_id, "uploading"))

        ext = file_path.split(".")[-1].lower()
        with open(file_path, "rb") as media_file:
            if ext in ["jpg", "jpeg", "png", "webp"]:
                await update.message.reply_photo(photo=media_file)
            elif ext in ["mp4", "mkv", "webm", "mov"]:
                await update.message.reply_video(video=media_file, supports_streaming=True)
            else:
                await update.message.reply_document(document=media_file)

        await status_msg.delete()

    except Exception as e:
        error_msg = clean_ansi(str(e))
        try:
            await status_msg.edit_text(get_text(user_id, "failed").format(error_msg))
        except TelegramError:
            pass

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

if __name__ == "__main__":
    if not os.path.exists(COOKIES_DIR):
        os.makedirs(COOKIES_DIR)

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)
