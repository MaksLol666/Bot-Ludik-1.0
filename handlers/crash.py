from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import random
import asyncio

from database_sqlite import db
from handlers.status import update_user_status
from handlers.glc import check_win_streak
from handlers.daily_quests import update_quest_progress
from config import MIN_BET, MAX_BET
from keyboards.inline import get_back_button

router = Router()

active_crash_games = {}
crash_multipliers = {}

class CrashGame:
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet
        self.cashout_at = None
        self.is_playing = True
        self.multiplier = 1.0

async def crash_game_loop(game_id):
    multiplier = 1.0
    while True:
        await asyncio.sleep(0.5)
        
        crash_chance = 0.01 + (multiplier * 0.005)
        if random.random() < crash_chance:
            crash_multipliers[game_id] = multiplier
            break
        
        multiplier += 0.1
        crash_multipliers[game_id] = multiplier

@router.message(F.text.lower().startswith(("краш", "crash")))
async def start_crash(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: краш [ставка]")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка должна быть числом")
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
    
    game_id = f"crash_{user_id}_{message.message_id}"
    
    game = CrashGame(user_id, bet)
    active_crash_games[game_id] = game
    
    asyncio.create_task(crash_game_loop(game_id))
    
    from keyboards.inline import get_crash_keyboard
    await message.answer(
        f"📈 <b>КРАШ</b>\n\n"
        f"💰 Ставка: {bet} LC\n"
        f"📊 Множитель: 1.00x\n\n"
        f"Забери деньги до того, как самолёт улетит!",
        reply_markup=get_crash_keyboard(game_id)
    )

@router.callback_query(F.data.startswith("crash_cashout_"))
async def crash_cashout(callback: CallbackQuery):
    game_id = callback.data.replace("crash_cashout_", "")
    
    if game_id not in active_crash_games:
        await callback.answer("❌ Игра уже закончена!", show_alert=True)
        return
    
    game = active_crash_games[game_id]
    
    if not game.is_playing:
        await callback.answer("❌ Игра уже закончена!", show_alert=True)
        return
    
    multiplier = crash_multipliers.get(game_id, 1.0)
    
    win_amount = int(game.bet * multiplier)
    
    await db.update_balance(game.user_id, win_amount)
    await db.add_game_stat(game.user_id, "crash", True, game.bet, win_amount)
    await update_user_status(game.user_id)
    await check_win_streak(game.user_id, "crash")
    
    await update_quest_progress(game.user_id, "crash_wins", 1)
    await update_quest_progress(game.user_id, "crash_bets", 1)
    await update_quest_progress(game.user_id, "total_bets", 1)
    
    game.is_playing = False
    
    await callback.message.edit_text(
        f"✅ <b>Ты забрал выигрыш!</b>\n\n"
        f"💰 Ставка: {game.bet} LC\n"
        f"📈 Множитель: x{multiplier:.2f}\n"
        f"💎 Выигрыш: +{win_amount} LC"
    )
    
    del active_crash_games[game_id]
    await callback.answer()

@router.callback_query(F.data.startswith("crash_check_"))
async def crash_check(callback: CallbackQuery):
    game_id = callback.data.replace("crash_check_", "")
    
    if game_id not in crash_multipliers:
        if game_id in active_crash_games:
            game = active_crash_games[game_id]
            if game.is_playing:
                game.is_playing = False
                await db.add_game_stat(game.user_id, "crash", False, game.bet, 0)
                await update_user_status(game.user_id)
                
                await update_quest_progress(game.user_id, "crash_bets", 1)
                await update_quest_progress(game.user_id, "total_bets", 1)
                
                await callback.message.edit_text(
                    f"💥 <b>КРАШ!</b>\n\n"
                    f"Самолёт улетел... Ты потерял {game.bet} LC"
                )
                del active_crash_games[game_id]
        await callback.answer()
        return
    
    multiplier = crash_multipliers[game_id]
    
    await callback.message.edit_text(
        f"📈 <b>КРАШ</b>\n\n"
        f"💰 Ставка: {active_crash_games[game_id].bet} LC\n"
        f"📊 Множитель: {multiplier:.2f}x\n\n"
        f"Забери деньги до того, как самолёт улетит!",
        reply_markup=callback.message.reply_markup
    )
    await callback.answer()
