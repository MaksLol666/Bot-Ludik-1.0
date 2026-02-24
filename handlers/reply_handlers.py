from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from handlers import (
    games, dice_duel, mines, lottery, profile, top, 
    promo, business, donate, bonus, referral, blackjack, glc
)
from keyboards.reply import (
    get_casino_reply_keyboard, get_business_reply_keyboard,
    get_top_reply_keyboard, get_glc_reply_keyboard, get_main_menu_keyboard
)

router = Router()

def is_private_chat(message: Message) -> bool:
    """Проверяет, является ли чат личным"""
    return message.chat.type == ChatType.PRIVATE

# ===== ГЛАВНОЕ МЕНЮ =====

@router.message(F.text == "🎰 Казино")
async def casino_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer("🎰 <b>Казино</b>\n\nВыбери игру:", reply_markup=get_casino_reply_keyboard())

@router.message(F.text == "🎟 Лотерея")
async def lottery_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.lottery import lottery_menu
    await lottery_menu(message)

@router.message(F.text == "💰 Донат")
async def donate_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.donate import show_donate
    await show_donate(message)

@router.message(F.text == "🎁 Бонус")
async def bonus_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.bonus import get_bonus_reply
    await get_bonus_reply(message)

@router.message(F.text == "💼 Бизнес")
async def business_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer("💼 <b>Бизнес</b>\n\nВыбери действие:", reply_markup=get_business_reply_keyboard())

@router.message(F.text == "👤 Моя стата")
async def profile_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.profile import show_my_stats
    await show_my_stats(message)

@router.message(F.text == "🏆 Топы")
async def top_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer("🏆 <b>Топы</b>\n\nВыбери категорию:", reply_markup=get_top_reply_keyboard())

@router.message(F.text == "🎫 Промокод")
async def promo_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.promo import activate_promo_start_reply
    await activate_promo_start_reply(message)

@router.message(F.text == "👥 Рефералы")
async def referral_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.referral import referral_menu_reply
    await referral_menu_reply(message)

@router.message(F.text == "💰 GLC")
async def glc_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer("💰 <b>GLC</b>\n\nВыбери действие:", reply_markup=get_glc_reply_keyboard())

@router.message(F.text == "ℹ️ Инфо")
async def info_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.start import show_info_reply
    await show_info_reply(message)

# ===== МЕНЮ КАЗИНО =====

@router.message(F.text == "🃏 Рулетка")
async def roulette_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.roulette import roulette_help_reply
    await roulette_help_reply(message)

@router.message(F.text == "🎰 Слоты")
async def slots_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.games import slots_help_reply
    await slots_help_reply(message)

@router.message(F.text == "🎲 Кости")
async def dice_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.dice_duel import dice_help_reply
    await dice_help_reply(message)

@router.message(F.text == "💣 Мины")
async def mines_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.mines import mines_help_reply
    await mines_help_reply(message)

@router.message(F.text == "🃏 Блэкджек")
async def blackjack_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.blackjack import blackjack_help_reply
    await blackjack_help_reply(message)

# ===== МЕНЮ БИЗНЕСА =====

@router.message(F.text == "20к (2.5к/день)")
async def buy_small_business_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.business import buy_business_reply
    await buy_business_reply(message, "small")

@router.message(F.text == "50к (5.5к/день)")
async def buy_medium_business_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.business import buy_business_reply
    await buy_business_reply(message, "medium")

@router.message(F.text == "100к (10.5к/день)")
async def buy_large_business_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.business import buy_business_reply
    await buy_business_reply(message, "large")

@router.message(F.text == "💎 500₽ (50к/день)")
async def buy_paid_business_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.business import buy_business_reply
    await buy_business_reply(message, "paid")

@router.message(F.text == "💰 Собрать")
async def collect_business_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.business import collect_business_reply
    await collect_business_reply(message)

@router.message(F.text == "📊 Мой бизнес")
async def my_business_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.business import my_business_reply
    await my_business_reply(message)

# ===== МЕНЮ ТОПОВ =====

@router.message(F.text == "💰 Богачи")
async def top_balance_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "tb")

@router.message(F.text == "🃏 Рулетка")
async def top_roulette_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "tr")

@router.message(F.text == "🎰 Слоты")
async def top_slots_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "ts")

@router.message(F.text == "🎲 Кости")
async def top_dice_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "tk")

@router.message(F.text == "💣 Мины")
async def top_mines_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "tm")

@router.message(F.text == "🎟 Лотерея")
async def top_lottery_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "tl")

@router.message(F.text == "🃏 Блэкджек")
async def top_blackjack_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import show_top_reply
    await show_top_reply(message, "tbj")

# ===== МЕНЮ GLC =====

@router.message(F.text == "🛒 Магазин статусов")
async def glc_shop_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.glc import glc_shop_reply
    await glc_shop_reply(message)

# ===== НАЗАД =====

@router.message(F.text == "◀️ Назад в меню")
async def back_to_menu(message: Message):
    if not is_private_chat(message):
        return
    await message.answer("🎮 Главное меню:", reply_markup=get_main_menu_keyboard())
