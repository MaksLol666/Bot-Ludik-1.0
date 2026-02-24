from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database_sqlite import db
from keyboards.inline import get_back_button

router = Router()

class PromoState(StatesGroup):
    waiting_for_code = State()

@router.callback_query(F.data == "activate_promo")
async def activate_promo_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoState.waiting_for_code)
    await callback.message.edit_text(
        "🎫 <b>Введи промокод:</b>\n\n"
        "Отправь его в чат одним сообщением.",
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(PromoState.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT * FROM promocodes WHERE code = ?",
        (code,)
    )
    promo = cursor.fetchone()
    
    if not promo:
        await message.answer("❌ Промокод не найден!")
        await state.clear()
        return
    
    if promo[3] >= promo[2]:  # used_count >= max_uses
        await message.answer("❌ Промокод уже использован максимальное количество раз!")
        await state.clear()
        return
    
    cursor = conn.execute(
        "SELECT * FROM used_promocodes WHERE user_id = ? AND code = ?",
        (user_id, code)
    )
    used = cursor.fetchone()
    
    if used:
        await message.answer("❌ Ты уже активировал этот промокод!")
        await state.clear()
        return
    
    conn.execute(
        "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
        (code,)
    )
    conn.execute(
        "INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)",
        (user_id, code)
    )
    conn.commit()
    
    new_balance = db.update_balance(user_id, promo[1])
    
    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"Ты получил: +{promo[1]} LC\n"
        f"💰 Текущий баланс: {new_balance} LC"
    )
    await state.clear()

@router.message(Command("promo"))
async def cmd_promo(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: /promo КОД")
        return
    
    code = args[1]
    user_id = message.from_user.id
    
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT * FROM promocodes WHERE code = ?",
        (code,)
    )
    promo = cursor.fetchone()
    
    if not promo:
        await message.answer("❌ Промокод не найден!")
        return
    
    if promo[3] >= promo[2]:
        await message.answer("❌ Лимит использований исчерпан!")
        return
    
    cursor = conn.execute(
        "SELECT * FROM used_promocodes WHERE user_id = ? AND code = ?",
        (user_id, code)
    )
    used = cursor.fetchone()
    
    if used:
        await message.answer("❌ Ты уже активировал этот промокод!")
        return
    
    conn.execute(
        "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
        (code,)
    )
    conn.execute(
        "INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)",
        (user_id, code)
    )
    conn.commit()
    
    new_balance = db.update_balance(user_id, promo[1])
    
    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"+{promo[1]} LC\n"
        f"Баланс: {new_balance} LC"
    )

# ===== НОВАЯ ФУНКЦИЯ ДЛЯ REPLY КНОПКИ =====

async def promo_start_reply(message: Message):
    """Начало активации промокода для Reply кнопки"""
    await message.answer(
        "🎫 <b>Активация промокода</b>\n\n"
        "Введи промокод командой:\n"
        "<code>/promo КОД</code>\n\n"
        "Пример: <code>/promo NEW</code>"
    )
