from aiogram import Router
from database_sqlite import db

router = Router()

STATUS_ICONS = {
    "roulette": "🃏",
    "slots": "🎰",
    "dice": "🎲",
    "mines": "💣",
    "lottery": "🎟️",
    "blackjack": "🃏",
    "rich": "💰"
}

def update_user_status(user_id: int):
    """Обновление статусов пользователя"""
    conn = db.get_connection()
    
    # Топ богачей
    cursor = conn.execute("""
        SELECT user_id FROM users 
        WHERE is_banned = 0 
        ORDER BY balance_lc DESC 
        LIMIT 1
    """)
    rich_row = cursor.fetchone()
    rich_top = rich_row[0] if rich_row else None
    
    # Топы по играм
    games = ['roulette', 'slots', 'dice', 'mines', 'lottery', 'blackjack']
    tops = {'rich': rich_top}
    
    for game in games:
        cursor = conn.execute("""
            SELECT user_id FROM game_stats 
            WHERE game_type = ?
            GROUP BY user_id
            ORDER BY SUM(win_amount) DESC 
            LIMIT 1
        """, (game,))
        row = cursor.fetchone()
        tops[game] = row[0] if row else None
    
    user_status = ""
    if tops['rich'] == user_id:
        user_status += STATUS_ICONS['rich']
    
    for game in games:
        if tops.get(game) == user_id:
            user_status += STATUS_ICONS[game]
    
    conn.execute("""
        INSERT INTO user_status (user_id, status)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET status = ?, updated_at = CURRENT_TIMESTAMP
    """, (user_id, user_status, user_status))
    conn.commit()
    
    return user_status

def get_user_status(user_id: int) -> str:
    """Получить статус пользователя"""
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT status FROM user_status WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else ""

def get_display_name(user_id: int, username: str) -> str:
    """Получить имя со статусом"""
    status = get_user_status(user_id)
    if status:
        return f"{status} @{username}"
    return f"@{username}"
