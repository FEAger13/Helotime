from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from telegram import Bot
from database import SessionLocal, Reminder
import config
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
scheduler = BackgroundScheduler()

def send_reminder(reminder_id):
    """Функция для отправки напоминания"""
    db_session = SessionLocal()
    try:
        reminder = db_session.query(Reminder).filter_by(id=reminder_id).first()
        
        if reminder and not reminder.is_sent:
            from keyboards import get_reminder_actions_keyboard
            
            bot.send_message(
                chat_id=reminder.chat_id,
                text=f"🔔 **Напоминание!**\n\n{reminder.reminder_text}",
                reply_markup=get_reminder_actions_keyboard(reminder_id),
                parse_mode='Markdown'
            )
            reminder.is_sent = True
            db_session.commit()
            logger.info(f"Напоминание {reminder_id} отправлено пользователю {reminder.user_id}")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания {reminder_id}: {e}")
    finally:
        db_session.close()

def schedule_reminder(reminder_id, reminder_time):
    """Добавляет напоминание в планировщик"""
    scheduler.add_job(
        send_reminder,
        trigger=DateTrigger(run_date=reminder_time),
        args=[reminder_id],
        id=f"reminder_{reminder_id}",
        replace_existing=True
    )
    logger.info(f"Напоминание {reminder_id} запланировано на {reminder_time}")

def create_reminder(user_id, chat_id, text, time):
    """Создает новое напоминание"""
    db_session = SessionLocal()
    try:
        reminder = Reminder(
            user_id=user_id,
            chat_id=chat_id,
            reminder_text=text,
            reminder_time=time
        )
        db_session.add(reminder)
        db_session.commit()
        
        schedule_reminder(reminder.id, time)
        return reminder.id
    except Exception as e:
        db_session.rollback()
        logger.error(f"Ошибка при создании напоминания: {e}")
        return None
    finally:
        db_session.close()

def get_user_reminders(user_id):
    """Получает все напоминания пользователя"""
    db_session = SessionLocal()
    try:
        reminders = db_session.query(Reminder).filter_by(
            user_id=user_id, 
            is_sent=False
        ).order_by(Reminder.reminder_time.asc()).all()
        return reminders
    except Exception as e:
        logger.error(f"Ошибка при получении напоминаний: {e}")
        return []
    finally:
        db_session.close()

def delete_reminder(reminder_id):
    """Удаляет напоминание"""
    db_session = SessionLocal()
    try:
        reminder = db_session.query(Reminder).filter_by(id=reminder_id).first()
        if reminder:
            db_session.delete(reminder)
            db_session.commit()
            
            # Удаляем задание из планировщика
            try:
                scheduler.remove_job(f"reminder_{reminder_id}")
            except Exception as e:
                logger.warning(f"Задание планировщика для {reminder_id} не найдено: {e}")
            
            return True
        return False
    except Exception as e:
        db_session.rollback()
        logger.error(f"Ошибка при удалении напоминания {reminder_id}: {e}")
        return False
    finally:
        db_session.close()

def delete_all_user_reminders(user_id):
    """Удаляет все напоминания пользователя"""
    db_session = SessionLocal()
    try:
        reminders = db_session.query(Reminder).filter_by(user_id=user_id).all()
        count = len(reminders)
        
        for reminder in reminders:
            db_session.delete(reminder)
            # Удаляем задания из планировщика
            try:
                scheduler.remove_job(f"reminder_{reminder.id}")
            except Exception:
                pass
        
        db_session.commit()
        return count
    except Exception as e:
        db_session.rollback()
        logger.error(f"Ошибка при удалении всех напоминаний пользователя {user_id}: {e}")
        return 0
    finally:
        db_session.close()

def calculate_time_from_text(time_text):
    """Вычисляет время из текстового описания"""
    now = datetime.now()
    
    time_mapping = {
        "⏱ Через 1 час": now + timedelta(hours=1),
        "⏱ Через 3 часа": now + timedelta(hours=3),
        "🌆 Сегодня вечером": now.replace(hour=19, minute=0, second=0, microsecond=0),
        "🌅 Завтра утром": (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0),
        "inline_1h": now + timedelta(hours=1),
        "inline_3h": now + timedelta(hours=3)
    }
    
    return time_mapping.get(time_text)

def load_unsent_reminders():
    """Загружает все неотправленные напоминания при запуске бота"""
    db_session = SessionLocal()
    try:
        unsent_reminders = db_session.query(Reminder).filter_by(is_sent=False).all()
        for reminder in unsent_reminders:
            if reminder.reminder_time > datetime.now():
                schedule_reminder(reminder.id, reminder.reminder_time)
                logger.info(f"Загружено напоминание {reminder.id} на {reminder.reminder_time}")
            else:
                # Если время уже прошло, помечаем как отправленное
                reminder.is_sent = True
        db_session.commit()
    except Exception as e:
        logger.error(f"Ошибка при загрузке напоминаний: {e}")
        db_session.rollback()
    finally:
        db_session.close()

# Запускаем планировщик
scheduler.start()
