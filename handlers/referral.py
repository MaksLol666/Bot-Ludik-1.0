from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.deep_link import create_start_link

from database import db
from handlers.glc import add_glc
from handlers.achievements import check_achievement
from keyboards.inline import get_back_button

router = Router()

@router.callback_query(F.data == "referral_menu")
async def referral_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    bot = callback.bot
    deep_link = await create_start_link(bot, f"ref_{user_id}", encode=True)
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        ref_count = await conn.fetchval(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = $1",
            user_id
        ) or 0
        
        total_donat = await conn.fetchval(
            "SELECT SUM(donat_amount) FROM referrals WHERE referrer_id = $1",
            user_id
        ) or 0
    
    text = (
        "👥 <b>Реферальная система</b>\n\n"
        f"📊 Твоя статистика:\n"
        f"👤 Приглашено: {ref_count} чел.\n"
        f"💰 Донатов рефералов: {total_donat} ₽\n"
        f"💎 Твой бонус: {total_donat * 10} LC + {ref_count * 100} GLC\n\n"
        f"🔗 Твоя ссылка:\n"
        f"<code>{deep_link}</code>\n\n"
        f"За каждого приглашенного ты получаешь 1000 LC и 100 GLC\n"
        f"Если реферал донатит, ты получаешь 10% от его доната в LC"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

async def add_referral_donat(referral_id: int, donat_amount: int):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        ref = await conn.fetchrow(
            "SELECT referrer_id FROM users WHERE user_id = $1",
            referral_id
        )
        
        if ref and ref['referrer_id']:
            referrer_id = ref['referrer_id']
            
            await conn.execute("""
                UPDATE referrals 
                SET donat_amount = donat_amount + $1 
                WHERE referral_id = $2
            """, donat_amount, referral_id)
            
            bonus = donat_amount * 10
            await db.update_balance(referrer_id, bonus)
            
            # Проверяем достижение популярности
            ref_count = await conn.fetchval(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = $1",
                referrer_id
            ) or 0
            
            from handlers.achievements import check_achievement
            await check_achievement(referrer_id, "popular", ref_count)
            
            return referrer_id, bonus
    
    return None, 0
