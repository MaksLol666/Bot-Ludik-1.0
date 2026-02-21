import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database_sqlite import db
from handlers.status import update_user_status
from config import MIN_BET, MAX_BET

router = Router()

GRID_SIZE = 5
CELLS_COUNT = GRID_SIZE * GRID_SIZE

MULTIPLIERS = {
    1: 1.2, 2: 1.5, 3: 2.0, 4: 2.5, 5: 3.2,
    6: 4.0, 7: 5.0, 8: 6.5, 9: 8.0, 10: 10.0,
    11: 12.5, 12: 15.0, 13: 18.0, 14: 22.0,
    15: 27.0, 16: 33.0, 17: 40.0, 18: 50.0,
    19: 65.0, 20: 85.0, 21: 110.0, 22: 150.0,
    23: 200.0, 24: 300.0,
}

class MinesStates(StatesGroup):
    playing = State()

@router.message(F.text.lower().startswith("мины"))
async def start_mines(message: Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: мины [ставка]")
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
    
    db.update_balance(user_id, -bet)
    
    mines = random.sample(range(CELLS_COUNT), 5)
    
    await state.set_state(MinesStates.playing)
    await state.update_data(
        bet=bet,
        mines=mines,
        opened=[],
        game_over=False
    )
    
    await show_mines_field(message, state, user_id)

async def show_mines_field(message: Message, state: FSMContext, user_id: int, edit: bool = False):
    data = await state.get_data()
    opened = data.get('opened', [])
    mines = data.get('mines', [])
    bet = data.get('bet', 0)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_rows = []
    
    for i in range(GRID_SIZE):
        row = []
        for j in range(GRID_SIZE):
            cell_num = i * GRID_SIZE + j
            
            if cell_num in opened:
                if cell_num in mines:
                    text = "💥"
                else:
                    mine_count = count_mines_around(cell_num, mines)
                    if mine_count == 0:
                        text = "⬜"
                    else:
                        text = str(mine_count)
            else:
                text = "⬛"
            
            row.append(InlineKeyboardButton(text=text, callback_data=f"mine_{cell_num}"))
        
        keyboard_rows.append(row)
    
    if opened:
        current_mult = MULTIPLIERS.get(len(opened), 300)
        win_amount = int(bet * current_mult)
        
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"💰 ЗАБРАТЬ {win_amount} LC (x{current_mult})", 
                callback_data="mine_cashout"
            )
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(text="◀️ Выйти", callback_data="mine_exit")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    info_text = (
        f"💣 <b>Мины</b>\n\n"
        f"💰 Ставка: {bet} LC\n"
        f"🔓 Открыто клеток: {len(opened)}\n"
    )
    
    if opened:
        info_text += f"📈 Текущий множитель: x{current_mult}\n"
        info_text += f"💎 Можно забрать: {win_amount} LC"
    else:
        info_text += f"📈 Множитель за 1 клетку: x1.2"
    
    info_text += "\n\n⬛ - закрыто\n⬜ - пусто\n💥 - мина"
    
    if edit:
        await message.edit_text(info_text, reply_markup=keyboard)
    else:
        await message.answer(info_text, reply_markup=keyboard)

def count_mines_around(cell: int, mines: list) -> int:
    row = cell // GRID_SIZE
    col = cell % GRID_SIZE
    
    count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            
            nr, nc = row + dr, col + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                neighbor = nr * GRID_SIZE + nc
                if neighbor in mines:
                    count += 1
    
    return count

@router.callback_query(F.data.startswith("mine_"), MinesStates.playing)
async def open_cell(callback: CallbackQuery, state: FSMContext):
    if callback.data == "mine_cashout":
        await cashout(callback, state)
        return
    
    if callback.data == "mine_exit":
        await exit_game(callback, state)
        return
    
    try:
        cell = int(callback.data.replace("mine_", ""))
    except:
        await callback.answer()
        return
    
    data = await state.get_data()
    
    if data.get('game_over', False):
        await callback.answer("Игра окончена!", show_alert=True)
        return
    
    opened = data.get('opened', [])
    mines = data.get('mines', [])
    bet = data.get('bet', 0)
    user_id = callback.from_user.id
    
    if cell in opened:
        await callback.answer("Эта клетка уже открыта!", show_alert=True)
        return
    
    if cell in mines:
        opened.append(cell)
        await state.update_data(opened=opened, game_over=True)
        
        await show_mines_field(callback.message, state, user_id, edit=True)
        
        await callback.message.answer(
            f"💥 <b>БАХ! Ты подорвался!</b>\n\n"
            f"💰 Потеряно: {bet} LC"
        )
        
        db.add_game_stat(user_id, "mines", False, bet, 0)
        update_user_status(user_id)
        
        await state.clear()
        await callback.answer()
        return
    
    opened.append(cell)
    await state.update_data(opened=opened)
    
    await show_mines_field(callback.message, state, user_id, edit=True)
    await callback.answer()

@router.callback_query(F.data == "mine_cashout", MinesStates.playing)
async def cashout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if data.get('game_over', False):
        await callback.answer("Игра окончена!", show_alert=True)
        return
    
    opened = data.get('opened', [])
    bet = data.get('bet', 0)
    user_id = callback.from_user.id
    
    if not opened:
        await callback.answer("Сначала открой хотя бы одну клетку!", show_alert=True)
        return
    
    current_mult = MULTIPLIERS.get(len(opened), 300)
    win_amount = int(bet * current_mult)
    
    db.update_balance(user_id, win_amount)
    db.add_game_stat(user_id, "mines", True, bet, win_amount)
    update_user_status(user_id)
    
    await callback.message.edit_text(
        f"💰 <b>Ты забрал выигрыш!</b>\n\n"
        f"📊 Открыто клеток: {len(opened)}\n"
        f"📈 Множитель: x{current_mult}\n"
        f"💎 Выигрыш: +{win_amount} LC\n\n"
        f"✅ Игра завершена"
    )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "mine_exit", MinesStates.playing)
async def exit_game(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if not data.get('game_over', False) and data.get('opened'):
        bet = data.get('bet', 0)
        user_id = callback.from_user.id
        
        await callback.message.edit_text(
            f"👋 <b>Ты вышел из игры</b>\n\n"
            f"💰 Ставка {bet} LC сгорает"
        )
        
        db.add_game_stat(user_id, "mines", False, bet, 0)
        update_user_status(user_id)
    else:
        await callback.message.edit_text("👋 Игра завершена")
    
    await state.clear()
    await callback.answer()
