from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()  # ДОБАВИТЬ ЭТУ СТРОКУ В НАЧАЛО ФАЙЛА

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
        InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")
    )
    builder.row(
        InlineKeyboardButton(text="💰 GLC", callback_data="glc_info")
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
    builder.row(
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="game_blackjack"),  # НОВАЯ КНОПКА
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
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

def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

# ДОБАВИТЬ ЭТОТ ОБРАБОТЧИК В КОНЕЦ ФАЙЛА
@router.callback_query(F.data == "game_blackjack")
async def blackjack_help(callback: CallbackQuery):
    text = (
        "🃏 <b>Блэкджек (21)</b>\n\n"
        "<b>Как играть:</b>\n"
        "Напиши в чат команду:\n"
        "<code>бджек [ставка]</code>\n\n"
        "<b>Пример:</b>\n"
        "бджек 1000\n\n"
        "<b>Правила:</b>\n"
        "• Нужно набрать 21 или ближе к 21\n"
        "• Карты от 2 до 10 - по номиналу\n"
        "• Валет, Дама, Король - 10 очков\n"
        "• Туз - 11 или 1 очко\n"
        "• Блэкджек (21 с двух карт) дает выигрыш x2.5"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()
