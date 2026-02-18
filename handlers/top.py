from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from handlers.status import get_display_name
from keyboards.inline import get_back_button

router = Router()

TOP_TYPES = {
    "tb": ("💰 Топ богачей", "balance_lc"),
    "tr": ("🃏 Топ рулетки", "roulette"),
    "ts": ("🎰 Топ слотов", "slots"),
    "tk": ("🎲 Топ костей", "dice_duel"),
    "tm": ("💣 Топ мин", "mines"),
    "tp": ("♠️ Топ покера", "poker"),
    "tbj": ("🃏 Топ блэкджека", "blackjack"),
    "tc": ("📈 Топ краша", "crash"),
    "td": ("🎲 Топ dice", "dice_game"),
    "tl": ("🎟 Топ лотереи", "lottery")
}

async def get_top_balance(limit: int = 10):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, username, balance_lc FROM users ORDER BY balance_lc DESC LIMIT $1",
            limit
        )
    return rows

async def get_top_game(game: str, limit: int = 10):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.user_id, u.username, 
                   COALESCE(SUM(CASE WHEN g.win THEN g.win_amount ELSE 0 END), 0) as total_won,
                   COUNT(*) as games_played
            FROM users u
            LEFT JOIN game_stats g ON u.user_id = g.user_id AND g.game_type = $1
            WHERE u.is_banned = FALSE
            GROUP BY u.user_id, u.username
            ORDER BY total_won DESC
            LIMIT $2
        """, game, limit)
    return rows

@router.message(Command("tb", "tr", "ts", "tk", "tm", "tp", "tbj", "tc", "td", "tl"))
async def show_top(message: Message):
    cmd = message.text[1:]
    
    if cmd not in TOP_TYPES:
        text = "🏆 <b>Доступные топы:</b>\n\n"
        for key, (name, _) in TOP_TYPES.items():
            text += f"/{key} - {name}\n"
        await message.answer(text)
        return
    
    title, top_type = TOP_TYPES[cmd]
    
    if top_type == "balance_lc":
        rows = await get_top_balance(10)
        text = f"{title}\n\n"
        for i, row in enumerate(rows, 1):
            display_name = await get_display_name(row['user_id'], row['username'] or f"id{row['user_id']}")
            text += f"{i}. {display_name} — {row['balance_lc']} LC\n"
    else:
        rows = await get_top_game(top_type, 10)
        text = f"{title}\n\n"
        for i, row in enumerate(rows, 1):
            display_name = await get_display_name(row['user_id'], row['username'] or f"id{row['user_id']}")
            text += f"{i}. {display_name} — {row['total_won']} LC выиграно ({row['games_played']} игр)\n"
    
    await message.answer(text)

@router.callback_query(F.data == "top_menu")
async def top_menu(callback: CallbackQuery):
    text = "🏆 <b>Топы игроков</b>\n\n"
    for key, (name, _) in TOP_TYPES.items():
        text += f"/{key} - {name}\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()
