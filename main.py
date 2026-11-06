import asyncio
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import yt_dlp


# Set BOT_TOKEN in Railway -> Variables. Never put the real token in source code.
TOKEN = os.getenv("7783693610:AAGi_vnGXIotfJf3bOU7VUGN7bBLRHGeCtQ", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "5436530930"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "49"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# In-memory language preferences reset when the process restarts.
# Use a database if you need persistent users/statistics.
users: dict[int, str] = {}

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
        "lang_set": "✅ Language set to English. Send a supported media link.",
        "invalid": "⚠️ Please send a valid http:// or https:// link.",
        "init": "⚡ Checking link and starting download...",
        "uploading": "📤 Uploading media to Telegram...",
        "failed": "❌ Download failed:\n{}",
        "too_large": "⚠️ This file is {:.1f} MB. The configured upload limit is {} MB.",
    },
    "hi": {
        "welcome": "👋 MultiSaver Pro Bot में आपका स्वागत है!\n\nकृपया अपनी भाषा चुनें:",
        "lang_set": "✅ भाषा हिंदी सेट हो गई है। डाउनलोड करने के लिए लिंक भेजें।",
        "invalid": "⚠️ कृपया http:// या https:// वाला सही लिंक भेजें।",
        "init": "⚡ लिंक जाँचा जा रहा है और डाउनलोड शुरू हो रहा है...",
        "uploading": "📤 मीडिया Telegram पर अपलोड हो रहा है...",
        "failed": "❌ डाउनलोड विफल:\n{}",
        "too_large": "⚠️ फ़ाइल {:.1f} MB की है। अपलोड सीमा {} MB है।",
    },
    "ur": {
        "welcome": "👋 MultiSaver Pro Bot میں خوش آمدید!\n\nبراہ کرم اپنی زبان منتخب کریں:",
        "lang_set": "✅ زبان اردو منتخب ہو گئی ہے۔ ڈاؤنلوڈ کے لیے لنک بھیجیں۔",
        "invalid": "⚠️ براہ کرم درست http:// یا https:// لنک بھیجیں۔",
        "init": "⚡ لنک چیک ہو رہا ہے اور ڈاؤنلوڈ شروع ہو رہا ہے...",
        "uploading": "📤 میڈیا Telegram پر اپلوڈ ہو رہا ہے...",
        "failed": "❌ ڈاؤنلوڈ ناکام:\n{}",
        "too_large": "⚠️ فائل {:.1f} MB ہے۔ اپلوڈ حد {} MB ہے۔",
    },
    "ar": {
        "welcome": "👋 مرحبًا بك في MultiSaver Pro Bot!\n\nيرجى اختيار لغتك:",
        "lang_set": "✅ تم ضبط اللغة على العربية. أرسل رابطًا مدعومًا.",
        "invalid": "⚠️ يرجى إرسال رابط http:// أو https:// صالح.",
        "init": "⚡ جارٍ فحص الرابط وبدء التنزيل...",
        "uploading": "📤 جارٍ رفع الوسائط إلى Telegram...",
        "failed": "❌ فشل التنزيل:\n{}",
        "too_large": "⚠️ حجم الملف {:.1f} MB، وحد الرفع {} MB.",
    },
    "es": {
        "welcome": "👋 ¡Bienvenido a MultiSaver Pro Bot!\n\nSelecciona tu idioma:",
        "lang_set": "✅ Idioma configurado en Español. Envía un enlace compatible.",
        "invalid": "⚠️ Envía un enlace http:// o https:// válido.",
        "init": "⚡ Comprobando el enlace e iniciando la descarga...",
        "uploading": "📤 Subiendo el archivo a Telegram...",
        "failed": "❌ Descarga fallida:\n{}",
        "too_large": "⚠️ El archivo pesa {:.1f} MB. El límite es {} MB.",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в MultiSaver Pro Bot!\n\nВыберите язык:",
        "lang_set": "✅ Язык установлен на Русский. Отправьте поддерживаемую ссылку.",
        "invalid": "⚠️ Отправьте корректную ссылку http:// или https://.",
        "init": "⚡ Проверяю ссылку и начинаю загрузку...",
        "uploading": "📤 Загружаю файл в Telegram...",
        "failed": "❌ Ошибка загрузки:\n{}",
        "too_large": "⚠️ Размер файла {:.1f} MB. Лимит — {} MB.",
    },
}


def get_text(user_id: int, key: str) -> str:
    language = users.get(user_id, "en")
    return TEXTS.get(language, TEXTS["en"]).get(key, TEXTS["en"][key])


def is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def build_ydl_options(output_dir: str, url: str, progress_hook):
    # Instagram post URLs can contain carousels. Other URLs are kept single-item.
    host = (urlparse(url).hostname or "").lower()
    is_instagram_post = (
        host.endswith("instagram.com")
        and re.search(r"/(p|reel|reels|tv)/", urlparse(url).path) is not None
    )

    options = {
        # With FFmpeg installed, yt-dlp can merge separate video/audio streams.
        # The final /best fallback also supports sites offering one combined stream.
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "outtmpl": str(Path(output_dir) / "%(title).80s-%(id)s.%(ext)s"),
        "noplaylist": not is_instagram_post,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "progress_hooks": [progress_hook],
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # Optional: paste Netscape-format Instagram cookies into Railway variable
    # INSTAGRAM_COOKIES if the post requires a logged-in account.
    cookie_text = os.getenv("INSTAGRAM_COOKIES", "").strip()
    if cookie_text and host.endswith("instagram.com"):
        cookie_path = Path(tempfile.gettempdir()) / "instagram_cookies.txt"
        cookie_path.write_text(cookie_text, encoding="utf-8")
        options["cookiefile"] = str(cookie_path)

    return options


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.setdefault(user_id, "en")

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
    await update.message.reply_text(
        get_text(user_id, "welcome"),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.removeprefix("lang_")
    if lang_code not in TEXTS:
        return
    users[query.from_user.id] = lang_code
    await query.edit_message_text(get_text(query.from_user.id, "lang_set"))


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"📊 Bot statistics\nUsers seen by this running process: {len(users)}"
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    message_text = " ".join(context.args).strip()
    if not message_text:
        await update.message.reply_text("Usage: /broadcast Your message here")
        return

    sent_count = 0
    for user_id in list(users):
        try:
            await context.bot.send_message(chat_id=user_id, text=message_text)
            sent_count += 1
            await asyncio.sleep(0.05)
        except TelegramError:
            logger.exception("Broadcast failed for user %s", user_id)

    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")


def download_files(url: str, output_dir: str, loop, status_msg):
    progress_state = {"last_update": 0.0, "last_text": ""}

    def progress_hook(data):
        if data.get("status") != "downloading":
            return

        now = time.monotonic()
        if now - progress_state["last_update"] < 2:
            return

        percent = clean_ansi(data.get("_percent_str", "")).strip() or "..."
        speed = clean_ansi(data.get("_speed_str", "")).strip() or "N/A"
        eta = clean_ansi(data.get("_eta_str", "")).strip() or "N/A"
        message = f"⏳ Downloading: {percent}\n⚡ Speed: {speed}\n⏱️ ETA: {eta}"

        if message != progress_state["last_text"]:
            progress_state["last_text"] = message
            progress_state["last_update"] = now
            future = asyncio.run_coroutine_threadsafe(
                status_msg.edit_text(message), loop
            )
            # Consume callback exceptions so a deleted status message doesn't
            # produce an unhandled-future warning in the worker thread.
            future.add_done_callback(lambda f: f.exception() if not f.cancelled() else None)

    options = build_ydl_options(output_dir, url, progress_hook)
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.extract_info(url, download=True)

    # Use the actual files on disk: prepare_filename() can point to the
    # pre-merge extension even after FFmpeg has converted/merged the output.
    return sorted(
        path for path in Path(output_dir).iterdir()
        if path.is_file() and not path.name.endswith((".part", ".ytdl"))
    )


def clean_ansi(value: str) -> str:
    return re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", str(value))


async def send_downloaded_file(update: Update, file_path: Path):
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        await update.message.reply_text(
            get_text(update.effective_user.id, "too_large").format(
                size_mb, MAX_UPLOAD_MB
            )
        )
        return

    suffix = file_path.suffix.lower()
    with file_path.open("rb") as media:
        if suffix in {".jpg", ".jpeg", ".png"}:
            await update.message.reply_photo(photo=media)
        elif suffix in {".mp4", ".mov"}:
            await update.message.reply_video(video=media, supports_streaming=True)
        elif suffix == ".webp":
            await update.message.reply_document(document=media)
        else:
            await update.message.reply_document(document=media)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    user_id = update.effective_user.id
    users.setdefault(user_id, "en")

    if not is_valid_http_url(url):
        await update.message.reply_text(get_text(user_id, "invalid"))
        return

    try:
        await update.message.set_reaction(reaction="⚡")
    except TelegramError:
        pass

    status_msg = await update.message.reply_text(get_text(user_id, "init"))
    loop = asyncio.get_running_loop()

    try:
        with tempfile.TemporaryDirectory(prefix="multisaver_") as temp_dir:
            files = await asyncio.to_thread(
                download_files, url, temp_dir, loop, status_msg
            )

            if not files:
                raise RuntimeError(
                    "The site did not provide a downloadable media file."
                )

            await status_msg.edit_text(get_text(user_id, "uploading"))

            sent = 0
            for file_path in files:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > MAX_UPLOAD_MB:
                    await update.message.reply_text(
                        get_text(user_id, "too_large").format(
                            size_mb, MAX_UPLOAD_MB
                        )
                    )
                    continue

                await send_downloaded_file(update, file_path)
                sent += 1

            if sent == 0:
                await status_msg.edit_text(
                    "⚠️ No files could be uploaded. They may exceed Telegram's upload limit."
                )
            else:
                await status_msg.delete()

    except Exception as exc:
        error_text = clean_ansi(str(exc))
        logger.exception("Download failed for user %s", user_id)
        # Telegram messages have a 4096-character limit.
        await status_msg.edit_text(
            get_text(user_id, "failed").format(error_text[:3500])
        )


async def post_init(application):
    # Helpful startup log; does not expose the token.
    me = await application.bot.get_me()
    logger.info("Bot started as @%s", me.username)


def main():
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError(
            "BOT_TOKEN is missing. Add the valid token in Railway -> Variables."
        )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang_"))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
