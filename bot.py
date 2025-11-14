from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, InlineQueryHandler
import config
from reminders import create_reminder, get_user_reminders, delete_reminder, delete_all_user_reminders, calculate_time_from_text
from keyboards import get_main_keyboard, get_quick_time_keyboard, get_cancel_keyboard, remove_keyboard, get_reminder_actions_keyboard
from inline_handler import handle_inline_query, handle_inline_callback
from datetime import datetime, timedelta
import re

# Состояния для ConversationHandler
WAITING_TEXT, WAITING_TIME = range(2)

# Обработка неизвестных команд
UNKNOWN_COMMAND_RESPONSE = """
🤖 Я бот-напоминалка! Вот что я умею:

*Основные команды:*
/start - Начать работу
/help - Помощь
/remind - Создать напоминание
/my_reminders - Мои напоминания

*Быстрые действия через меню:*
📅 Создать напоминание
📋 Мои напоминания  
⏰ Быстрое напоминание
❌ Удалить все

*Инлайн-режим:*
Наберите `@{} напомнить купить молоко` в любом чате!

Нужна помощь? Используйте /help
"""

async def start(update: Update, context):
    """Обработка команды /start"""
    welcome_text = """
    🎉 Добро пожаловать в бот-напоминалку!

    *Что я умею:*
    • Создавать напоминания на любое время
    • Показывать ваши активные напоминания  
    • Работать в инлайн-режиме
    • Быстрые напоминания в один клик

    *Как пользоваться:*
    1. Используйте кнопки ниже
    2. Или команду /remind
    3. Или инлайн-режим: в любом чате напишите `@{} ваше_напоминание`

    Выберите действие ниже 👇
    """.format(context.bot.username)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context):
    """Обработка команды /help"""
    help_text = """
    📖 *Помощь по боту*

    *Создание напоминаний:*
    • Используйте кнопку "📅 Создать напоминание"
    • Или команду /remind
    • Или инлайн-режим в любом чате

    *Форматы времени:*
    • Через 2 часа
    • Завтра в 15:30
    • 25.12.2023 18:00
    • Сегодня вечером

    *Быстрые команды:*
    /my_reminders - показать все напоминания
    /cancel - отменить текущее действие

    *Инлайн-режим:*
    В любом чате напишите: `@{} ваше напоминание`
    """.format(context.bot.username)
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_unknown_command(update: Update, context):
    """Обработка неизвестных команд"""
    await update.message.reply_text(
        UNKNOWN_COMMAND_RESPONSE.format(context.bot.username),
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def handle_unknown_text(update: Update, context):
    """Обработка неизвестного текста"""
    text = update.message.text
    
    # Если это не команда, а просто текст
    if not text.startswith('/'):
        await update.message.reply_text(
            "🤔 Я не понимаю этот текст. Используйте кнопки ниже или команду /help для справки.",
            reply_markup=get_main_keyboard()
        )
    else:
        await handle_unknown_command(update, context)

async def button_handler(update: Update, context):
    """Обработка нажатий на кнопки главного меню"""
    text = update.message.text
    
    if text == "📅 Создать напоминание":
        await update.message.reply_text(
            "📝 Введите текст напоминания:",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_TEXT
        
    elif text == "📋 Мои напоминания":
        await show_user_reminders(update, context)
        
    elif text == "⏰ Быстрое напоминание":
        await update.message.reply_text(
            "⏰ Выберите время:",
            reply_markup=get_quick_time_keyboard()
        )
        context.user_data['quick_reminder'] = True
        return WAITING_TEXT
        
    elif text == "❌ Удалить все":
        await delete_all_reminders(update, context)
        
    elif text == "❌ Отмена":
        await update.message.reply_text(
            "❌ Действие отменено",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def show_user_reminders(update: Update, context):
    """Показывает напоминания пользователя"""
    user_id = update.effective_user.id
    reminders = get_user_reminders(user_id)
    
    if not reminders:
        await update.message.reply_text(
            "📭 У вас нет активных напоминаний",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = "📋 *Ваши напоминания:*\n\n"
    for reminder in reminders:
        time_str = reminder.reminder_time.strftime('%d.%m.%Y %H:%M')
        text += f"• {reminder.reminder_text}\n  ⏰ {time_str}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def delete_all_reminders(update: Update, context):
    """Удаляет все напоминания пользователя"""
    user_id = update.effective_user.id
    count = delete_all_user_reminders(user_id)
    
    await update.message.reply_text(
        f"✅ Удалено {count} напоминаний",
        reply_markup=get_main_keyboard()
    )

async def receive_reminder_text(update: Update, context):
    """Получает текст напоминания"""
    context.user_data['reminder_text'] = update.message.text
    
    if context.user_data.get('quick_reminder'):
        # Для быстрого напоминания время уже выбрано
        return await create_quick_reminder(update, context)
    else:
        await update.message.reply_text(
            "⏰ Теперь введите время напоминания:\n"
            "• Через 2 часа\n"
            "• Завтра в 15:30\n" 
            "• 25.12.2023 18:00\n"
            "• Сегодня вечером",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_TIME

async def create_quick_reminder(update: Update, context):
    """Создает быстрое напоминание"""
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    reminder_text = context.user_data['reminder_text']
    
    # Время уже выбрано через кнопку
    time_text = context.user_data.get('quick_time')
    reminder_time = calculate_time_from_text(time_text)
    
    if reminder_time:
        reminder_id = create_reminder(user_id, chat_id, reminder_text, reminder_time)
        
        if reminder_id:
            await update.message.reply_text(
                f"✅ Напоминание создано!\n\n"
                f"📝 *Текст:* {reminder_text}\n"
                f"⏰ *Время:* {reminder_time.strftime('%d.%m.%Y %H:%M')}",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при создании напоминания",
                reply_markup=get_main_keyboard()
            )
    else:
        await update.message.reply_text(
            "❌ Не удалось распознать время",
            reply_markup=get_main_keyboard()
        )
    
    # Очищаем данные
    context.user_data.clear()
    return ConversationHandler.END

async def receive_reminder_time(update: Update, context):
    """Получает время напоминания"""
    time_text = update.message.text
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    reminder_text = context.user_data['reminder_text']
    
    # Парсим время
    reminder_time = parse_time_input(time_text)
    
    if not reminder_time:
        await update.message.reply_text(
            "❌ Не могу распознать время. Попробуйте еще раз:\n"
            "• Через 2 часа\n"
            "• Завтра в 15:30\n"
            "• 25.12.2023 18:00",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_TIME
    
    # Создаем напоминание
    reminder_id = create_reminder(user_id, chat_id, reminder_text, reminder_time)
    
    if reminder_id:
        await update.message.reply_text(
            f"✅ Напоминание создано!\n\n"
            f"📝 *Текст:* {reminder_text}\n"
            f"⏰ *Время:* {reminder_time.strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка при создании напоминания",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()
    return ConversationHandler.END

def parse_time_input(time_text):
    """Парсит текстовый ввод времени"""
    now = datetime.now()
    
    # Через X часов/минут
    match = re.search(r'через\s+(\d+)\s*(час|часа|часов|ч|минут|минуты|мин)', time_text.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit in ['час', 'часа', 'часов', 'ч']:
            return now + timedelta(hours=value)
        else:
            return now + timedelta(minutes=value)
    
    # Завтра в X:Y
    match = re.search(r'завтра\s+в\s+(\d+):(\d+)', time_text.lower())
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Дата и время (DD.MM.YYYY HH:MM)
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})', time_text)
    if match:
        day, month, year, hour, minute = map(int, match.groups())
        return datetime(year, month, day, hour, minute)
    
    # Сегодня вечером/утром
    if "сегодня вечером" in time_text.lower():
        return now.replace(hour=19, minute=0, second=0, microsecond=0)
    elif "сегодня утром" in time_text.lower():
        return now.replace(hour=9, minute=0, second=0, microsecond=0)
    elif "завтра утром" in time_text.lower():
        return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    return None

async def handle_callback_query(update: Update, context):
    """Обработка callback от инлайн-кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('done_'):
        reminder_id = int(data.split('_')[1])
        if delete_reminder(reminder_id):
            await query.edit_message_text("✅ Напоминание выполнено!")
        else:
            await query.edit_message_text("❌ Ошибка при выполнении напоминания")
            
    elif data.startswith('delete_'):
        reminder_id = int(data.split('_')[1])
        if delete_reminder(reminder_id):
            await query.edit_message_text("✅ Напоминание удалено!")
        else:
            await query.edit_message_text("❌ Ошибка при удалении напоминания")
    
    # Обработка инлайн-режима
    elif data.startswith('inline_'):
        await handle_inline_callback(update, context)

async def cancel(update: Update, context):
    """Отмена текущего действия"""
    await update.message.reply_text(
        "❌ Действие отменено",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def quick_time_handler(update: Update, context):
    """Обработка быстрого выбора времени"""
    context.user_data['quick_time'] = update.message.text
    await update.message.reply_text(
        "📝 Введите текст напоминания:",
        reply_markup=get_cancel_keyboard()
    )
    return WAITING_TEXT

def setup_handlers(application):
    """Настройка обработчиков"""
    
    # Conversation Handler для создания напоминаний
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^(📅 Создать напоминание|⏰ Быстрое напоминание)$'), button_handler),
            CommandHandler('remind', button_handler)
        ],
        states={
            WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reminder_text)],
            WAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reminder_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(filters.Regex('^❌ Отмена$'), cancel)]
    )
    
    # Основные обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_reminders", show_user_reminders))
    
    # Обработчики кнопок и callback
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Инлайн-режим
    application.add_handler(InlineQueryHandler(handle_inline_query))
    
    # Обработка обычных сообщений (кнопки главного меню)
    application.add_handler(MessageHandler(filters.Regex('^(📋 Мои напоминания|❌ Удалить все|🔙 Назад)$'), button_handler))
    
    # Обработка быстрого выбора времени
    application.add_handler(MessageHandler(
        filters.Regex('^(⏱ Через 1 час|⏱ Через 3 часа|🌅 Завтра утром|🌆 Сегодня вечером)$'),
        quick_time_handler
    ))
    
    # Обработка неизвестных команд и текста
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_text))

def main():
    """Основная функция"""
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Настраиваем обработчики
    setup_handlers(application)
    
    # Запускаем бота
    if config.WEBHOOK_URL:
        # Для Render с webhook
        from app import setup_webhook
        setup_webhook(application)
    else:
        # Для локальной разработки с polling
        application.run_polling()

if __name__ == "__main__":
    main()
