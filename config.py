import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
db_auth = str(os.getenv("db_auth") or os.getenv("DATABASE_URL") or "")
admin_id = os.getenv("admin_id")
admin_id = int(admin_id) if admin_id else 0
custom_api_url = str(os.getenv("custom_api_url") or "")
MEASUREMENT_ID = str(os.getenv("MEASUREMENT_ID") or "")
API_SECRET = str(os.getenv("API_SECRET") or "")
CHANNEL_ID = str(os.getenv("CHANNEL_ID") or "")
OUTPUT_DIR = "downloads"
INSTAGRAM_RAPID_API_HOST = str(os.getenv("INSTAGRAM_RAPID_API_HOST") or "")
INSTAGRAM_RAPID_API_KEY1 = str(os.getenv("INSTAGRAM_RAPID_API_KEY1") or "")
INSTAGRAM_RAPID_API_KEY2 = str(os.getenv("INSTAGRAM_RAPID_API_KEY2") or "")


BOT_COMMANDS = [
    {'command': 'start', 'description': '🚀Початок роботи / Get started🔥'},
    {'command': 'settings', 'description': '⚙️Налаштування / Settings🛠'},
    {'command': 'stats', 'description': '📊Статистика / Statistics📈'},
]

ADMINS_UID = [admin_id]

PORT = int(os.getenv("PORT", "8080"))
