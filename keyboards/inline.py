from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для /start"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📰 Подписаться", url="https://t.me/BotLudik_chanels"),
        InlineKeyboardButton(text="🔄 Проверить", callback_data="check_sub")
    )
    builder.row(InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"))
    return builder.as_markup()

def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Казино", callback_data="casino_menu"),
        InlineKeyboardButton(text="🎟 Лотерея", callback_data="lottery_menu")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Донат", callback_data="donate_menu"),
        InlineKeyboardButton(text="🎁 Бонус", callback_data="get_bonus")
    )
    builder.row(
        InlineKeyboardButton(text="💼 Бизнес", callback_data="business_menu"),
        InlineKeyboardButton(text="👤 Моя стата", callback_data="my_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Топы", callback_data="top_menu"),
        InlineKeyboardButton(text="🎫 Промокод", callback_data="activate_promo")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Рефералы", callback_data="referral_menu"),
        InlineKeyboardButton(text="💰 GLC", callback_data="glc_info")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Квесты", callback_data="daily_quests"),
        InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")
    )
    return builder.as_markup()

def get_casino_menu() -> InlineKeyboardMarkup:
    """Меню казино"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Рулетка", callback_data="game_roulette"),
        InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")
    )
    builder.row(
        InlineKeyboardButton(text="🎲 Кости", callback_data="game_dice"),
        InlineKeyboardButton(text="💣 Мины", callback_data="game_mines")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_roulette_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для рулетки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔴 КРАСНОЕ", callback_data="roulette_red"),
        InlineKeyboardButton(text="⚫ ЧЕРНОЕ", callback_data="roulette_black")
    )
    
    numbers_row1 = []
    for i in range(1, 13):
        numbers_row1.append(InlineKeyboardButton(text=str(i), callback_data=f"roulette_num_{i}"))
    builder.row(*numbers_row1)
    
    numbers_row2 = []
    for i in range(13, 25):
        numbers_row2.append(InlineKeyboardButton(text=str(i), callback_data=f"roulette_num_{i}"))
    builder.row(*numbers_row2)
    
    numbers_row3 = []
    for i in range(25, 37):
        numbers_row3.append(InlineKeyboardButton(text=str(i), callback_data=f"roulette_num_{i}"))
    builder.row(*numbers_row3)
    
    builder.row(
        InlineKeyboardButton(text="0️⃣ НОЛЬ", callback_data="roulette_num_0"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_casino")
    )
    
    return builder.as_markup()

def get_business_menu() -> InlineKeyboardMarkup:
    """Меню бизнеса"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="20к (2.5к/день)", callback_data="buy_business_small"),
        InlineKeyboardButton(text="50к (5.5к/день)", callback_data="buy_business_medium")
    )
    builder.row(
        InlineKeyboardButton(text="100к (10.5к/день)", callback_data="buy_business_large"),
        InlineKeyboardButton(text="💎 500₽ (50к/день)", callback_data="buy_business_paid")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Собрать", callback_data="collect_business"),
        InlineKeyboardButton(text="📊 Мой бизнес", callback_data="my_business")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_daily_quests_keyboard(quests: list) -> InlineKeyboardMarkup:
    """Клавиатура для ежедневных квестов"""
    builder = InlineKeyboardBuilder()
    
    for quest in quests:
        if quest['completed'] and not quest['claimed']:
            builder.row(InlineKeyboardButton(
                text=f"🎁 Забрать {quest['reward_lc']} LC + {quest['reward_glc']} GLC",
                callback_data=f"claim_quest_{quest['id']}"
            ))
    
    builder.row(InlineKeyboardButton(text="🔄 Обновить", callback_data="daily_quests"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_back_to_casino() -> InlineKeyboardMarkup:
    """Кнопка назад в казино"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад в казино", callback_data="back_to_casino"))
    return builder.as_markup()
