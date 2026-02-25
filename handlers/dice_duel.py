import random
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database_sqlite import db
from handlers.status import update_user_status
from handlers.subscription_check import require_subscription  # ВАЖНО: ДОБАВИТЬ ЭТОТ ИМПОРТ!
from config import MIN_BET, MAX_BET

router = Router()

# Хранилище активных дуэлей
active_duels = {}

class DuelStates(StatesGroup):
    waiting_for_opponent = State()

@router.message(F.text.lower().startswith("кости"))
@require_subscription()
async def create_duel(message: Message, state: FSMContext):
    """Создание дуэли"""
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
    user = db.get_user(user_id)
    
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
    
    # Создаем дуэль
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
    """Принятие дуэли"""
    duel_id = callback.data.replace("accept_duel_", "")
    
    if duel_id not in active_duels:
        await callback.answer("❌ Дуэль уже неактуальна", show_alert=True)
        return
    
    duel = active_duels[duel_id]
    
    if duel['status'] != 'waiting':
        await callback.answer("❌ Дуэль уже началась", show_alert=True)
        return
    
    opponent_id = callback.from_user.id
    
    # Нельзя играть с самим собой
    if opponent_id == duel['creator']:
        await callback.answer("❌ Нельзя играть с самим собой!", show_alert=True)
        return
    
    # Проверяем оппонента
    opponent = db.get_user(opponent_id)
    
    if not opponent:
        await callback.answer("❌ Ты не зарегистрирован!", show_alert=True)
        return
    
    if opponent['is_banned']:
        await callback.answer("⛔ Ты забанен!", show_alert=True)
        return
    
    if duel['bet'] > opponent['balance_lc']:
        await callback.answer(f"❌ У тебя недостаточно средств! Нужно {duel['bet']} LC", show_alert=True)
        return
    
    # Блокируем ставки у обоих
    db.update_balance(duel['creator'], -duel['bet'])
    db.update_balance(opponent_id, -duel['bet'])
    
    # Меняем статус
    duel['opponent'] = opponent_id
    duel['opponent_name'] = callback.from_user.full_name
    duel['status'] = 'playing'
    
    # Отправляем сообщение о начале дуэли
    await callback.message.edit_text(
        f"🎲 <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n\n"
        f"👤 {duel['creator_name']} VS {duel['opponent_name']}\n"
        f"💰 Банк: {duel['bet'] * 2} LC\n\n"
        f"⚡ Кидаем кости..."
    )
    
    # Кидаем кости через эмодзи
    creator_dice = await callback.bot.send_dice(callback.message.chat.id, emoji="🎲")
    opponent_dice = await callback.bot.send_dice(callback.message.chat.id, emoji="🎲")
    
    # Ждем, пока анимация закончится
    await asyncio.sleep(4)
    
    # Получаем значения
    creator_roll = creator_dice.dice.value
    opponent_roll = opponent_dice.dice.value
    
    # Определяем победителя
    if creator_roll > opponent_roll:
        winner_id = duel['creator']
        winner_name = duel['creator_name']
        win_amount = duel['bet'] * 2
        db.update_balance(winner_id, win_amount)
        db.add_game_stat(winner_id, "dice", True, duel['bet'], win_amount)
        db.add_game_stat(opponent_id, "dice", False, duel['bet'], 0)
        update_user_status(winner_id)
        update_user_status(opponent_id)
        
        result_text = f"🏆 <b>ПОБЕДИТЕЛЬ: {winner_name}</b>"
        
    elif opponent_roll > creator_roll:
        winner_id = opponent_id
        winner_name = duel['opponent_name']
        win_amount = duel['bet'] * 2
        db.update_balance(winner_id, win_amount)
        db.add_game_stat(winner_id, "dice", True, duel['bet'], win_amount)
        db.add_game_stat(duel['creator'], "dice", False, duel['bet'], 0)
        update_user_status(winner_id)
        update_user_status(duel['creator'])
        
        result_text = f"🏆 <b>ПОБЕДИТЕЛЬ: {winner_name}</b>"
        
    else:
        # Ничья - возврат ставок
        db.update_balance(duel['creator'], duel['bet'])
        db.update_balance(opponent_id, duel['bet'])
        
        await callback.message.answer(
            f"🎲 <b>НИЧЬЯ!</b>\n\n"
            f"👤 {duel['creator_name']}: {creator_roll}\n"
            f"👤 {duel['opponent_name']}: {opponent_roll}\n\n"
            f"🤝 Ставки возвращены!"
        )
        
        del active_duels[duel_id]
        await callback.answer()
        return
    
    # Отправляем результат
    result_text = (
        f"🎲 <b>ДУЭЛЬ ЗАВЕРШЕНА!</b>\n\n"
        f"👤 {duel['creator_name']}: {creator_roll}\n"
        f"👤 {duel['opponent_name']}: {opponent_roll}\n\n"
        f"{result_text}\n"
        f"💰 Выигрыш: +{win_amount} LC"
    )
    
    await callback.message.answer(result_text)
    
    # Удаляем дуэль
    del active_duels[duel_id]
    await callback.answer()

@router.callback_query(F.data == "game_dice")
async def dice_help(callback: CallbackQuery):
    """Помощь по костям"""
    text = (
        "🎲 <b>Кости (дуэль)</b>\n\n"
        "<b>Как играть:</b>\n"
        "1️⃣ Напиши <code>кости [ставка]</code>\n"
        "2️⃣ Бот создаст дуэль\n"
        "3️⃣ Другой игрок нажимает кнопку \"Принять вызов\"\n"
        "4️⃣ Бот кидает кости 🎲 для обоих игроков\n"
        "5️⃣ У кого больше очков - тот забирает банк!\n\n"
        "<b>Пример:</b>\n"
        "<code>кости 1000</code>\n\n"
        "<b>Правила:</b>\n"
        "• Побеждает тот, у кого больше очков\n"
        "• При ничьей ставки возвращаются\n"
        "• Банк = ставка × 2"
    )
    
    from keyboards.inline import get_back_button
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()
