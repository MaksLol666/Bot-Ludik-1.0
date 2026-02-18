import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database_sqlite import db
from handlers.status import update_user_status
from handlers.daily_quests import update_quest_progress
from config import MIN_BET, MAX_BET

router = Router()

active_duels = {}

class DuelStates(StatesGroup):
    waiting_for_opponent = State()

@router.message(F.text.lower().startswith("кости"))
async def create_duel(message: Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: кости [ставка]")
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
    
    if bet > MAX_BET:
        await message.answer(f"❌ Максимальная ставка: {MAX_BET} LC")
        return
    
    duel_id = f"{user_id}_{message.message_id}"
    
    active_duels[duel_id] = {
        'creator': user_id,
        'creator_name': message.from_user.full_name,
        'bet': bet,
        'status': 'waiting',
        'message_id': message.message_id,
        'chat_id': message.chat.id
    }
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Принять вызов", callback_data=f"accept_duel_{duel_id}")]
    ])
    
    await message.answer(
        f"🎲 <b>Дуэль создана!</b>\n\n"
        f"👤 Игрок: {message.from_user.full_name}\n"
        f"💰 Ставка: {bet} LC\n\n"
        f"⚔️ Ждем противника...",
        reply_markup=keyboard
    )
    
    await state.update_data(duel_id=duel_id, bet=bet)
    await state.set_state(DuelStates.waiting_for_opponent)

@router.callback_query(F.data.startswith("accept_duel_"))
async def accept_duel(callback: CallbackQuery, state: FSMContext):
    duel_id = callback.data.replace("accept_duel_", "")
    
    if duel_id not in active_duels:
        await callback.answer("❌ Дуэль уже неактуальна", show_alert=True)
        return
    
    duel = active_duels[duel_id]
    
    if duel['status'] != 'waiting':
        await callback.answer("❌ Дуэль уже началась", show_alert=True)
        return
    
    opponent_id = callback.from_user.id
    
    if opponent_id == duel['creator']:
        await callback.answer("❌ Нельзя играть с самим собой!", show_alert=True)
        return
    
    opponent = await db.get_user(opponent_id)
    
    if not opponent:
        await callback.answer("❌ Ты не зарегистрирован!", show_alert=True)
        return
    
    if opponent['is_banned']:
        await callback.answer("⛔ Ты забанен!", show_alert=True)
        return
    
    if duel['bet'] > opponent['balance_lc']:
        await callback.answer(f"❌ У тебя недостаточно средств! Нужно {duel['bet']} LC", show_alert=True)
        return
    
    await db.update_balance(duel['creator'], -duel['bet'])
    await db.update_balance(opponent_id, -duel['bet'])
    
    duel['opponent'] = opponent_id
    duel['opponent_name'] = callback.from_user.full_name
    duel['status'] = 'playing'
    
    creator_roll = random.randint(1, 6) + random.randint(1, 6)
    opponent_roll = random.randint(1, 6) + random.randint(1, 6)
    
    if creator_roll > opponent_roll:
        winner_id = duel['creator']
        winner_name = duel['creator_name']
        win_amount = duel['bet'] * 2
        await db.update_balance(winner_id, win_amount)
        await db.add_game_stat(winner_id, "dice", True, duel['bet'], win_amount)
        await db.add_game_stat(opponent_id, "dice", False, duel['bet'], 0)
        await update_user_status(winner_id)
        await update_user_status(opponent_id)
        await update_quest_progress(winner_id, "dice", 1)
        await update_quest_progress(opponent_id, "dice", 1)
    elif opponent_roll > creator_roll:
        winner_id = opponent_id
        winner_name = duel['opponent_name']
        win_amount = duel['bet'] * 2
        await db.update_balance(winner_id, win_amount)
        await db.add_game_stat(winner_id, "dice", True, duel['bet'], win_amount)
        await db.add_game_stat(duel['creator'], "dice", False, duel['bet'], 0)
        await update_user_status(winner_id)
        await update_user_status(duel['creator'])
        await update_quest_progress(winner_id, "dice", 1)
        await update_quest_progress(duel['creator'], "dice", 1)
    else:
        await db.update_balance(duel['creator'], duel['bet'])
        await db.update_balance(opponent_id, duel['bet'])
        
        await callback.message.edit_text(
            f"🎲 <b>НИЧЬЯ!</b>\n\n"
            f"👤 {duel['creator_name']}: {creator_roll}\n"
            f"👤 {duel['opponent_name']}: {opponent_roll}\n\n"
            f"🤝 Ставки возвращены!"
        )
        
        del active_duels[duel_id]
        await callback.answer()
        return
    
    result_text = (
        f"🎲 <b>ДУЭЛЬ ЗАВЕРШЕНА!</b>\n\n"
        f"👤 {duel['creator_name']}: {creator_roll}\n"
        f"👤 {duel['opponent_name']}: {opponent_roll}\n\n"
        f"🏆 <b>ПОБЕДИТЕЛЬ: {winner_name}</b>\n"
        f"💰 Выигрыш: +{win_amount} LC"
    )
    
    await callback.message.edit_text(result_text)
    
    del active_duels[duel_id]
    await callback.answer()
