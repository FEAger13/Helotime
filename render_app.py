import config
from bot import main
from reminders import load_unsent_reminders
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Загружаем неотправленные напоминания
    load_unsent_reminders()
    
    # Запускаем бота с polling
    logger.info("🚀 Starting bot with polling...")
    main()
