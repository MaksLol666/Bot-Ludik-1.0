from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from database_sqlite import db
from handlers import (
    games, dice_duel, mines, lottery, profile, top, 
    promo, business, donate, bonus, referral, blackjack, glc, roulette
)
from keyboards.reply import (
    get_casino_reply_keyboard, get_business_reply_keyboard,
    get_top_reply_keyboard, get_glc_reply_keyboard, get_main_menu_keyboard
)
from keyboards.inline import get_back_button

router = Router()

def is_private_chat(message: Message) -> bool:
    """Проверяет, является ли чат личным"""
    return message.chat.type == ChatType.PRIVATE

# ===== ГЛАВНОЕ МЕНЮ =====

@router.message(F.text == "🎰 Казино")
async def casino_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer(
        "🎰 <b>Казино</b>\n\nВыбери игру и напиши команду с ставкой.\n\n"
        "Пример: <code>рул красное 1000</code>",
        reply_markup=get_casino_reply_keyboard()
    )

@router.message(F.text == "🎟 Лотерея")
async def lottery_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.lottery import lottery_menu_reply
    await lottery_menu_reply(message)

@router.message(F.text == "💰 Донат")
async def donate_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.donate import show_donate_reply
    await show_donate_reply(message)

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
    from handlers.business import business_menu_reply
    await business_menu_reply(message)

@router.message(F.text == "👤 Моя стата")
async def profile_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.profile import show_my_stats_reply
    await show_my_stats_reply(message)

@router.message(F.text == "🏆 Топы")
async def top_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.top import top_menu_reply
    await top_menu_reply(message)

@router.message(F.text == "🎫 Промокод")
async def promo_reply(message: Message):
    if not is_private_chat(message):
        return
    from handlers.promo import promo_start_reply
    await promo_start_reply(message)

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
    from handlers.glc import glc_menu_reply
    await glc_menu_reply(message)

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
    await message.answer(
        "🃏 <b>Рулетка</b>\n\n"
        "Напиши команду в формате:\n"
        "<code>рул [ставка] [цвет/число]</code>\n\n"
        "Примеры:\n"
        "<code>рул красное 1000</code>\n"
        "<code>рул черное 500</code>\n"
        "<code>рул 7 2000</code>"
    )

@router.message(F.text == "🎰 Слоты")
async def slots_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer(
        "🎰 <b>Слоты</b>\n\n"
        "Напиши команду в формате:\n"
        "<code>слоты [ставка]</code>\n\n"
        "Пример:\n"
        "<code>слоты 1000</code>"
    )

@router.message(F.text == "🎲 Кости")
async def dice_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer(
        "🎲 <b>Кости (дуэль)</b>\n\n"
        "Напиши команду в формате:\n"
        "<code>кости [ставка]</code>\n\n"
        "Пример:\n"
        "<code>кости 1000</code>"
    )

@router.message(F.text == "💣 Мины")
async def mines_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer(
        "💣 <b>Мины</b>\n\n"
        "Напиши команду в формате:\n"
        "<code>мины [ставка]</code>\n\n"
        "Пример:\n"
        "<code>мины 1000</code>"
    )

@router.message(F.text == "🃏 Блэкджек")
async def blackjack_reply(message: Message):
    if not is_private_chat(message):
        return
    await message.answer(
        "🃏 <b>Блэкджек (21)</b>\n\n"
        "Напиши команду в формате:\n"
        "<code>бджек [ставка]</code>\n\n"
        "Пример:\n"
        "<code>бджек 1000</code>"
    )

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
    await message.answer(
        "💎 <b>Платный бизнес</b>\n\n"
        "Для покупки напиши /donate и выбери 'Бизнес 500₽'"
    )

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
