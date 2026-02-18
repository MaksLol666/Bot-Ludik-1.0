from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta

from database_sqlite import db
from config import ADMIN_IDS
from keyboards.inline import get_back_button

router = Router()

stats_cache = {
    'online': 0,
    'games_today': 0,
    'bets_today': 0,
    'donations_today': 0,
    'last_update': None
}

@router.message(Command("stats"))
@router.callback_query(F.data == "live_stats")
async def show_live_stats(event: Message | CallbackQuery):
    """Показать статистику в реальном времени"""
    user_id = event.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await update_stats_cache()
    
    today = datetime.now().date()
    now = datetime.now()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        active_users = await conn.fetchval("""
            SELECT COUNT(DISTINCT user_id) 
            FROM game_stats 
            WHERE created_at > NOW() - INTERVAL '15 minutes'
        """) or 0
        
        games_today = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM game_stats 
            WHERE DATE(created_at) = $1
        """, today) or 0
        
        bets_today = await conn.fetchval("""
            SELECT COALESCE(SUM(bet), 0) 
            FROM game_stats 
            WHERE DATE(created_at) = $1
        """, today) or 0
        
        new_users = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM users 
            WHERE DATE(registered_at) = $1
        """, today) or 0
        
        total_users = await conn.fetchval("""
            SELECT COUNT(*) FROM users
        """) or 0
        
        top_game = await conn.fetchrow("""
            SELECT game_type, COUNT(*) as count 
            FROM game_stats 
            WHERE created_at > NOW() - INTERVAL '1 hour'
            GROUP BY game_type 
            ORDER BY count DESC 
            LIMIT 1
        """)
    
    text = (
        f"📊 <b>СТАТИСТИКА В РЕАЛЬНОМ ВРЕМЕНИ</b>\n\n"
        f"⏰ {now.strftime('%H:%M:%S')}\n\n"
        f"<b>СЕЙЧАС:</b>\n"
        f"👥 Онлайн: {active_users} чел.\n"
        f"🎮 Популярная игра: {top_game['game_type'] if top_game else 'нет'}\n\n"
        f"<b>СЕГОДНЯ:</b>\n"
        f"📈 Игр сыграно: {games_today}\n"
        f"💰 Сделано ставок: {bets_today} LC\n"
        f"🆕 Новых игроков: {new_users}\n\n"
        f"<b>ВСЕГО:</b>\n"
        f"👤 Пользователей: {total_users}"
    )
    
    if is_admin:
        text += f"\n\n💵 Донатов сегодня: {stats_cache['donations_today']}₽"
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_back_button())
    else:
        await event.message.edit_text(text, reply_markup=get_back_button())
        await event.answer()

async def update_stats_cache():
    """Обновить кэш статистики"""
    now = datetime.now()
    
    if stats_cache['last_update'] and (now - stats_cache['last_update']).seconds < 60:
        return
    
    today = now.date()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        donations = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM donations 
            WHERE DATE(created_at) = $1
        """, today) or 0
    
    stats_cache.update({
        'donations_today': donations,
        'last_update': now
    })

async def track_donation(user_id: int, amount: int):
    """Записать донат в статистику"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO donations (user_id, amount) VALUES ($1, $2)
        """, user_id, amount)
