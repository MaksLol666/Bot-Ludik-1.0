from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import random

from database_sqlite import db
from handlers.status import update_user_status
from config import MIN_BET, MAX_BET
from keyboards.inline import get_back_button

router = Router()

# Значения слотов из Telegram
SLOT_VALUES = {
    64: {"name": "777", "display": "7️⃣7️⃣7️⃣", "multiplier": 10, "win_name": "ДЖЕКПОТ"},
    1: {"name": "BAR", "display": "💎💎💎", "multiplier": 5, "win_name": "БАР"},
    43: {"name": "LEMON", "display": "🍋🍋🍋", "multiplier": 3, "win_name": "ЛИМОНЫ"},
    22: {"name": "CHERRY", "display": "🍒🍒🍒", "multiplier": 3, "win_name": "ВИШНИ"},
}

# Все возможные значения для симуляции
ALL_SLOT_VALUES = list(range(1, 65))

@router.message(F.text.lower().startswith(("слоты", "слот")))
async def process_slots(message: Message):
    """Обработчик слотов (текстовая команда)"""
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("❌ Формат: слоты [ставка]\nПример: слоты 1000")
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
    
    # Списываем ставку
    db.update_balance(user_id, -bet)
    
    # Отправляем сообщение о начале игры
    msg = await message.answer("🎰 <b>Слоты</b>\n\n🎰 Крутим барабаны...")
    
    # Имитируем анимацию
    await msg.edit_text("🎰 <b>Слоты</b>\n\n🎰 🎰 Крутим...")
    await msg.edit_text("🎰 <b>Слоты</b>\n\n🎰 🎰 🎰 Крутим...")
    
    # Генерируем результат
    result_value = random.choice(ALL_SLOT_VALUES)
    
    # Проверяем выигрыш
    if result_value in SLOT_VALUES:
        slot_info = SLOT_VALUES[result_value]
        win_multiplier = slot_info["multiplier"]
        win_amount = bet * win_multiplier
        
        # Начисляем выигрыш
        db.update_balance(user_id, win_amount)
        db.add_game_stat(user_id, "slots", True, bet, win_amount)
        update_user_status(user_id)
        
        result_text = (
            f"🎰 <b>СЛОТЫ - {slot_info['win_name']}!</b>\n\n"
            f"{slot_info['display']}\n\n"
            f"💰 Ставка: {bet} LC\n"
            f"📈 Коэффициент: x{win_multiplier}\n"
            f"💎 Выигрыш: +{win_amount} LC\n\n"
            f"🪙 Текущий баланс: {user['balance_lc'] - bet + win_amount} LC"
        )
    else:
        db.add_game_stat(user_id, "slots", False, bet, 0)
        update_user_status(user_id)
        
        random_display = f"{random.choice(['🍒','🍋','💎','7️⃣'])} {random.choice(['🍒','🍋','💎','7️⃣'])} {random.choice(['🍒','🍋','💎','7️⃣'])}"
        
        result_text = (
            f"🎰 <b>СЛОТЫ - ПРОИГРЫШ</b>\n\n"
            f"{random_display}\n\n"
            f"💰 Ставка: {bet} LC\n"
            f"💔 Потеряно: {bet} LC\n\n"
            f"🪙 Текущий баланс: {user['balance_lc'] - bet} LC"
        )
    
    await msg.edit_text(result_text)

@router.message(F.dice.emoji == "🎰")
async def handle_slots_dice(message: Message):
    """Обработчик реальных слотов Telegram"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user or user['is_banned']:
        return
    
    value = message.dice.value
    
    if value in SLOT_VALUES:
        slot_info = SLOT_VALUES[value]
        bet = 100  # Фиксированная ставка для дайсов
        
        if user['balance_lc'] >= bet:
            db.update_balance(user_id, -bet)
            win_amount = bet * slot_info["multiplier"]
            db.update_balance(user_id, win_amount)
            db.add_game_stat(user_id, "slots", True, bet, win_amount)
            update_user_status(user_id)
            
            await message.reply(
                f"🎰 <b>СЛОТЫ - {slot_info['win_name']}!</b>\n\n"
                f"{slot_info['display']}\n\n"
                f"💰 Ставка: {bet} LC\n"
                f"📈 Коэффициент: x{slot_info['multiplier']}\n"
                f"💎 Выигрыш: +{win_amount} LC"
            )

@router.callback_query(F.data == "game_slots")
async def slots_help(callback: CallbackQuery):
    """Помощь по слотам"""
    text = (
        "🎰 <b>Слоты</b>\n\n"
        "<b>Как играть:</b>\n"
        "Напиши команду:\n"
        "<code>слоты [ставка]</code>\n\n"
        "<b>Пример:</b>\n"
        "<code>слоты 1000</code>\n\n"
        "<b>Выигрышные комбинации:</b>\n"
        "• 7️⃣7️⃣7️⃣ — x10 (ДЖЕКПОТ)\n"
        "• 💎💎💎 — x5\n"
        "• 🍋🍋🍋 — x3\n"
        "• 🍒🍒🍒 — x3\n\n"
        "<b>Шанс выигрыша:</b> ~6%"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()
