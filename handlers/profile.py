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
    user = await db.get_user(user_id)
    
    if not user:
        text = "❌ Ты не зарегистрирован! Напиши /start"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.message.edit_text(text)
            await event.answer()
        return
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetch("""
            SELECT game_type, 
                   COUNT(*) as total,
                   SUM(CASE WHEN win THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN win THEN 0 ELSE 1 END) as losses,
                   COALESCE(SUM(bet), 0) as total_bet,
                   COALESCE(SUM(CASE WHEN win THEN win_amount ELSE 0 END), 0) as total_won
            FROM game_stats 
            WHERE user_id = $1
            GROUP BY game_type
        """, user_id)
    
    stats_dict = {s['game_type']: s for s in stats}
    
    def get_stat(game):
        s = stats_dict.get(game, {})
        return f"{s.get('wins', 0)}💰 / {s.get('losses', 0)}💔 / {s.get('total', 0)} игр"
    
    display_name = await get_display_name(user_id, event.from_user.username or "NoUsername")
    
    # Считаем общую статистику
    total_games = sum(s.get('total', 0) for s in stats_dict.values())
    total_won = sum(s.get('total_won', 0) for s in stats_dict.values())
    
    text = (
        f"👤 <b>Пользователь:</b> {display_name} | ID: {user_id}\n"
        f"📈 <b>Общая статистика:</b>\n\n"
        f"🃏 Рулетка: {get_stat('roulette')}\n"
        f"🎰 Слоты: {get_stat('slots')}\n"
        f"🎲 Кости (дуэль): {get_stat('dice_duel')}\n"
        f"💣 Мины: {get_stat('mines')}\n"
        f"♠️ Покер: {get_stat('poker')}\n"
        f"🃏 Блэкджек: {get_stat('blackjack')}\n"
        f"📈 Краш: {get_stat('crash')}\n"
        f"🎲 Dice: {get_stat('dice_game')}\n"
        f"🎟 Лотерея: {get_stat('lottery')}\n\n"
        f"🪙 Баланс LC: {user['balance_lc']}\n"
        f"💰 Баланс GLC: {user['balance_glc']}\n\n"
        f"📊 Всего игр: {total_games}\n"
        f"🏆 Всего выиграно: {total_won} LC\n"
        f"😭 Всего проиграно: {user['total_lost']} LC"
    )
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_back_button())
    else:
        await event.message.edit_text(text, reply_markup=get_back_button())
        await event.answer()
