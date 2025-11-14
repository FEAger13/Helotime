from flask import Flask, request
from bot import main, setup_handlers
from reminders import load_unsent_reminders
import config
from telegram.ext import Application
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Создаем application
application = Application.builder().token(config.BOT_TOKEN).build()
setup_handlers(application)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    update = Update.de_json(request.get_json(), application.bot)
    application.update_queue.put(update)
    return 'ok'

def setup_webhook(app_instance):
    """Настраивает webhook для бота"""
    try:
        app_instance.bot.set_webhook(config.WEBHOOK_URL)
        logger.info(f"Webhook set to: {config.WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

if __name__ == "__main__":
    # Загружаем неотправленные напоминания при запуске
    load_unsent_reminders()
    
    # Настраиваем webhook
    setup_webhook(application)
    
    # Запускаем Flask app
    app.run(host='0.0.0.0', port=config.PORT)
