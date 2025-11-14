from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, InlineQueryHandler
import uuid
from datetime import datetime, timedelta
from reminders import create_reminder, calculate_time_from_text
from keyboards import get_inline_quick_reminders

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка инлайн-запросов"""
    query = update.inline_query.query
    
    if not query:
        return
    
    results = []
    
    # Быстрые напоминания
    quick_reminders = [
        {
            "title": "⏰ Напомнить через 1 час",
            "description": f"Напомнить: {query}",
            "time_data": "inline_1h"
        },
        {
            "title": "⏰ Напомнить через 3 часа", 
            "description": f"Напомнить: {query}",
            "time_data": "inline_3h"
        },
        {
            "title": "✏️ Настроить время",
            "description": f"Установить свое время для: {query}",
            "time_data": "inline_custom"
        }
    ]
    
    for reminder in quick_reminders:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=reminder["title"],
                description=reminder["description"],
                input_message_content=InputTextMessageContent(
                    f"🔔 Напоминание: {query}\n\n"
                    f"⏰ Время: {reminder['title'].replace('⏰ ', '').replace('✏️ ', '')}"
                ),
                reply_markup=get_inline_quick_reminders()
            )
        )
    
    await update.inline_query.answer(results, cache_time=1)

async def handle_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от инлайн-кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    message_text = query.message.text
    
    # Извлекаем текст напоминания из сообщения
    reminder_text = message_text.replace("🔔 Напоминание: ", "").split("\n\n")[0]
    
    if query.data.startswith("inline_"):
        time_key = query.data
        
        if time_key == "inline_custom":
            await query.message.reply_text(
                "⏰ Введите время для напоминания в формате:\n"
                "• Через 2 часа\n" 
                "• Завтра в 15:30\n"
                "• 20.12.2023 18:00"
            )
            return
        
        # Создаем напоминание для быстрых вариантов
        reminder_time = calculate_time_from_text(time_key)
        
        if reminder_time:
            reminder_id = create_reminder(user_id, chat_id, reminder_text, reminder_time)
            
            if reminder_id:
                await query.edit_message_text(
                    f"✅ Напоминание создано!\n\n"
                    f"📝 Текст: {reminder_text}\n"
                    f"⏰ Время: {reminder_time.strftime('%d.%m.%Y %H:%M')}",
                    reply_markup=None
                )
            else:
                await query.edit_message_text("❌ Ошибка при создании напоминания")
        else:
            await query.edit_message_text("❌ Не удалось распознать время")
