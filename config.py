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
COOKIES_FILE = str(os.getenv("COOKIES_FILE") or "")
OUTPUT_DIR = "downloads"

BOT_COMMANDS = [
    {'command': 'start', 'description': '🚀Початок роботи / Get started🔥'},
    {'command': 'settings', 'description': '⚙️Налаштування / Settings🛠'},
    {'command': 'stats', 'description': '📊Статистика / Statistics📈'},
]

ADMINS_UID = [admin_id]

PORT = int(os.getenv("PORT", "8080"))
