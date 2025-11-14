import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") + "/webhook"
PORT = int(os.getenv("PORT", 5000))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///reminders.db")
