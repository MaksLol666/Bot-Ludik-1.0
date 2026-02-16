from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime
import random

from database import db
from handlers.glc import add_glc
from config import BONUS_MIN, BONUS_MAX, BONUS_COOLDOWN

router = Router()

@router.callback_query(F.data == "get_bonus")
async def get_bonus(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Ты не зарегистрирован!", show_alert=True)
        return
    
    last_bonus = user.get('last_bonus')
    
    if last_bonus:
        if isinstance(last_bonus, str):
            from dateutil import parser
            last_bonus = parser.parse(last_bonus)
        
        time_diff = datetime.now() - last_bonus
        if time_diff.total_seconds() < BONUS_COOLDOWN:
            hours_left = (BONUS_COOLDOWN - time_diff.total_seconds()) / 3600
            await callback.answer(
                f"⏳ Бонус можно будет получить через {hours_left:.1f} часов",
                show_alert=True
            )
            return
    
    bonus = random.randint(BONUS_MIN, BONUS_MAX)
    glc_bonus = random.randint(5, 20)
    
    new_balance = await db.update_balance(user_id, bonus)
    await add_glc(user_id, glc_bonus, "Daily bonus")
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_bonus = NOW() WHERE user_id = $1",
            user_id
        )
    
    await callback.answer(
        f"🎁 Ты получил {bonus} LC + {glc_bonus} GLC!\n"
        f"💰 Баланс: {new_balance} LC",
        show_alert=True
    )
    
    await callback.message.edit_text(
        f"🎁 <b>Бонус получен!</b>\n\n"
        f"Ты получил: +{bonus} LC\n"
        f"💎 GLC: +{glc_bonus}\n"
        f"💰 Текущий баланс: {new_balance} LC\n\n"
        f"Следующий бонус через 5 часов.",
        reply_markup=callback.message.reply_markup
    )
