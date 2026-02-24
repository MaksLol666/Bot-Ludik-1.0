from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from handlers.status import get_display_name
from keyboards.inline import get_back_button, get_top_keyboard

router = Router()

TOP_TYPES = {
    "tb": ("💰 Топ богачей", "balance_lc"),
    "tr": ("🃏 Топ рулетки", "roulette"),
    "ts": ("🎰 Топ слотов", "slots"),
    "tk": ("🎲 Топ костей", "dice"),
    "tm": ("💣 Топ мин", "mines"),
    "tl": ("🎟 Топ лотереи", "lottery"),
    "tbj": ("🃏 Топ блэкджека", "blackjack")
}

async def get_top_balance(limit: int = 10):
    """Топ по балансу"""
    conn = db.get_connection()
    cursor = conn.execute("""
        SELECT user_id, username, balance_lc 
        FROM users 
        WHERE is_banned = 0 
        ORDER BY balance_lc DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    return rows

async def get_top_game(game: str, limit: int = 10):
    """Топ по конкретной игре"""
    conn = db.get_connection()
    cursor = conn.execute("""
        SELECT u.user_id, u.username, 
               COALESCE(SUM(CASE WHEN g.win THEN 1 ELSE 0 END), 0) as wins,
               COALESCE(SUM(g.win_amount), 0) as total_won
        FROM users u
        LEFT JOIN game_stats g ON u.user_id = g.user_id AND g.game_type = ?
        WHERE u.is_banned = 0
        GROUP BY u.user_id
        ORDER BY total_won DESC, wins DESC
        LIMIT ?
    """, (game, limit))
    rows = cursor.fetchall()
    return rows

@router.message(Command("tb", "tr", "ts", "tk", "tm", "tl", "tbj"))
async def show_top(message: Message):
    """Показать топ по команде"""
    cmd = message.text[1:]
    
    if cmd not in TOP_TYPES:
        await message.answer(
            "🏆 <b>Доступные топы:</b>\n\n"
            "/tb - топ богачей 💰\n"
            "/tr - топ рулетки 🃏\n"
            "/ts - топ слотов 🎰\n"
            "/tk - топ костей 🎲\n"
            "/tm - топ мин 💣\n"
            "/tl - топ лотереи 🎟️\n"
            "/tbj - топ блэкджека 🃏"
        )
        return
    
    title, top_type = TOP_TYPES[cmd]
    
    if top_type == "balance_lc":
        rows = await get_top_balance(10)
        text = f"{title}\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[2]} LC\n"
    else:
        rows = await get_top_game(top_type, 10)
        text = f"{title}\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    
    await message.answer(text)

@router.callback_query(F.data == "top_menu")
async def top_menu(callback: CallbackQuery):
    """Меню выбора топа"""
    text = (
        "🏆 <b>Топы игроков</b>\n\n"
        "Выбери категорию:"
    )
    await callback.message.edit_text(text, reply_markup=get_top_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("top_"))
async def top_category_callback(callback: CallbackQuery):
    """Обработка выбора категории топа"""
    top_type = callback.data.replace("top_", "")
    
    if top_type == "balance":
        rows = await get_top_balance(10)
        text = "💰 <b>Топ богачей</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[2]} LC\n"
    elif top_type == "roulette":
        rows = await get_top_game("roulette", 10)
        text = "🃏 <b>Топ рулетки</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif top_type == "slots":
        rows = await get_top_game("slots", 10)
        text = "🎰 <b>Топ слотов</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif top_type == "dice":
        rows = await get_top_game("dice", 10)
        text = "🎲 <b>Топ костей</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif top_type == "mines":
        rows = await get_top_game("mines", 10)
        text = "💣 <b>Топ мин</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif top_type == "lottery":
        rows = await get_top_game("lottery", 10)
        text = "🎟 <b>Топ лотереи</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif top_type == "blackjack":
        rows = await get_top_game("blackjack", 10)
        text = "🃏 <b>Топ блэкджека</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    else:
        await callback.message.answer("❌ Неизвестный топ")
        await callback.answer()
        return
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

async def show_top_command(message: Message, cmd: str):
    """Показать конкретный топ (для инлайн кнопок)"""
    if cmd == "tb":
        rows = await get_top_balance(10)
        text = "💰 <b>Топ богачей</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[2]} LC\n"
    elif cmd == "tr":
        rows = await get_top_game("roulette", 10)
        text = "🃏 <b>Топ рулетки</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "ts":
        rows = await get_top_game("slots", 10)
        text = "🎰 <b>Топ слотов</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tk":
        rows = await get_top_game("dice", 10)
        text = "🎲 <b>Топ костей</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tm":
        rows = await get_top_game("mines", 10)
        text = "💣 <b>Топ мин</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tl":
        rows = await get_top_game("lottery", 10)
        text = "🎟 <b>Топ лотереи</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tbj":
        rows = await get_top_game("blackjack", 10)
        text = "🃏 <b>Топ блэкджека</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    else:
        await message.answer("❌ Неизвестный топ")
        return
    
    await message.edit_text(text, reply_markup=get_back_button())

# ===== ФУНКЦИИ ДЛЯ REPLY КНОПОК =====

async def top_menu_reply(message: Message):
    """Меню выбора топа для Reply кнопки"""
    from keyboards.reply import get_top_reply_keyboard
    await message.answer("🏆 <b>Выбери категорию топов:</b>", reply_markup=get_top_reply_keyboard())

async def show_top_reply(message: Message, cmd: str):
    """Показать конкретный топ для Reply кнопки"""
    if cmd == "tb":
        rows = await get_top_balance(10)
        text = "💰 <b>Топ богачей</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[2]} LC\n"
    elif cmd == "tr":
        rows = await get_top_game("roulette", 10)
        text = "🃏 <b>Топ рулетки</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "ts":
        rows = await get_top_game("slots", 10)
        text = "🎰 <b>Топ слотов</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tk":
        rows = await get_top_game("dice", 10)
        text = "🎲 <b>Топ костей</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tm":
        rows = await get_top_game("mines", 10)
        text = "💣 <b>Топ мин</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tl":
        rows = await get_top_game("lottery", 10)
        text = "🎟 <b>Топ лотереи</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    elif cmd == "tbj":
        rows = await get_top_game("blackjack", 10)
        text = "🃏 <b>Топ блэкджека</b>\n\n"
        for i, row in enumerate(rows, 1):
            display_name = get_display_name(row[0], row[1] or f"id{row[0]}")
            text += f"{i}. {display_name} — {row[3]} LC выиграно\n"
    else:
        await message.answer("❌ Неизвестный топ")
        return
    
    from keyboards.reply import get_top_reply_keyboard
    await message.answer(text, reply_markup=get_top_reply_keyboard())
