from aiogram import Router, F
from aiogram.types import Message
import random

from database import db
from handlers.status import update_user_status
from handlers.glc import check_win_streak
from handlers.daily_quests import update_quest_progress
from config import MIN_BET, MAX_BET

router = Router()

@router.message(F.text.lower().startswith(("дайс", "dice")))
async def start_dice(message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Формат: дайс [число] [ставка]\nНапример: дайс 50 1000")
        return
    
    try:
        target = int(parts[1])
        bet = int(parts[2])
    except:
        await message.answer("❌ Число и ставка должны быть числами")
        return
    
    if target < 1 or target > 100:
        await message.answer("❌ Число должно быть от 1 до 100")
        return
    
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован! Напиши /start")
        return
    
    if user['is_banned']:
        await message.answer("⛔ Ты забанен!")
        return
    
    if bet < MIN_BET:
        await message.answer(f"❌ Минимальная ставка: {MIN_BET} LC")
        return
    
    if bet > user['balance_lc']:
        await message.answer("❌ Недостаточно средств!")
        return
    
    await db.update_balance(user_id, -bet)
    
    roll = random.randint(1, 100)
    
    if roll <= target:
        multiplier = 100 / target
        win_amount = int(bet * multiplier)
        
        await db.update_balance(user_id, win_amount)
        await db.add_game_stat(user_id, "dice_game", True, bet, win_amount)
        await update_user_status(user_id)
        await check_win_streak(user_id, "dice_game")
        
        await update_quest_progress(user_id, "dice_game_wins", 1)
        
        result_text = (
            f"🎲 <b>DICE - ВЫИГРЫШ!</b>\n\n"
            f"🎯 Твоё число: {target}\n"
            f"🎲 Выпало: {roll}\n"
            f"📈 Множитель: x{multiplier:.2f}\n"
            f"💰 Выигрыш: +{win_amount} LC"
        )
    else:
        await db.add_game_stat(user_id, "dice_game", False, bet, 0)
        await update_user_status(user_id)
        
        result_text = (
            f"🎲 <b>DICE - ПРОИГРЫШ</b>\n\n"
            f"🎯 Твоё число: {target}\n"
            f"🎲 Выпало: {roll}\n"
            f"💔 Ты потерял {bet} LC"
        )
    
    await update_quest_progress(user_id, "dice_game_bets", 1)
    await update_quest_progress(user_id, "total_bets", 1)
    
    user = await db.get_user(user_id)
    result_text += f"\n\n💰 Текущий баланс: {user['balance_lc']} LC"
    
    await message.answer(result_text)
