import os
import re
import time
import glob
import asyncio
import logging
import subprocess
from urllib.parse import urlparse, urlunparse

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
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
DOWNLOADS_DIR = "downloads"

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

def extract_clean_url(text: str) -> str | None:
    """मैसेज से साफ़ URL निकालता है और फालतू ट्रैकिंग पैरामीटर्स हटाता है"""
    url_pattern = r"(https?://[^\s]+)"
    match = re.search(url_pattern, text)
    if not match:
        return None

    raw_url = match.group(1).strip()
    raw_url = re.sub(r"[),.\'\"]+$", "", raw_url)

    parsed = urlparse(raw_url)
    if "pin.it" in parsed.netloc:
        return raw_url.split("?")[0]

    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

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

def download_with_gallery_dl(url: str, dest_dir: str, cookie_file: str = None) -> list[str]:
    """gallery-dl के ज़रिए फ़ोटोज़/कैरोसेल डाउनलोड करता है"""
    cmd = ["gallery-dl", "--directory", dest_dir]
    if cookie_file and os.path.exists(cookie_file):
        cmd.extend(["--cookies", cookie_file])
    cmd.append(url)

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            downloaded = []
            for root, _, files in os.walk(dest_dir):
                for f in files:
                    downloaded.append(os.path.join(root, f))
            return downloaded
    except Exception:
        pass
    return []

def download_with_ytdlp(url: str, dest_dir: str, cookie_file: str = None, progress_hook=None) -> list[str]:
    """yt-dlp के ज़रिए वीडियो/ऑडियो डाउनलोड करता है"""
    output_template = os.path.join(dest_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[filesize<49M]+bestaudio/best[filesize<49M]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]
    if cookie_file and os.path.exists(cookie_file):
        ydl_opts["cookiefile"] = cookie_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    downloaded = []
    for root, _, files in os.walk(dest_dir):
        for f in files:
            downloaded.append(os.path.join(root, f))
    return downloaded

def route_and_download(url: str, dest_dir: str, progress_hook=None) -> list[str]:
    """प्लेटफॉर्म के हिसाब से gallery-dl या yt-dlp का चुनाव करता है"""
    domain = urlparse(url).netloc.lower()
    cookie_file = get_cookie_for_url(url)

    # 1. Instagram / Pinterest / X (Twitter) - पहले फ़ोटोज़/इमेज के लिए gallery-dl
    if any(p in domain for p in ["instagram.com", "pinterest.com", "pin.it", "twitter.com", "x.com"]):
        files = download_with_gallery_dl(url, dest_dir, cookie_file)
        if files:
            return files
        # अगर gallery-dl से कोई फ़ाइल नहीं मिली, तो yt-dlp फ़ॉलबैक (वीडियो/रील्स)
        return download_with_ytdlp(url, dest_dir, cookie_file, progress_hook)

    # 2. YouTube या अन्य प्लेटफ़ॉर्म्स - yt-dlp
    return download_with_ytdlp(url, dest_dir, cookie_file, progress_hook)

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = "en"

    clean_url = extract_clean_url(raw_text)
    if not clean_url:
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

    task_dir = os.path.join(DOWNLOADS_DIR, f"{user_id}_{int(time.time())}")
    os.makedirs(task_dir, exist_ok=True)

    downloaded_files = []
    try:
        downloaded_files = await asyncio.to_thread(
            route_and_download, clean_url, task_dir, progress_hook
        )

        if not downloaded_files:
            raise Exception("No media found or download failed.")

        # साइज चेक
        valid_files = [f for f in downloaded_files if os.path.getsize(f) <= MAX_FILE_SIZE]
        if not valid_files:
            await status_msg.edit_text(get_text(user_id, "file_too_large"))
            return

        await status_msg.edit_text(get_text(user_id, "uploading"))

        # एक से ज़्यादा मीडिया (Carousels/Albums) या सिंगल मीडिया अपलोड
        media_group = []
        for file_path in valid_files:
            ext = file_path.split(".")[-1].lower()
            if ext in ["jpg", "jpeg", "png", "webp"]:
                with open(file_path, "rb") as f:
                    media_group.append(InputMediaPhoto(media=f.read()))
            elif ext in ["mp4", "mkv", "webm", "mov"]:
                with open(file_path, "rb") as f:
                    media_group.append(InputMediaVideo(media=f.read()))

        if len(media_group) > 1:
            # 10 के बैच में टेलीग्राम एल्बम भेजें
            for i in range(0, len(media_group), 10):
                await update.message.reply_media_group(media=media_group[i:i + 10])
        elif len(media_group) == 1:
            file_path = valid_files[0]
            ext = file_path.split(".")[-1].lower()
            with open(file_path, "rb") as media_file:
                if ext in ["jpg", "jpeg", "png", "webp"]:
                    await update.message.reply_photo(photo=media_file)
                elif ext in ["mp4", "mkv", "webm", "mov"]:
                    await update.message.reply_video(video=media_file, supports_streaming=True)
                else:
                    await update.message.reply_document(document=media_file)
        else:
            for file_path in valid_files:
                with open(file_path, "rb") as media_file:
                    await update.message.reply_document(document=media_file)

        await status_msg.delete()

    except Exception as e:
        error_msg = clean_ansi(str(e))
        try:
            await status_msg.edit_text(get_text(user_id, "failed").format(error_msg))
        except TelegramError:
            pass

    finally:
        # क्लीनअप
        if os.path.exists(task_dir):
            for f in glob.glob(os.path.join(task_dir, "*")):
                try:
                    os.remove(f)
                except OSError:
                    pass
            try:
                os.rmdir(task_dir)
            except OSError:
                pass

if __name__ == "__main__":
    os.makedirs(COOKIES_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

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
