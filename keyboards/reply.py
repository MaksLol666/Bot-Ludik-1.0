from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Основная Reply клавиатура для ЛС"""
    keyboard = [
        [KeyboardButton(text="🎰 Казино"), KeyboardButton(text="🎟 Лотерея")],
        [KeyboardButton(text="💰 Донат"), KeyboardButton(text="🎁 Бонус")],
        [KeyboardButton(text="💼 Бизнес"), KeyboardButton(text="👤 Моя стата")],
        [KeyboardButton(text="🏆 Топы"), KeyboardButton(text="🎫 Промокод")],
        [KeyboardButton(text="👥 Рефералы"), KeyboardButton(text="💰 GLC")],
        [KeyboardButton(text="ℹ️ Инфо")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_casino_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура для казино в ЛС"""
    keyboard = [
        [KeyboardButton(text="🃏 Рулетка"), KeyboardButton(text="🎰 Слоты")],
        [KeyboardButton(text="🎲 Кости"), KeyboardButton(text="💣 Мины")],
        [KeyboardButton(text="🃏 Блэкджек")],
        [KeyboardButton(text="◀️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_business_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура для бизнеса в ЛС"""
    keyboard = [
        [KeyboardButton(text="20к (2.5к/день)"), KeyboardButton(text="50к (5.5к/день)")],
        [KeyboardButton(text="100к (10.5к/день)"), KeyboardButton(text="💎 500₽ (50к/день)")],
        [KeyboardButton(text="💰 Собрать"), KeyboardButton(text="📊 Мой бизнес")],
        [KeyboardButton(text="◀️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_top_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура для топов в ЛС"""
    keyboard = [
        [KeyboardButton(text="💰 Богачи"), KeyboardButton(text="🃏 Рулетка")],
        [KeyboardButton(text="🎰 Слоты"), KeyboardButton(text="🎲 Кости")],
        [KeyboardButton(text="💣 Мины"), KeyboardButton(text="🎟 Лотерея")],
        [KeyboardButton(text="🃏 Блэкджек")],
        [KeyboardButton(text="◀️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_glc_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура для GLC в ЛС"""
    keyboard = [
        [KeyboardButton(text="🛒 Магазин статусов")],
        [KeyboardButton(text="◀️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def remove_keyboard():
    """Удалить клавиатуру"""
    return ReplyKeyboardRemove()
