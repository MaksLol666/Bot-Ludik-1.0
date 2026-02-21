from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.link import create_telegram_link  # Новый импорт для aiogram 3.x

from database_sqlite import db
from keyboards.inline import get_back_button

router = Router()

@router.callback_query(F.data == "referral_menu")
async def referral_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    bot = callback.bot
    # Создаем реферальную ссылку для aiogram 3.x
    bot_username = (await bot.me()).username
    deep_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
        (user_id,)
    )
    ref_count = cursor.fetchone()[0]
    
    cursor = conn.execute(
        "SELECT COALESCE(SUM(donat_amount), 0) FROM referrals WHERE referrer_id = ?",
        (user_id,)
    )
    total_donat = cursor.fetchone()[0]
    
    text = (
        "👥 <b>Реферальная система</b>\n\n"
        f"📊 Твоя статистика:\n"
        f"👤 Приглашено: {ref_count} чел.\n"
        f"💰 Донатов рефералов: {total_donat} ₽\n"
        f"💎 Твой бонус: {total_donat * 10} LC (10%)\n\n"
        f"🔗 Твоя ссылка:\n"
        f"<code>{deep_link}</code>\n\n"
        f"За каждого приглашенного ты получаешь 1000 LC\n"
        f"Если реферал донатит, ты получаешь 10% от его доната в LC"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

def add_referral_donat(referral_id: int, donat_amount: int):
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT referrer_id FROM users WHERE user_id = ?",
        (referral_id,)
    )
    row = cursor.fetchone()
    
    if row and row[0]:
        referrer_id = row[0]
        
        conn.execute("""
            UPDATE referrals 
            SET donat_amount = donat_amount + ? 
            WHERE referral_id = ?
        """, (donat_amount, referral_id))
        conn.commit()
        
        bonus = donat_amount * 10
        db.update_balance(referrer_id, bonus)
        
        return referrer_id, bonus
    
    return None, 0
