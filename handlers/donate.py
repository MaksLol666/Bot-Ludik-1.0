from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from config import ADMIN_USERNAME, ADMIN_IDS

router = Router()

DONATE_TARIFFS = {
    100: 20000,
    200: 30000,
    300: 40000,
    400: 50000,
    500: 60000,
    600: 70000,
    700: 80000,
    800: 90000,
    900: 100000,
    1000: 110000
}

async def show_donate(message: Message):
    """Показать меню доната"""
    text = "💰 <b>ДОНАТ</b>\n\n"
    text += "Пополни баланс и получи бонус!\n\n"
    text += "<b>Тарифы:</b>\n"
    
    for rub, lc in DONATE_TARIFFS.items():
        text += f"• {rub}₽ — {lc} #LC\n"
    
    text += f"\n💎 <b>Специальное предложение:</b>\n"
    text += f"• 500₽ — Богатый бизнес (50к #LC/день)\n\n"
    text += f"Для оплаты напиши админу: {ADMIN_USERNAME}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from keyboards.inline import get_back_button
    
    keyboard_rows = []
    for rub, lc in list(DONATE_TARIFFS.items())[:5]:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{rub}₽ → {lc} LC", 
                callback_data=f"donate_{rub}"
            )
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="💎 Бизнес 500₽", 
            callback_data="donate_business"
        )
    ])
    
    # Добавляем кнопку назад
    keyboard_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await message.answer(text, reply_markup=keyboard)

@router.message(Command("donate"))
async def cmd_donate(message: Message):
    await show_donate(message)

@router.callback_query(F.data == "donate_menu")
async def donate_menu_callback(callback: CallbackQuery):
    await show_donate(callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("donate_"))
async def process_donate(callback: CallbackQuery):
    data = callback.data.replace("donate_", "")
    
    if data == "business":
        amount = 500
        text = "💎 Богатый бизнес"
    else:
        amount = int(data)
        text = f"{amount}₽"
    
    admin_text = (
        f"💰 <b>ЗАПРОС ДОНАТА</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {callback.from_user.id})\n"
        f"💵 Сумма: {amount}₽\n"
    )
    
    # Отправляем админу
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(admin_id, admin_text)
        except:
            pass
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        f"✅ <b>Запрос отправлен!</b>\n\n"
        f"Ты выбрал: {text}\n"
        f"Ожидай подтверждения от админа.\n"
        f"После оплаты напиши ему: {ADMIN_USERNAME}",
        reply_markup=keyboard
    )
    await callback.answer()

async def process_paid_business(user_id: int):
    """Выдача платного бизнеса"""
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    existing = cursor.fetchone()
    
    if existing:
        return False, "У пользователя уже есть бизнес"
    
    conn.execute("""
        INSERT INTO business (user_id, business_type, last_collected)
        VALUES (?, 'paid', datetime('now'))
    """, (user_id,))
    conn.commit()
    
    return True, "Бизнес выдан"

def process_paid_donate(user_id: int, amount_rub: int, is_business: bool = False):
    """Обработка подтвержденного доната"""
    if is_business:
        return process_paid_business(user_id)
    else:
        if amount_rub in DONATE_TARIFFS:
            lc_amount = DONATE_TARIFFS[amount_rub]
        else:
            lc_amount = amount_rub * 200
        
        db.update_balance(user_id, lc_amount)
        return True, f"Начислено {lc_amount} LC"

# ===== НОВАЯ ФУНКЦИЯ ДЛЯ REPLY КНОПКИ =====

async def show_donate_reply(message: Message):
    """Показать меню доната для Reply кнопки"""
    text = "💰 <b>ДОНАТ</b>\n\n"
    text += "Пополни баланс и получи бонус!\n\n"
    text += "<b>Тарифы:</b>\n"
    
    for rub, lc in DONATE_TARIFFS.items():
        text += f"• {rub}₽ — {lc} #LC\n"
    
    text += f"\n💎 <b>Специальное предложение:</b>\n"
    text += f"• 500₽ — Богатый бизнес (50к #LC/день)\n\n"
    text += f"Для оплаты напиши команду /donate или напиши админу: {ADMIN_USERNAME}"
    
    from keyboards.reply import get_main_menu_keyboard
    await message.answer(text, reply_markup=get_main_menu_keyboard())
