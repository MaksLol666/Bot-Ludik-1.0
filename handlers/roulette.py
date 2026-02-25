from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import random

from database_sqlite import db
from handlers.status import update_user_status
from handlers.subscription_check import require_subscription  # ДОБАВИТЬ ЭТОТ ИМПОРТ!
from config import MIN_BET, MAX_BET
from keyboards.inline import get_back_button

router = Router()

# Цвета
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
GREEN_NUMBERS = [0]

# Ряды
ROW1 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
ROW2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
ROW3 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]

# Столбцы (по 3 числа)
COLUMNS = {
    1: [1, 2, 3],
    2: [4, 5, 6],
    3: [7, 8, 9],
    4: [10, 11, 12],
    5: [13, 14, 15],
    6: [16, 17, 18],
    7: [19, 20, 21],
    8: [22, 23, 24],
    9: [25, 26, 27],
    10: [28, 29, 30],
    11: [31, 32, 33],
    12: [34, 35, 36]
}

# Диапазоны
RANGE1_12 = list(range(1, 13))
RANGE13_24 = list(range(13, 25))
RANGE25_36 = list(range(25, 37))
RANGE1_18 = list(range(1, 19))
RANGE19_36 = list(range(19, 37))

# Четные/нечетные
EVEN = [x for x in range(1, 37) if x % 2 == 0]
ODD = [x for x in range(1, 37) if x % 2 != 0]

# Коэффициенты
MULTIPLIERS = {
    "color": 2,           # 🔴/⚫ - x2
    "green": 36,          # 🟢 - x36
    "row": 3,             # Ряд1/Ряд2/Ряд3 - x3
    "range_12": 3,        # 1-12/13-24/25-36 - x3
    "range_18": 2,        # 1-18/19-36 - x2
    "even_odd": 2,        # Чёт/Нечёт - x2
    "column": 12,         # Любой столбец (от 1 до 12) - x12
    "number": 36          # Конкретное число - x36
}

def check_win(bet_type: str, bet_value, result: int) -> tuple[bool, float]:
    """Проверка выигрыша и возврат коэффициента"""
    
    # Зеленое (0)
    if bet_type == "зеленое" or bet_type == "0":
        return result == 0, MULTIPLIERS["green"]
    
    # Конкретное число
    if bet_type.isdigit():
        return int(bet_type) == result, MULTIPLIERS["number"]
    
    # Цвет
    if bet_type == "красное":
        return result in RED_NUMBERS, MULTIPLIERS["color"]
    if bet_type == "черное":
        return result in BLACK_NUMBERS, MULTIPLIERS["color"]
    
    # Ряды
    if bet_type == "ряд1":
        return result in ROW1, MULTIPLIERS["row"]
    if bet_type == "ряд2":
        return result in ROW2, MULTIPLIERS["row"]
    if bet_type == "ряд3":
        return result in ROW3, MULTIPLIERS["row"]
    
    # Диапазоны 1-12, 13-24, 25-36
    if bet_type == "1-12":
        return result in RANGE1_12, MULTIPLIERS["range_12"]
    if bet_type == "13-24":
        return result in RANGE13_24, MULTIPLIERS["range_12"]
    if bet_type == "25-36":
        return result in RANGE25_36, MULTIPLIERS["range_12"]
    
    # Малые/большие
    if bet_type in ["мал", "малые", "1-18"]:
        return result in RANGE1_18, MULTIPLIERS["range_18"]
    if bet_type in ["бол", "большие", "19-36"]:
        return result in RANGE19_36, MULTIPLIERS["range_18"]
    
    # Чет/нечет
    if bet_type in ["чёт", "чет", "чётное", "четное"]:
        return result in EVEN, MULTIPLIERS["even_odd"]
    if bet_type in ["нечёт", "нечет", "нечётное", "нечетное"]:
        return result in ODD, MULTIPLIERS["even_odd"]
    
    # Столбцы (1-12)
    if bet_type.startswith("столбец"):
        try:
            col_num = int(bet_type.replace("столбец", ""))
            if 1 <= col_num <= 12:
                return result in COLUMNS[col_num], MULTIPLIERS["column"]
        except:
            pass
    
    return False, 0

def get_result_info(result: int) -> dict:
    """Получить информацию о выпавшем числе"""
    info = {
        "number": result,
        "color": "зеленое" if result == 0 else ("красное" if result in RED_NUMBERS else "черное"),
        "row": None,
        "range_12": None,
        "range_18": None,
        "even_odd": None
    }
    
    if result != 0:
        # Ряд
        if result in ROW1:
            info["row"] = "ряд1"
        elif result in ROW2:
            info["row"] = "ряд2"
        elif result in ROW3:
            info["row"] = "ряд3"
        
        # Диапазон
        if result in RANGE1_12:
            info["range_12"] = "1-12"
        elif result in RANGE13_24:
            info["range_12"] = "13-24"
        elif result in RANGE25_36:
            info["range_12"] = "25-36"
        
        # Малые/большие
        if result in RANGE1_18:
            info["range_18"] = "1-18"
        else:
            info["range_18"] = "19-36"
        
        # Чет/нечет
        info["even_odd"] = "чётное" if result % 2 == 0 else "нечётное"
    
    return info

@router.message(F.text.lower().startswith(("рул", "рулетка")))
@require_subscription()
async def process_roulette(message: Message):
    """Обработчик рулетки"""
    # Парсим сообщение
    text = message.text.lower()
    parts = text.split()
    
    if len(parts) < 3:
        await message.answer(
            "❌ <b>Неправильный формат</b>\n\n"
            "Примеры ставок:\n"
            "• <code>рул красное 1000</code>\n"
            "• <code>рул черное 500</code>\n"
            "• <code>рул 7 2000</code>\n"
            "• <code>рул ряд1 1000</code>\n"
            "• <code>рул 1-12 500</code>\n"
            "• <code>рул малые 1000</code>\n"
            "• <code>рул чёт 500</code>\n"
            "• <code>рул столбец5 1000</code>"
        )
        return
    
    bet_type = parts[1]
    try:
        bet = int(parts[2])
    except:
        await message.answer("❌ Сумма ставки должна быть числом")
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
    
    # Списываем ставку
    db.update_balance(user_id, -bet)
    
    # Генерируем результат
    result = random.randint(0, 36)
    result_info = get_result_info(result)
    
    # Проверяем выигрыш
    win, multiplier = check_win(bet_type, None, result)
    
    if win:
        win_amount = int(bet * multiplier)
        db.update_balance(user_id, win_amount)
        db.add_game_stat(user_id, "roulette", True, bet, win_amount)
        update_user_status(user_id)
        
        # Формируем сообщение о выигрыше
        text = (
            f"🎉 <b>Ты выиграл в рулетке!</b>\n\n"
            f"🎲 Выпало число: <b>{result}</b> ({result_info['color']})\n\n"
            f"📊 Информация:\n"
            f"• Ряд: {result_info['row'] or '-'}\n"
            f"• Диапазон: {result_info['range_12'] or '-'}\n"
            f"• {result_info['range_18'] or '-'}\n"
            f"• Число {result_info['even_odd'] or '-'}\n\n"
            f"💰 Твоя ставка: {bet} LC\n"
            f"📈 Коэффициент: x{multiplier}\n"
            f"💎 Выигрыш: +{win_amount} LC\n\n"
            f"🪙 Текущий баланс: {user['balance_lc'] - bet + win_amount} LC"
        )
    else:
        db.add_game_stat(user_id, "roulette", False, bet, 0)
        update_user_status(user_id)
        
        text = (
            f"💔 <b>Ты проиграл в рулетке</b>\n\n"
            f"🎲 Выпало число: <b>{result}</b> ({result_info['color']})\n\n"
            f"💰 Потеряно: {bet} LC\n"
            f"🪙 Текущий баланс: {user['balance_lc'] - bet} LC"
        )
    
    await message.answer(text)

@router.callback_query(F.data == "game_roulette")
async def roulette_help(callback: CallbackQuery):
    """Помощь по рулетке"""
    text = (
        "🃏 <b>Рулетка</b>\n\n"
        "<b>Доступные ставки:</b>\n\n"
        "🎨 <b>Цвета:</b>\n"
        "• <code>красное</code> - x2\n"
        "• <code>черное</code> - x2\n"
        "• <code>зеленое</code> (0) - x36\n\n"
        
        "📊 <b>Ряды:</b>\n"
        "• <code>ряд1</code> - x3\n"
        "• <code>ряд2</code> - x3\n"
        "• <code>ряд3</code> - x3\n\n"
        
        "🔢 <b>Диапазоны:</b>\n"
        "• <code>1-12</code> - x3\n"
        "• <code>13-24</code> - x3\n"
        "• <code>25-36</code> - x3\n"
        "• <code>1-18</code> (малые) - x2\n"
        "• <code>19-36</code> (большие) - x2\n\n"
        
        "➕ <b>Четность:</b>\n"
        "• <code>чёт</code> / <code>чётное</code> - x2\n"
        "• <code>нечёт</code> / <code>нечётное</code> - x2\n\n"
        
        "📐 <b>Столбцы (1-12):</b>\n"
        "• <code>столбец1</code> ... <code>столбец12</code> - x12\n"
        "• Каждый столбец содержит 3 числа\n\n"
        
        "🎯 <b>Конкретное число:</b>\n"
        "• <code>0-36</code> - x36\n\n"
        
        "<b>Примеры:</b>\n"
        "<code>рул красное 1000</code>\n"
        "<code>рул ряд2 500</code>\n"
        "<code>рул 1-12 1000</code>\n"
        "<code>рул столбец5 500</code>\n"
        "<code>рул 7 2000</code>"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()
