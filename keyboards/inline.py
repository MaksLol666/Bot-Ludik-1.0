from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

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
    builder.row(
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="game_blackjack"),
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

def get_top_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для топов"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Богачи", callback_data="top_balance"),
        InlineKeyboardButton(text="🃏 Рулетка", callback_data="top_roulette")
    )
    builder.row(
        InlineKeyboardButton(text="🎰 Слоты", callback_data="top_slots"),
        InlineKeyboardButton(text="🎲 Кости", callback_data="top_dice")
    )
    builder.row(
        InlineKeyboardButton(text="💣 Мины", callback_data="top_mines"),
        InlineKeyboardButton(text="🎟 Лотерея", callback_data="top_lottery")
    )
    builder.row(
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="top_blackjack"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_glc_shop_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для GLC магазина"""
    builder = InlineKeyboardBuilder()
    
    from handlers.glc import GLC_STATUSES
    
    all_statuses = list(GLC_STATUSES.items())
    pages = [all_statuses[i:i+10] for i in range(0, len(all_statuses), 10)]
    
    if page < len(pages):
        for key, status in pages[page]:
            builder.row(InlineKeyboardButton(
                text=f"{status['icon']} {status['name']} - {status['price']} GLC",
                callback_data=f"buy_status_{key}"
            ))
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"shop_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"shop_page_{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="glc_info"))
    
    return builder.as_markup()

# ========== ОБРАБОТЧИКИ КНОПОК ==========

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("🎮 Главное меню:", reply_markup=get_main_menu())
    await callback.answer()

@router.callback_query(F.data == "casino_menu")
async def casino_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎰 <b>Казино Лудик</b>\n\nВыбери игру:",
        reply_markup=get_casino_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "game_roulette")
async def roulette_callback(callback: CallbackQuery):
    from handlers.roulette import roulette_help
    await roulette_help(callback)

@router.callback_query(F.data == "game_slots")
async def slots_callback(callback: CallbackQuery):
    from handlers.games import slots_help
    await slots_help(callback)

@router.callback_query(F.data == "game_dice")
async def dice_callback(callback: CallbackQuery):
    from handlers.dice_duel import dice_help
    await dice_help(callback)

@router.callback_query(F.data == "game_mines")
async def mines_callback(callback: CallbackQuery):
    from handlers.mines import mines_help
    await mines_help(callback)

@router.callback_query(F.data == "game_blackjack")
async def blackjack_callback(callback: CallbackQuery):
    from handlers.blackjack import blackjack_help
    await blackjack_help(callback)

@router.callback_query(F.data == "donate_menu")
async def donate_callback(callback: CallbackQuery):
    from handlers.donate import show_donate
    await show_donate(callback.message)
    await callback.answer()

@router.callback_query(F.data == "glc_info")
async def glc_info_callback(callback: CallbackQuery):
    from handlers.glc import cmd_glc
    await cmd_glc(callback.message)
    await callback.answer()

@router.callback_query(F.data == "glc_shop")
async def glc_shop_callback(callback: CallbackQuery):
    from handlers.glc import glc_shop
    await glc_shop(callback)

@router.callback_query(F.data == "top_menu")
async def top_menu_callback(callback: CallbackQuery):
    text = "🏆 <b>Выбери категорию топов:</b>"
    await callback.message.edit_text(text, reply_markup=get_top_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("top_"))
async def top_category_callback(callback: CallbackQuery):
    from handlers.top import show_top_command
    
    top_type = callback.data.replace("top_", "")
    
    if top_type == "balance":
        await show_top_command(callback.message, "tb")
    elif top_type == "roulette":
        await show_top_command(callback.message, "tr")
    elif top_type == "slots":
        await show_top_command(callback.message, "ts")
    elif top_type == "dice":
        await show_top_command(callback.message, "tk")
    elif top_type == "mines":
        await show_top_command(callback.message, "tm")
    elif top_type == "lottery":
        await show_top_command(callback.message, "tl")
    elif top_type == "blackjack":
        await show_top_command(callback.message, "tbj")
    
    await callback.answer()

@router.callback_query(F.data == "info")
async def info_callback(callback: CallbackQuery):
    from handlers.start import show_info
    await show_info(callback)

@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    from handlers.start import check_subscription
    await check_subscription(callback)
