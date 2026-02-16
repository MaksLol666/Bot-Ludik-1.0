from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
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
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        promo = await conn.fetchrow(
            "SELECT * FROM promocodes WHERE code = $1",
            code
        )
        
        if not promo:
            await message.answer("❌ Промокод не найден!")
            await state.clear()
            return
        
        if promo['used_count'] >= promo['max_uses']:
            await message.answer("❌ Промокод уже использован максимальное количество раз!")
            await state.clear()
            return
        
        used = await conn.fetchrow(
            "SELECT * FROM used_promocodes WHERE user_id = $1 AND code = $2",
            user_id, code
        )
        
        if used:
            await message.answer("❌ Ты уже активировал этот промокод!")
            await state.clear()
            return
        
        async with conn.transaction():
            await conn.execute(
                "UPDATE promocodes SET used_count = used_count + 1 WHERE code = $1",
                code
            )
            await conn.execute(
                "INSERT INTO used_promocodes (user_id, code) VALUES ($1, $2)",
                user_id, code
            )
            
            new_balance = await db.update_balance(user_id, promo['reward'])
    
    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"Ты получил: +{promo['reward']} LC\n"
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
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        promo = await conn.fetchrow(
            "SELECT * FROM promocodes WHERE code = $1",
            code
        )
        
        if not promo:
            await message.answer("❌ Промокод не найден!")
            return
        
        if promo['used_count'] >= promo['max_uses']:
            await message.answer("❌ Лимит использований исчерпан!")
            return
        
        used = await conn.fetchrow(
            "SELECT * FROM used_promocodes WHERE user_id = $1 AND code = $2",
            user_id, code
        )
        
        if used:
            await message.answer("❌ Ты уже активировал этот промокод!")
            return
        
        async with conn.transaction():
            await conn.execute(
                "UPDATE promocodes SET used_count = used_count + 1 WHERE code = $1",
                code
            )
            await conn.execute(
                "INSERT INTO used_promocodes (user_id, code) VALUES ($1, $2)",
                user_id, code
            )
            new_balance = await db.update_balance(user_id, promo['reward'])
    
    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"+{promo['reward']} LC\n"
        f"Баланс: {new_balance} LC"
    )
