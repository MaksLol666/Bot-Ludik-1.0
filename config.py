import os

# ВРЕМЕННО - токен прямо здесь
BOT_TOKEN = "7578048091:AAF1jFkII4yA29bmVU9EpObpErqjpBcSLDM"

# Проверка
if not BOT_TOKEN:
    raise ValueError("❌ Токен не указан!")

ADMIN_IDS = [1691654877]
ADMIN_USERNAME = "@CIM_KAPTbI_BIO"

# Эти переменные можно тоже указать прямо здесь
CHANNEL_ID = "@BotLudik_chanels"
CHANNEL_LINK = "https://t.me/BotLudik_chanels"
DATABASE_URL = "postgresql://postgres:postgres@localhost/ludik_db"

MIN_BET = 100
MAX_BET = 1000000

BONUS_COOLDOWN = 5 * 60 * 60
BONUS_MIN = 1000
BONUS_MAX = 10000

BOT_VERSION = "1.0"
BOT_RELEASE_DATE = "2024-04-15"

print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")
