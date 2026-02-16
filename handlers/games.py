from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import random

from database import db
from handlers.status import update_user_status
from handlers.daily_quests import update_quest_progress
from keyboards.inline import get_casino_menu, get_back_button
from config import MIN_BET, MAX_BET

router = Router()

@router.callback_query(F.data == "casino_menu")
async def show_casino(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎰 <b>Казино Лудик</b>\n\n"
        "Выбери игру:",
        reply_markup=get_casino_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "game_roulette")
async def roulette_help(callback: CallbackQuery):
    text = (
        "🃏 <b>Рулетка</b>\n\n"
        "<b>Как играть:</b>\n"
        "Напиши в чат команду:\n"
        "<code>рул [цвет/число] [ставка]</code>\n\n"
        "<b>Примеры:</b>\n"
        "рул красное 1000\n"
        "рул черное 500\n"
        "рул 7 2000\n\n"
        "💰 <b>Коэффициенты:</b>\n"
        "Цвет (красное/черное) — x2\n"
        "Число (0-36) — x36"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

@router.callback_query(F.data == "game_slots")
async def slots_help(callback: CallbackQuery):
    text = (
        "🎰 <b>Слоты</b>\n\n"
        "<b>Как играть:</b>\n"
        "Напиши в чат команду:\n"
        "<code>слоты [ставка]</code>\n\n"
        "<b>Пример:</b>\n"
        "слоты 1000\n\n"
        "<b>Выигрышные комбинации:</b>\n"
        "🍒🍒🍒 — x3\n"
        "🍋🍋🍋 — x5\n"
        "💎💎💎 — x10\n"
        "7️⃣7️⃣7️⃣ — x20"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

@router.callback_query(F.data == "back_to_casino")
async def back_to_casino(callback: CallbackQuery):
    await show_casino(callback)

@router.message(F.text.lower().startswith("рул"))
async def process_roulette(message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Формат: рул [цвет/число] [ставка]")
        return
    
    bet_type = parts[1].lower()
    try:
        bet = int(parts[2])
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
    
    result = random.randint(0, 36)
    
    red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
    
    if result == 0:
        color = "зеленое"
    elif result in red_numbers:
        color = "красное"
    else:
        color = "черное"
    
    win = False
    win_amount = 0
    
    if bet_type.isdigit():
        if int(bet_type) == result:
            win = True
            win_amount = bet * 36
    else:
        if bet_type == "красное" and color == "красное":
            win = True
            win_amount = bet * 2
        elif bet_type == "черное" and color == "черное":
            win = True
            win_amount = bet * 2
    
    if win:
        await db.add_game_stat(user_id, "roulette", True, bet, win_amount)
        await update_user_status(user_id)
        await update_quest_progress(user_id, "roulette", 1)
        await message.answer(
            f"🎉 <b>Ты выиграл!</b>\n\n"
            f"Выпало: {result} ({color})\n"
            f"Ставка: {bet} LC\n"
            f"Выигрыш: +{win_amount} LC\n"
            f"💰 Баланс: {user['balance_lc'] - bet + win_amount} LC"
        )
    else:
        await db.add_game_stat(user_id, "roulette", False, bet, 0)
        await update_user_status(user_id)
        await update_quest_progress(user_id, "roulette", 1)
        await message.answer(
            f"💔 <b>Ты проиграл!</b>\n\n"
            f"Выпало: {result} ({color})\n"
            f"Ставка: {bet} LC\n"
            f"💰 Баланс: {user['balance_lc'] - bet} LC"
        )

@router.message(F.text.lower().startswith("слоты"))
async def process_slots(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: слоты [ставка]")
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
    
    symbols = ["🍒", "🍋", "💎", "7️⃣"]
    weights = [0.5, 0.3, 0.15, 0.05]
    
    spin = random.choices(symbols, weights=weights, k=3)
    
    win_mult = 0
    if spin[0] == spin[1] == spin[2]:
        if spin[0] == "🍒":
            win_mult = 3
        elif spin[0] == "🍋":
            win_mult = 5
        elif spin[0] == "💎":
            win_mult = 10
        elif spin[0] == "7️⃣":
            win_mult = 20
    
    if win_mult > 0:
        win_amount = bet * win_mult
        await db.add_game_stat(user_id, "slots", True, bet, win_amount)
        await update_user_status(user_id)
        await update_quest_progress(user_id, "slots", 1)
        result_text = (
            f"🎰 <b>Слоты</b>\n\n"
            f"{' '.join(spin)}\n\n"
            f"🎉 <b>Ты выиграл!</b>\n"
            f"Коэффициент: x{win_mult}\n"
            f"Выигрыш: +{win_amount} LC\n"
            f"💰 Баланс: {user['balance_lc'] - bet + win_amount} LC"
        )
    else:
        await db.add_game_stat(user_id, "slots", False, bet, 0)
        await update_user_status(user_id)
        await update_quest_progress(user_id, "slots", 1)
        result_text = (
            f"🎰 <b>Слоты</b>\n\n"
            f"{' '.join(spin)}\n\n"
            f"💔 <b>Ты проиграл!</b>\n"
            f"💰 Баланс: {user['balance_lc'] - bet} LC"
        )
    
    await message.answer(result_text)
