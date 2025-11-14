from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# --- Обычные клавиатуры ---
def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = [
        ["📅 Создать напоминание", "📋 Мои напоминания"],
        ["⏰ Быстрое напоминание", "❌ Удалить все"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_quick_time_keyboard():
    """Клавиатура для быстрого выбора времени"""
    keyboard = [
        ["⏱ Через 1 час", "⏱ Через 3 часа"],
        ["🌅 Завтра утром", "🌆 Сегодня вечером"],
        ["✏️ Свое время...", "🔙 Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура для отмены"""
    return ReplyKeyboardMarkup([['❌ Отмена']], one_time_keyboard=True, resize_keyboard=True)

def remove_keyboard():
    """Убрать клавиатуру"""
    return ReplyKeyboardRemove()

# --- Инлайн клавиатуры ---
def get_reminder_actions_keyboard(reminder_id):
    """Инлайн-кнопки для действий с напоминанием"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{reminder_id}"),
            InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{reminder_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_inline_quick_reminders():
    """Инлайн-кнопки для быстрых напоминаний в инлайн-режиме"""
    keyboard = [
        [
            InlineKeyboardButton("⏰ Через 1 час", callback_data="inline_1h"),
            InlineKeyboardButton("⏰ Через 3 часа", callback_data="inline_3h")
        ],
        [
            InlineKeyboardButton("📝 Свое время", callback_data="inline_custom")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
