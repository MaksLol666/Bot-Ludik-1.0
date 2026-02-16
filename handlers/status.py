from aiogram import Router
from database import db

router = Router()

STATUS_ICONS = {
    "roulette": "🃏",
    "slots": "🎰",
    "dice_duel": "🎲",
    "mines": "💣",
    "poker": "♠️",
    "blackjack": "🃏",
    "crash": "📈",
    "dice_game": "🎲",
    "lottery": "🎟️",
    "rich": "💰"
}

async def update_user_status(user_id: int):
    """Обновление статусов пользователя"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tops = {}
        
        rich_top = await conn.fetchrow("""
            SELECT user_id FROM users 
            WHERE is_banned = FALSE 
            ORDER BY balance_lc DESC 
            LIMIT 1
        """)
        tops['rich'] = rich_top['user_id'] if rich_top else None
        
        games = ['roulette', 'slots', 'dice_duel', 'mines', 'poker', 'blackjack', 'crash', 'dice_game', 'lottery']
        for game in games:
            game_top = await conn.fetchrow("""
                SELECT user_id FROM game_stats 
                WHERE game_type = $1 AND win = TRUE
                GROUP BY user_id
                ORDER BY SUM(win_amount) DESC 
                LIMIT 1
            """, game)
            tops[game] = game_top['user_id'] if game_top else None
        
        # Получаем статусы из инвентаря
        equipped = await conn.fetch("""
            SELECT emoji FROM user_inventory 
            WHERE user_id = $1 AND is_equipped = TRUE
            ORDER BY id
        """, user_id)
        
        inventory_status = ''.join([e['emoji'] for e in equipped])
        
        # Добавляем топ-статусы
        top_status = ""
        if tops['rich'] == user_id:
            top_status += STATUS_ICONS['rich']
        
        for game in games:
            if tops.get(game) == user_id:
                top_status += STATUS_ICONS[game]
        
        # Объединяем
        final_status = top_status + inventory_status
        
        await conn.execute("""
            INSERT INTO user_status (user_id, status)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET status = $2, updated_at = NOW()
        """, user_id, final_status)
        
        return final_status

async def get_user_status(user_id: int) -> str:
    """Получить статус пользователя"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status FROM user_status WHERE user_id = $1",
            user_id
        )
        return row['status'] if row else ""

async def get_display_name(user_id: int, username: str) -> str:
    """Получить имя со статусом"""
    status = await get_user_status(user_id)
    if status:
        return f"{status} @{username}"
    return f"@{username}"
