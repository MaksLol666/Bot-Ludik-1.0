from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime
import random

from database_sqlite import db
from config import BONUS_MIN, BONUS_MAX, BONUS_COOLDOWN

router = Router()

@router.callback_query(F.data == "get_bonus")
async def get_bonus(callback: CallbackQuery):
    """Обработчик для Inline кнопки бонуса"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Ты не зарегистрирован!", show_alert=True)
        return
    
    last_bonus = user.get('last_bonus')
    
    if last_bonus:
        last = datetime.strptime(last_bonus, '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - last
        if time_diff.total_seconds() < BONUS_COOLDOWN:
            hours_left = (BONUS_COOLDOWN - time_diff.total_seconds()) / 3600
            await callback.answer(
                f"⏳ Бонус можно будет получить через {hours_left:.1f} часов",
                show_alert=True
            )
            return
    
    bonus = random.randint(BONUS_MIN, BONUS_MAX)
    
    new_balance = db.update_balance(user_id, bonus)
    
    conn = db.get_connection()
    conn.execute(
        "UPDATE users SET last_bonus = datetime('now') WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    
    # Добавляем GLC (шанс 30%)
    if random.random() < 0.3:
        glc_bonus = random.randint(5, 20)
        from handlers.glc import add_glc
        add_glc(user_id, glc_bonus, "daily_bonus")
        glc_text = f"\n💰 GLC: +{glc_bonus}"
    else:
        glc_text = ""
    
    await callback.answer(
        f"🎁 Ты получил {bonus} LC!{glc_text}",
        show_alert=True
    )
    
    await callback.message.edit_text(
        f"🎁 <b>Бонус получен!</b>\n\n"
        f"Ты получил: +{bonus} LC{glc_text}\n"
        f"💰 Текущий баланс: {new_balance} LC\n\n"
        f"Следующий бонус через 5 часов.",
        reply_markup=callback.message.reply_markup
    )

async def get_bonus_reply(message: Message):
    """Обработчик для Reply кнопки бонуса (для ЛС)"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован!")
        return
    
    last_bonus = user.get('last_bonus')
    
    if last_bonus:
        last = datetime.strptime(last_bonus, '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - last
        if time_diff.total_seconds() < BONUS_COOLDOWN:
            hours_left = (BONUS_COOLDOWN - time_diff.total_seconds()) / 3600
            await message.answer(
                f"⏳ Бонус можно будет получить через {hours_left:.1f} часов"
            )
            return
    
    bonus = random.randint(BONUS_MIN, BONUS_MAX)
    
    new_balance = db.update_balance(user_id, bonus)
    
    conn = db.get_connection()
    conn.execute(
        "UPDATE users SET last_bonus = datetime('now') WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    
    # Добавляем GLC (шанс 30%)
    if random.random() < 0.3:
        glc_bonus = random.randint(5, 20)
        from handlers.glc import add_glc
        add_glc(user_id, glc_bonus, "daily_bonus")
        glc_text = f"\n💰 GLC: +{glc_bonus}"
    else:
        glc_text = ""
    
    from keyboards.reply import get_main_menu_keyboard
    
    await message.answer(
        f"🎁 <b>Бонус получен!</b>\n\n"
        f"Ты получил: +{bonus} LC{glc_text}\n"
        f"💰 Текущий баланс: {new_balance} LC\n\n"
        f"Следующий бонус через 5 часов.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(F.text == "🎁 Бонус")
async def bonus_message_handler(message: Message):
    """Обработчик текстовой команды '🎁 Бонус'"""
    await get_bonus_reply(message)
