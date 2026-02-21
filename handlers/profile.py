from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from handlers.status import get_display_name
from keyboards.inline import get_back_button

router = Router()

@router.message(Command("my"))
@router.callback_query(F.data == "my_stats")
async def show_my_stats(event: Message | CallbackQuery):
    user_id = event.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        text = "❌ Ты не зарегистрирован! Напиши /start"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.message.edit_text(text)
            await event.answer()
        return
    
    conn = db.get_connection()
    cursor = conn.execute("""
        SELECT game_type, 
               COUNT(*) as total_games,
               SUM(CASE WHEN win THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN win THEN 0 ELSE 1 END) as losses
        FROM game_stats 
        WHERE user_id = ?
        GROUP BY game_type
    """, (user_id,))
    rows = cursor.fetchall()
    
    stats_dict = {}
    for row in rows:
        stats_dict[row[0]] = {
            'wins': row[2],
            'losses': row[3],
            'total_bets': row[1]
        }
    
    def get_stat(game):
        s = stats_dict.get(game, {})
        return f"{s.get('wins', 0)}💰 / {s.get('losses', 0)}💔 / {s.get('total_bets', 0)} ставок"
    
    display_name = get_display_name(user_id, event.from_user.username or "NoUsername")
    
    text = (
        f"👤 <b>Пользователь:</b> {display_name} | ID: {user_id}\n"
        f"📈 <b>Общая статистика:</b>\n\n"
        f"🃏 Рулетка: {get_stat('roulette')}\n"
        f"🎰 Слоты: {get_stat('slots')}\n"
        f"🎲 Кости: {get_stat('dice')}\n"
        f"💣 Мины: {get_stat('mines')}\n"
        f"🎟 Лотерея: {get_stat('lottery')}\n"
        f"🃏 Блэкджек: {get_stat('blackjack')}\n\n"
        f"🪙 Баланс LC: {user['balance_lc']}\n"
        f"💰 Баланс GLC: {user['balance_glc']}\n\n"
        f"😭 Всего проиграно: {user['total_lost']} LC"
    )
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_back_button())
    else:
        await event.message.edit_text(text, reply_markup=get_back_button())
        await event.answer()
