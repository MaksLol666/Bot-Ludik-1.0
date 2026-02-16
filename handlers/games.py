from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import random

from database import db
from handlers.status import update_user_status
from keyboards.inline import get_casino_menu, get_back_button  # Убрали get_roulette_keyboard
from config import MIN_BET, MAX_BET

router = Router()

# ... остальной код ...

# Словарь для временных данных игры
user_game_data = {}

# Словарь для сопоставления текста кнопки с типом ставки
BET_MAPPING = {
    "🔴 Красное": "red",
    "⚫ Чёрное": "black",
    "🟢 0": "0",
    "1-18": "1_18",
    "19-36": "19_36",
    "Чёт": "even",
    "Нечёт": "odd",
    "1-12": "1_12",
    "13-24": "13_24",
    "25-36": "25_36",
    "1 ряд": "column_1",
    "2 ряд": "column_2",
    "3 ряд": "column_3",
    "1 столбец": "street_1",
    "2 столбец": "street_2",
    "3 столбец": "street_3",
    "4 столбец": "street_4",
    "5 столбец": "street_5",
    "6 столбец": "street_6",
    "7 столбец": "street_7",
    "8 столбец": "street_8",
    "9 столбец": "street_9",
    "10 столбец": "street_10",
    "11 столбец": "street_11",
    "12 столбец": "street_12",
}

RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

# Настройки сложности
DIFFICULTY_SETTINGS = {
    "easy": {
        "name": "Легкий 🟢",
        "multiplier": 1.2,
        "win_chance": 0.6,
        "min_bet": MIN_BET,
        "max_bet": MAX_BET // 2
    },
    "normal": {
        "name": "Средний 🟡",
        "multiplier": 1.0,
        "win_chance": 0.5,
        "min_bet": MIN_BET,
        "max_bet": MAX_BET
    },
    "hard": {
        "name": "Сложный 🔴",
        "multiplier": 0.8,
        "win_chance": 0.4,
        "min_bet": MIN_BET * 2,
        "max_bet": MAX_BET * 2
    },
    "extreme": {
        "name": "Экстрим ⚡",
        "multiplier": 0.5,
        "win_chance": 0.3,
        "min_bet": MIN_BET * 5,
        "max_bet": MAX_BET * 5
    },
}

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
        "1. Нажми 'Играть в рулетку'\n"
        "2. Введи сумму ставки\n"
        "3. Выбери тип ставки\n\n"
        "<b>Коэффициенты:</b>\n"
        "• Красное/Чёрное — x2\n"
        "• Чёт/Нечёт — x2\n"
        "• 1-18 / 19-36 — x2\n"
        "• 1-12 / 13-24 / 25-36 — x3\n"
        "• Ряды (1,2,3) — x3\n"
        "• Столбцы (1-12) — x3\n"
        "• Число 0 — x36\n\n"
        f"💰 Мин. ставка: {MIN_BET} LC\n"
        f"💰 Макс. ставка: {MAX_BET} LC"
    )
    await callback.message.edit_text(text, reply_markup=get_roulette_keyboard())
    await callback.answer()

@router.callback_query(F.data == "play_roulette")
async def play_roulette(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        chat_member = await callback.bot.get_chat_member(CHANNEL_ID, user_id)
        from aiogram.enums import ChatMemberStatus
        if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            await callback.answer("❌ Ты не подписан на канал!", show_alert=True)
            return
    except:
        pass
    
    user = await db.get_user(user_id)
    if user and user['is_banned']:
        await callback.answer("⛔ Ты забанен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"💰 <b>Введи сумму ставки:</b>\n\n"
        f"Минимальная: {MIN_BET} LC\n"
        f"Максимальная: {MAX_BET} LC\n"
        f"Твой баланс: {user['balance_lc']} LC",
        reply_markup=get_back_button()
    )
    
    user_game_data[user_id] = {'state': 'waiting_bet'}
    await callback.answer()

@router.message(F.text.regexp(r'^\d+$'))
async def process_bet_amount(message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_game_data or user_game_data[user_id].get('state') != 'waiting_bet':
        return
    
    try:
        bet = int(message.text)
    except:
        await message.answer("❌ Введите число!")
        return
    
    user = await db.get_user(user_id)
    
    if bet < MIN_BET:
        await message.answer(f"❌ Минимальная ставка: {MIN_BET} LC")
        return
    
    if bet > MAX_BET:
        await message.answer(f"❌ Максимальная ставка: {MAX_BET} LC")
        return
    
    if bet > user['balance_lc']:
        await message.answer("❌ Недостаточно средств!")
        return
    
    user_game_data[user_id] = {
        'state': 'waiting_choice',
        'bet': bet
    }
    
    from keyboards.inline import get_roulette_bet_keyboard
    await message.answer(
        "🎰 <b>Выбери тип ставки:</b>",
        reply_markup=get_roulette_bet_keyboard()
    )

@router.callback_query(F.data.startswith("roulette_bet_"))
async def process_roulette_bet(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_game_data or user_game_data[user_id].get('state') != 'waiting_choice':
        await callback.answer("❌ Начни игру заново!", show_alert=True)
        await callback.message.edit_text("Начни игру заново: /play")
        return
    
    bet_type_code = callback.data.replace("roulette_bet_", "")
    
    bet_text = None
    for text, code in BET_MAPPING.items():
        if code == bet_type_code:
            bet_text = text
            break
    
    if not bet_text:
        await callback.answer("❌ Неизвестный тип ставки!")
        return
    
    bet = user_game_data[user_id]['bet']
    
    # Списываем ставку
    await db.update_balance(user_id, -bet)
    
    # Генерируем число
    number = random.randint(0, 36)
    
    # Определяем результат
    win = False
    multiplier = 1
    
    if bet_type_code == 'red':
        win = number in RED_NUMBERS
        multiplier = 2
    elif bet_type_code == 'black':
        win = number in BLACK_NUMBERS
        multiplier = 2
    elif bet_type_code == '0':
        win = (number == 0)
        multiplier = 36
    elif bet_type_code in ['1_18', '19_36']:
        if bet_type_code == '1_18':
            win = (1 <= number <= 18)
        else:
            win = (19 <= number <= 36)
        multiplier = 2
    elif bet_type_code in ['even', 'odd']:
        if number == 0:
            win = False
        else:
            if bet_type_code == 'even':
                win = (number % 2 == 0)
            else:
                win = (number % 2 == 1)
        multiplier = 2
    elif bet_type_code in ['1_12', '13_24', '25_36']:
        if bet_type_code == '1_12':
            win = (1 <= number <= 12)
        elif bet_type_code == '13_24':
            win = (13 <= number <= 24)
        else:
            win = (25 <= number <= 36)
        multiplier = 3
    elif bet_type_code.startswith('column_'):
        col = int(bet_type_code.split('_')[1])
        numbers = list(range(col, 37, 3))
        win = (number in numbers)
        multiplier = 3
    elif bet_type_code.startswith('street_'):
        street = int(bet_type_code.split('_')[1])
        start = (street - 1) * 3 + 1
        numbers = [start, start + 1, start + 2]
        win = (number in numbers)
        multiplier = 3
    
    if win:
        win_amount = bet * multiplier
        profit = win_amount - bet
        
        await db.update_balance(user_id, win_amount)
        await db.add_game_stat(user_id, "roulette", True, bet, win_amount)
        await update_user_status(user_id)
        await check_win_streak(user_id, "roulette")
        await update_quest_progress(user_id, "roulette_wins", 1)
        
        result_text = (
            f"🎉 <b>Ты выиграл!</b>\n\n"
            f"Выпало число: {number}\n"
            f"Твоя ставка: {bet} LC\n"
            f"Выигрыш: +{win_amount} LC\n"
            f"Чистый профит: +{profit} LC"
        )
    else:
        await db.add_game_stat(user_id, "roulette", False, bet, 0)
        await update_user_status(user_id)
        
        result_text = (
            f"💔 <b>Ты проиграл!</b>\n\n"
            f"Выпало число: {number}\n"
            f"Твоя ставка: {bet} LC\n"
            f"Потеряно: {bet} LC"
        )
    
    await update_quest_progress(user_id, "roulette_bets", 1)
    await update_quest_progress(user_id, "total_bets", 1)
    
    user = await db.get_user(user_id)
    result_text += f"\n\n💰 Текущий баланс: {user['balance_lc']} LC"
    
    await callback.message.answer(
        result_text,
        reply_markup=get_casino_menu()
    )
    
    del user_game_data[user_id]
    await callback.answer()

@router.callback_query(F.data == "roulette_back")
async def roulette_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_game_data:
        del user_game_data[user_id]
    
    await callback.message.edit_text(
        "🎮 Игровой зал:",
        reply_markup=get_casino_menu()
    )
    await callback.answer()

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
        await db.update_balance(user_id, win_amount)
        await db.add_game_stat(user_id, "slots", True, bet, win_amount)
        await update_user_status(user_id)
        await check_win_streak(user_id, "slots")
        await update_quest_progress(user_id, "slots_wins", 1)
        
        result_text = (
            f"🎰 <b>Слоты</b>\n\n"
            f"{' '.join(spin)}\n\n"
            f"🎉 <b>Ты выиграл!</b>\n"
            f"Коэффициент: x{win_mult}\n"
            f"Выигрыш: +{win_amount} LC"
        )
    else:
        await db.add_game_stat(user_id, "slots", False, bet, 0)
        await update_user_status(user_id)
        
        result_text = (
            f"🎰 <b>Слоты</b>\n\n"
            f"{' '.join(spin)}\n\n"
            f"💔 <b>Ты проиграл!</b>\n"
            f"Потеряно: {bet} LC"
        )
    
    await update_quest_progress(user_id, "slots_bets", 1)
    await update_quest_progress(user_id, "total_bets", 1)
    
    user = await db.get_user(user_id)
    result_text += f"\n\n💰 Текущий баланс: {user['balance_lc']} LC"
    
    await message.answer(result_text)
