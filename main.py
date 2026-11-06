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

# Raw Cookies Data for Automatic Netscape File Generation
COOKIES_RAW = {
    "youtube.txt": [
        {"domain": ".youtube.com", "name": "VISITOR_PRIVACY_METADATA", "value": "CgJJThIEGgAgZg%3D%3D", "expirationDate": 1809536217},
        {"domain": ".youtube.com", "name": "__Secure-3PSID", "value": "g.a000Egk46zztKjTe49zTLwM7182DKZeZT-GmgQDeitJRSmhlF3KBRLMW6r1psbtR0RFhUTjxEwACgYKATQSARMSFQHGX2Miz09XsRcpiXfhf88enttNJhoVAUF8yKrSFtRuM054L2NG4gjZuM7J0076", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "GPS", "value": "1", "expirationDate": 1793985000},
        {"domain": ".youtube.com", "name": "SIDCC", "value": "APD_SKHQiveoj7pbY1B-e3fLv0Dt43v5m1gJQP5Nc8W4omDpRmdYb7qLDhd0QAqUPMDCYHS_", "expirationDate": 1825520220},
        {"domain": ".youtube.com", "name": "YSC", "value": "9Dqu379GhSk", "expirationDate": 0},
        {"domain": ".youtube.com", "name": "SID", "value": "g.a000Egk46zztKjTe49zTLwM7182DKZeZT-GmgQDeitJRSmhlF3KBf-7ca59N8sEC7KgYxm-L9gACgYKAX0SARMSFQHGX2MihL_pftsEDegR2r9hGEJlExoVAUF8yKoj64dwLc4Vir_NJwXkF-gd0076", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PSIDTS", "value": "sidts-CjQBnJZzanSlWaSeWiRlvUygojlpb5hR7zxQhqdrpyt2CerSa2RcRd9rM2pr3dXSlEWaWMEsEAA", "expirationDate": 1825519256},
        {"domain": ".youtube.com", "name": "SAPISID", "value": "5mxiUK3s1akuiDBh/AOAh3IoJqQTknptBb", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PSIDCC", "value": "APD_SKFEIGVr3xwMESCOTvBPUq46bsQPRgt3eM0PCnP_Eu9TL3oLAPFYsDwPQ-XBBPaVtXbG", "expirationDate": 1825520220},
        {"domain": ".youtube.com", "name": "SSID", "value": "ATHa9Q0uOeK99pyUj", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PAPISID", "value": "5mxiUK3s1akuiDBh/AOAh3IoJqQTknptBb", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PSID", "value": "g.a000Egk46zztKjTe49zTLwM7182DKZeZT-GmgQDeitJRSmhlF3KBzglZnqbkQLaX7qDE-zgjBQACgYKAecSARMSFQHGX2MiUjEEJYFr57mGBFTCNWQePBoVAUF8yKpdzfu5n0_k6XOc1F_tgpOp0076", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-3PAPISID", "value": "5mxiUK3s1akuiDBh/AOAh3IoJqQTknptBb", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-3PSIDCC", "value": "APD_SKEEAwjuEQjmBYHp6LJp6nX3PZp7jXGjUC2-4PRibUaBz4ZzB0vpnCaKHQdD7fckLSOR", "expirationDate": 1825520220},
        {"domain": ".youtube.com", "name": "__Secure-3PSIDTS", "value": "sidts-CjQBnJZzanSlWaSeWiRlvUygojlpb5hR7zxQhqdrpyt2CerSa2RcRd9rM2pr3dXSlEWaWMEsEAA", "expirationDate": 1825519256},
        {"domain": ".youtube.com", "name": "__Secure-YNID", "value": "CtoBCAUSjAEBDB6PDMggTN-P0Yv9rAhHiq6eE54X5bBy-6LBQxXuLGiF2dXpV-BdlQwk5AoH4Rq8zAu9sB0vFk1Br-eKdwImEhWzbB1XgAm-ZHNfQyTHmEzjN5eZdlCoo_va-e7weI_uAcBrFFO4gRjCjK9kuSTpL6mBstS-l3FHz6DYDZf_0yWJVQ1EAqcpEO49aygFMkUBHFj1au9F1DVsCNdctutOes_5hYcUPtHkifxlt92vd7Yk6Ztl4kJpSRaXUPvjnl48Zu0qrVOGUpm3IsnRGSlalhOFAws", "expirationDate": 1809535200},
        {"domain": ".youtube.com", "name": "APISID", "value": "69FXIJOKsSb7Ay74/Avzrez4hKEVOXM6Ps", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "HSID", "value": "AxyD5vJ-_0-hmSJZK", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "LOGIN_INFO", "value": "AFmmF2swRAIgcSf3PuEA-P2yUiFL2W-ryZc9LkxzGNZtbYa0v9nipFwCIFpLKA1CYkyvYgIaNGCjethamNZ1-6nmfD89NdkVxYTb:QUQ3MjNmeHZUTWtPSGpkZGotMUxINkxmVU52RGd3MU5LRFZzM2w4TV9uMWlpSy1XSjc4c0RhSEdjNEo2WU82Wl9Lc2NzRWZUMks0S2lsTUVLMm5YRzlFZmRIQVk0TFNueVFuaXVlVHJXbUM1VkpteVhhUU5rNkdlaEdVSUJRSFZEX0I0X2g0NEhFQnpKTkM1eVNYUWpzVDNMT3dlUWc0T2p3", "expirationDate": 1828543257},
        {"domain": ".youtube.com", "name": "PREF", "value": "f6=40000000&tz=Asia.Kolkata&f4=4000000", "expirationDate": 1828543550},
        {"domain": ".youtube.com", "name": "VISITOR_INFO1_LIVE", "value": "cpgrYatvHuo", "expirationDate": 1809536217}
    ],
    "instagram.txt": [
        {"domain": ".instagram.com", "name": "ps_n", "value": "1", "expirationDate": 1828543792},
        {"domain": ".instagram.com", "name": "datr", "value": "MQXuak-DzxEIpwnZg6a2L6Qn", "expirationDate": 1828543792},
        {"domain": ".instagram.com", "name": "ds_user_id", "value": "68193481076", "expirationDate": 1801759897},
        {"domain": ".instagram.com", "name": "csrftoken", "value": "IRoCbVXA3qMj8Kh3T9l2tg", "expirationDate": 1828543897},
        {"domain": ".instagram.com", "name": "ig_did", "value": "83A00985-C5A6-4DA1-97F4-E6F1B9A62206", "expirationDate": 1825519792},
        {"domain": ".instagram.com", "name": "ps_l", "value": "1", "expirationDate": 1828543792},
        {"domain": ".instagram.com", "name": "wd", "value": "423x780", "expirationDate": 1794588700},
        {"domain": ".instagram.com", "name": "mid", "value": "au4FMQABAAHOxL9hT1fX8odVj4Km", "expirationDate": 1828543794},
        {"domain": ".instagram.com", "name": "sessionid", "value": "68193481076%3AbLR0x7fgumtWDg%3A23%3AAYmNJGnXLDOoHgUNvBKDQhBQ5f_vKJ1e9X04CIGblg", "expirationDate": 1825519853},
        {"domain": ".instagram.com", "name": "dpr", "value": "3", "expirationDate": 1794588653},
        {"domain": ".instagram.com", "name": "rur", "value": "EAG%2C17841468192284185%2C1795193502%3A01ff90d4ec31ef9c1a71042c9f4ae76dfb864f519d64898a5755aa09e68c516faa462090", "expirationDate": 0}
    ],
    "pinterest.txt": [
        {"domain": ".pinterest.com", "name": "_b", "value": "\"AZqQCMdXuftE3ZnGecfc9rH4lsE1fYSIroKN6enhckdqoZfcwmLBP3BecjZq8YHhysY=\"", "expirationDate": 1828543948},
        {"domain": ".pinterest.com", "name": "_pinterest_sess", "value": "TWc9PSZhSHdTckE4ZXFwakJuK1FvdnozNVBKZFd1TzVrYThSQTFmM2Z2SFFKeVFZS3lkMWp4TmVHMjNiTWxzdEN0M25JM2hXSlBTN3l0VlV3UHVBRUlGcTdLZm8wNkVVMi83RVgveUtYa3oyekYxVHdESmJDTUZYclI1d2lCVG9IL25SN0ZpTHZmMk9OUk1sL2NlNWtXTC91anRRNEVwckJzbmplS2l5VmZKYVp1c0JBbndXeXpMR3dPcFRQdFNuZVgzeDNudXFhR2xYSWsvaTg0dzFPWGFiM3E2RzRFV0hMZmJUUllQUnpibytGSTVrTzIwZXhFTEo1OUJtYVFTWjk1TFI4REcrRHlGNlJkZjQ0MHVjOW9OUm51WWRzMUpIbmZXcjY3V3JHMUdiVk5RV2JFKzlWbDU4bCtOT2Q2S0I5WEJndXNnOXN5Myt1bHpTT3lYRitqUGFra3I3NzZuTnNzRlJvWUtacnphUmQ5Q04zMEwyZFRxNFZJSDhRQzFWTHJQUzNYUVVhL2c1Y0pyanQ0ajd1OGxNRzZIOHdDMjJ0ZmNQTytLSlFmYTFIazIvSjYycDVEMGl3cXV6dEQ2cnVaL3RUQS9mNVcwd3NwQ1Y0ZFp5Ymx3RGdSeTkvbXlYVGNLYno1S0M1UFJVUjBVUXJMRTc0VWl1OVo3V05Ic0tYK2g3STlPaU9MMTRHZDU4eU9BQ2VQb1NrWEF4WUFzOUVKaXhsQVgrUTlvSE1LR0dyNmZQZ3hETmpCeG5KbkNWNWFyeUVBcitqaGdEREVOanYxUzdHYjVrbFR2aDhtTU1EOFpMcGpqc2x6YXVyY2Z0OGwyRStFc2wzU21BUHZ2Z3JmU2txZDRsOGJjNUJESENmbXhwVy9DcUczVEc3bzcxdFV5azFKSzc2VGpNLzJEc2xVc2Evb1lIY0JBblZ2cjAxUTEwY1BIUFBiUHJIdmNEakdqZFgrSHlQM3BzZXFabGR0ZXhURi9BMDBDR29rNFpIK05VSzY1Zm84UkZobWkvbVlnSFlQa3llaWdWTVQrQUhLYitSU2FLSWlEODVXT1VldG5rbDRpUVZIWEVvTEMrdlNsZjdaTVlDNHJFdENHTC8xaTBFVmxYbm4yTjdGam1WemhKZks1M3lkYythL0YvTnp5SzZiZUNyYmEwT1F2dGxLanVjNVhkNnkvY2NvMXNTL2l4VjZHTEdVVUlEYjh6SHpJa1ZFZk41TnFzdWhkUVVDM2ttalVhTW83WitJclVmYUlQb2psTnR5UGkwa0hxRmNpR1R2Q2VYaklkbXBCK3hlNVQxNGNPZ0ZaTFBTbGxmQ0tyM0hNSW9jOVZGQUkxMlZ4alpoQ3p0dUJtSVRESzNRSzBsZ2lmckVXUlE2QndzakZ5bGpYSDUrWXBrcC9KZStmM3RaZHlqRXZUTE50L2VHcGYydFBzM0pobC9CRzNIM3ZPcW0zRUovdm5pTzV5ZWtNSThucm53THUxZWI2Qm9ab1N4YUwvTGwrSHlzWDlzZmF3T2o0dEtiUmhQNW56cVZDNVVEeDRUeUdIWWI5SXBFSVB4L1hSTHZDdFBFVXNQQmhxVEU3Slp4Y1NTbmNnMUxkY2h2M1NFcWZZOHkzWGNUSFpnY0FHWnord3ZFNStrN2hGc3J2ekhnbjNMNXFoNW1EUEhjbmtTYTVveVdnNlJPaXJIS291cDd3N25wYUMvL2RzYWZWbTNOV1hybndoR0NrRG1KUmpOTmFCL0VaSVNxSy9wWUJ1a09jbjE3elNaWHJ3WitrT0duZ0xrcHFWd0trSFkmaHhCdDNCbXBvTURJT3ZlR1llVHRHY01VL1hrPQ==", "expirationDate": 1825088000},
        {"domain": ".pinterest.com", "name": "__Secure-s_a", "value": "RVRUUEVlVGRFZVl6OVprSE5pU1dscGp5TlJhMThHMmp2cU00VzJzWFF6YXpUS2dsZnRWZnJtb05BV1k4cTlkK2pNWG9KVi9TUnFYNW1NaDRxVk1VYmx0KzFTRC8zZldCSWhQTTZZUTBrc0RldmFsNXV6ZVhHVEhwVzNSYXJRUjRUa2RDdWxLUVh0Rk9xRzFNRHVLZCs1S0dsbHFwV1RaQ0ZUZ011WnV3ZDg4V2FheGM0RFNaTjJrZWdjR0V5VVF6SHlBWjZkd1RFeHZ6Z1BwVlhoeE5xdFRCSkNqelRKTWNzRGJZR1grUTJMMHV0WERrU3JCajBJdGhMYXp5T1M3RzUvYmF3UEg0YSt3cWhNYk9DSDlkVGx2Nnp2YmllWG1NOGZOOTNuT01EOFdYSDE0YVhJRFBhMkZkTnE1NmZKZnE2am1aMDRzeWVNWUx4bVVPVGdtSHJWNjBwQlNxSjdCaDYvTC9tZUwwbkxpOU9GTUw1KzdXWGlCRFZCRHBpejhVSEJaNHVOWnlVQk5FeDFKT2Z6Sk1JakpWVW1VeGNDVllNVGxKZGd3WEt0bXhkTHVkY2lBL2xhUWFRbEpzcFBuWEhEQ0xweE80K0ZVM0xJYjFHNmwzTzRtTnQvVnBtN3NNdHR2NjNDaVZRUTMxNkNXWGxPNXQ5STFtVjlMbWs1YW9zQXVCb1NkQ2N1S1NRTm90c0R1ZjF2RUVHdjQ5Y2lZb2N6M1VBSENscWozUkZucGZlek15SHJVajQySXNTVlJVU2Nld2JXVEpLZ0pGK1RuTHNHR3FMUnptNUZYdkZVY2loMlRPMTl1QWU5WENIS0lmRUJhTzhPWlVGeG1qMnZRRVRIcExSU0JEOUcrQTlxUGhZR1VTU3NneTUvMEdiK1BjYS81UkZ4TnBxYzRvWW9DOWFyNnNqSmE4cSthdVQrYXVvVGRabUhlanBESWFZYkI1a29KT1R5aHFhdklwSzlFaFBGTmlmRHlwaDVTdnhLMXNxMDYxL2dHTnVzUit5NmViNUt3Q0hkS0dYVkF6eTN0RHFGU3NNQk5LdTJiTFZhYXFSWHIwL2llc29qZU9LbkJsOWdWamdXWmRBQmxjZnRHdUJkZjJGKzNCWGpqa0JNY3F3dGlGZTVuMzNTTWZGRkRiOW5tR0htTXpqN2dSbHBGM3VwdG1ZcjVmSUx4TW5BQ1RMTFRZdEpHVFJ5ZjJ1ODlQZnV0VDE3Y2N1cVVLeXpPckRYZmQvTkVjUkVUV01qYUZLTkMwbWNaQTFONXhyQy8xQWhGditvVWNHajFpMXFUYUM1VHpvZXpLS1pzQnFwRGlGa3RVUGszYmloUT0mOGFQVkp5V0x0ckRJa3NreUhJaTR6S1V3eDBrPQ==", "expirationDate": 1825088000},
        {"domain": ".pinterest.com", "name": "_auth", "value": "1", "expirationDate": 1825088000},
        {"domain": "in.pinterest.com", "name": "csrftoken", "value": "8bdbaef8e1be8c5e17b137450e2ac4d0", "expirationDate": 1825519946}
    ],
    "twitter.txt": [
        {"domain": ".x.com", "name": "auth_token", "value": "5574f6bf59968d32d1c6ce18ca105bd917bc5d9b", "expirationDate": 1825520165},
        {"domain": ".x.com", "name": "ct0", "value": "a967405b67d7470b3e02b02ad8dc4038e3b6479ff905f15a8218d2b1e6c48a88fb3aafbec0315eaea0fdc96b6555fa627b100769a28458e235644573d7bd469040caa32bfdf450ecbfcbe0f680e4ec94", "expirationDate": 1828544167},
        {"domain": ".x.com", "name": "twid", "value": "u%3D1504164685587038210", "expirationDate": 1825520170},
        {"domain": ".x.com", "name": "guest_id", "value": "v1%3A179398404823622652", "expirationDate": 1828544047}
    ]
}

def auto_generate_cookies():
    """Railway environment start hote hi automatically netscape txt files generate karta hai"""
    os.makedirs(COOKIES_DIR, exist_ok=True)
    for filename, cookies in COOKIES_RAW.items():
        filepath = os.path.join(COOKIES_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c["domain"]
                include_sub = "TRUE" if domain.startswith(".") else "FALSE"
                path = "/"
                secure = "TRUE"
                expiry = str(int(c.get("expirationDate", 0)))
                f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expiry}\t{c['name']}\t{c['value']}\n")

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
    """Message se extra share text (Pinterest ka Take a look wagera) hatakar sirf URL nikalta hai"""
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
    """Images aur carousels ke liye gallery-dl use karta hai"""
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
    """Video/audio ke liye yt-dlp run karta hai (format error fixed)"""
    output_template = os.path.join(dest_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": MAX_FILE_SIZE,
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
    domain = urlparse(url).netloc.lower()
    cookie_file = get_cookie_for_url(url)

    # 1. Instagram / Pinterest / Twitter (X) -> Pehle gallery-dl se check karo
    if any(p in domain for p in ["instagram.com", "pinterest.com", "pin.it", "twitter.com", "x.com"]):
        files = download_with_gallery_dl(url, dest_dir, cookie_file)
        if files:
            return files
        # Agar image nahi hai (reels/video), tab yt-dlp fallback
        return download_with_ytdlp(url, dest_dir, cookie_file, progress_hook)

    # 2. YouTube aur baaki sites -> Seedhe yt-dlp
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

        valid_files = [f for f in downloaded_files if os.path.getsize(f) <= MAX_FILE_SIZE]
        if not valid_files:
            await status_msg.edit_text(get_text(user_id, "file_too_large"))
            return

        await status_msg.edit_text(get_text(user_id, "uploading"))

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
    auto_generate_cookies()
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
