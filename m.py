import os
import re
import time
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import yt_dlp

TOKEN = "7783693610:AAGi_vnGXIotfJf3bOU7VUGN7bBLRHGeCtQ"
ADMIN_ID = 5436530930

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
        "lang_set": "✅ Language set to English. Send any supported link (YouTube, Instagram, Pinterest, etc.) to download.",
        "invalid": "⚠️ Please provide a valid URL link.",
        "init": "⚡ Initializing download...",
        "uploading": "📤 Uploading media...",
        "failed": "❌ Download failed: {}",
    },
    "hi": {
        "welcome": "👋 MultiSaver Pro Bot में आपका स्वागत है!\n\nकृपया अपनी भाषा चुनें:",
        "lang_set": "✅ भाषा हिंदी सेट हो गई है। डाउनलोड करने के लिए कोई भी लिंक (YouTube, Instagram, Pinterest आदि) भेजें।",
        "invalid": "⚠️ कृपया एक वैध URL लिंक भेजें।",
        "init": "⚡ डाउनलोड शुरू हो रहा है...",
        "uploading": "📤 मीडिया अपलोड हो रहा है...",
        "failed": "❌ डाउनलोड विफल: {}",
    },
    "ur": {
        "welcome": "👋 MultiSaver Pro Bot میں خوش آمدید!\n\nبراہ کرم اپنی زبان منتخب کریں:",
        "lang_set": "✅ زبان اردو منتخب ہو گئی ہے۔ ڈاؤنلوڈ کرنے کے لیے کوئی بھی لنک بھیجیں۔",
        "invalid": "⚠️ برائے مہربانی درست لنک فراہم کریں۔",
        "init": "⚡ ڈاؤنلوڈ شروع ہو رہا ہے۔۔۔",
        "uploading": "📤 میڈیا اپلوڈ ہو रहा ہے۔۔۔",
        "failed": "❌ ڈاؤنلوڈ ناکام: {}",
    },
    "ar": {
        "welcome": "👋 مرحبًا بك في MultiSaver Pro Bot!\n\nيرجى اختيار لغتك:",
        "lang_set": "✅ تم ضبط اللغة على العربية. أرسل أي رابط للتنزيل.",
        "invalid": "⚠️ يرجى إرسال رابط صالح.",
        "init": "⚡ جاري بدء التنزيل...",
        "uploading": "📤 جاري رفع الوسائط...",
        "failed": "❌ فشل التنزيل: {}",
    },
    "es": {
        "welcome": "👋 ¡Bienvenido a MultiSaver Pro Bot!\n\nPor favor seleccione su idioma:",
        "lang_set": "✅ Idioma configurado en Español. Envía cualquier enlace para descargar.",
        "invalid": "⚠️ Por favor, introduce un enlace válido.",
        "init": "⚡ Iniciando descarga...",
        "uploading": "📤 Subiendo archivo multimedia...",
        "failed": "❌ Descarga fallida: {}",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в MultiSaver Pro Bot!\n\nПожалуйста, выберите язык:",
        "lang_set": "✅ Язык установлен на Русский. Отправьте ссылку для скачивания.",
        "invalid": "⚠️ Пожалуйста, укажите рабочую ссылку.",
        "init": "⚡ Запуск загрузки...",
        "uploading": "📤 Отправка медиа...",
        "failed": "❌ Ошибка загрузки: {}",
    },
}

def clean_ansi(text):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)

def get_text(user_id, key):
    lang = users.get(user_id, "en")
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"][key])

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
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")

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
            if now - progress_state["last_time"] >= 2.0:
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
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(msg, parse_mode="Markdown"), loop
                    )

    output_template = f"download_{user_id}_%(id)s.%(ext)s"
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
    }

    try:
        def fetch_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
                return filename, info

        file_path, info = await loop.run_in_executor(None, fetch_media)

        await status_msg.edit_text(get_text(user_id, "uploading"))

        ext = file_path.split(".")[-1].lower()
        with open(file_path, "rb") as media_file:
            if ext in ["jpg", "jpeg", "png", "webp"]:
                await update.message.reply_photo(photo=media_file)
            elif ext in ["mp4", "mkv", "webm", "mov"]:
                await update.message.reply_video(video=media_file)
            else:
                await update.message.reply_document(document=media_file)

        await status_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        error_msg = clean_ansi(str(e))
        await status_msg.edit_text(get_text(user_id, "failed").format(error_msg))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")
    app.run_polling()
