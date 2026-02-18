from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import random

from database_sqlite import db
from keyboards.inline import get_back_button

router = Router()

GLC_PER_REFERRAL = 100
GLC_PER_DONAT_10RUB = 10
GLC_DAILY_BONUS = random.randint(5, 50)
GLC_PER_GAME_STREAK = 50

@router.message(Command("glc"))
async def show_glc_info(message: Message):
    """Информация о GLC валюте"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    # Считаем серии побед
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        streak = await conn.fetchval("""
            SELECT COUNT(*) FROM game_stats 
            WHERE user_id = $1 AND win = TRUE
            AND created_at > NOW() - INTERVAL '24 hours'
        """, user_id) or 0
    
    text = (
        f"💰 <b>GLC — Премиальная валюта</b>\n\n"
        f"Твой баланс GLC: {user['balance_glc']} #GLC\n\n"
        f"<b>Как получить GLC:</b>\n"
        f"• 👥 За реферала: +{GLC_PER_REFERRAL} GLC\n"
        f"• 💵 За донат: +{GLC_PER_DONAT_10RUB} GLC за каждые 10₽\n"
        f"• 🔥 За серию побед (5+): +{GLC_PER_GAME_STREAK} GLC\n"
        f"• 📅 За бонус: +{GLC_DAILY_BONUS} GLC\n\n"
        f"<b>На что потратить GLC:</b>\n"
        f"• 💎 VIP статусы в /vip\n"
        f"• 🎫 Эксклюзивная лотерея (скоро)\n"
        f"• 🎁 Особые предметы (скоро)\n\n"
        f"🔥 Твоя текущая серия: {streak} побед"
    )
    
    await message.answer(text, reply_markup=get_back_button())

async def add_glc(user_id: int, amount: int, reason: str = ""):
    """Добавить GLC пользователю"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        new_balance = await conn.fetchval("""
            UPDATE users 
            SET balance_glc = balance_glc + $1 
            WHERE user_id = $2 
            RETURNING balance_glc
        """, amount, user_id)
    
    print(f"GLC: +{amount} to {user_id} | {reason}")
    
    return new_balance

async def check_win_streak(user_id: int, game: str):
    """Проверка на серию побед (5+ подряд)"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetch("""
            SELECT win FROM game_stats 
            WHERE user_id = $1 AND game_type = $2
            ORDER BY id DESC LIMIT 10
        """, user_id, game)
        
        if len(stats) >= 5:
            streak = 0
            for stat in stats:
                if stat['win']:
                    streak += 1
                else:
                    break
            
            if streak >= 5 and streak % 5 == 0:
                await add_glc(user_id, 50, f"Streak {streak} in {game}")
                return True
    return False
