import asyncpg
from asyncpg import Pool
from typing import Optional, Dict, Any
import datetime

class Database:
    _pool: Optional[Pool] = None

    @classmethod
    async def connect(cls):
        cls._pool = await asyncpg.create_pool(
            "postgresql://postgres:postgres@localhost/ludik_db"
        )
        
        async with cls._pool.acquire() as conn:
            # Пользователи
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance_lc BIGINT DEFAULT 2500,
                    balance_glc BIGINT DEFAULT 0,
                    referrer_id BIGINT,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    registered_at TIMESTAMP DEFAULT NOW(),
                    last_bonus TIMESTAMP,
                    total_lost BIGINT DEFAULT 0
                )
            """)
            
            # Статистика игр
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    game_type TEXT,
                    win BOOLEAN,
                    bet BIGINT,
                    win_amount BIGINT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Промокоды
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    reward BIGINT,
                    max_uses INT,
                    used_count INT DEFAULT 0
                )
            """)
            
            # Использованные промокоды
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS used_promocodes (
                    user_id BIGINT REFERENCES users(user_id),
                    code TEXT REFERENCES promocodes(code),
                    used_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, code)
                )
            """)
            
            # Бизнес
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS business (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                    business_type TEXT,
                    last_collected TIMESTAMP
                )
            """)
            
            # Лотерея
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lottery_tickets (
                    user_id BIGINT REFERENCES users(user_id),
                    week_number TEXT,
                    ticket_count INT DEFAULT 0,
                    purchase_date TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, week_number)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lottery_results (
                    id SERIAL PRIMARY KEY,
                    week_number TEXT UNIQUE,
                    draw_date TIMESTAMP,
                    winners TEXT,
                    total_tickets INT,
                    total_amount INT
                )
            """)
            
            # Рефералы
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    referrer_id BIGINT REFERENCES users(user_id),
                    referral_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                    registered_at TIMESTAMP DEFAULT NOW(),
                    donat_amount BIGINT DEFAULT 0
                )
            """)
            
            # Статусы игроков
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_status (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                    status TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Инвентарь статусов
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_inventory (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    emoji TEXT,
                    name TEXT,
                    price INT,
                    purchased_at TIMESTAMP DEFAULT NOW(),
                    is_equipped BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Донаты для статистики
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    amount INT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Ежедневные задания
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_quests (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    quest_date DATE DEFAULT CURRENT_DATE,
                    quest_type TEXT,
                    target INT,
                    progress INT DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    reward_lc INT,
                    reward_glc INT
                )
            """)
            
            # Жалобы
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id SERIAL PRIMARY KEY,
                    complainant_id BIGINT REFERENCES users(user_id),
                    accused_id BIGINT,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    reviewed_at TIMESTAMP,
                    reviewed_by BIGINT
                )
            """)
            
            # Достижения
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    achievement_key TEXT,
                    unlocked_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS achievement_progress (
                    user_id BIGINT REFERENCES users(user_id),
                    achievement_key TEXT,
                    progress INT DEFAULT 0,
                    target INT,
                    PRIMARY KEY (user_id, achievement_key)
                )
            """)
    
    @classmethod
    async def get_pool(cls) -> Pool:
        if not cls._pool:
            await cls.connect()
        return cls._pool
    
    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
    
    @classmethod
    async def get_user(cls, user_id: int) -> Optional[Dict[str, Any]]:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None
    
    @classmethod
    async def create_user(cls, user_id: int, username: str, first_name: str, referrer_id: int = None):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO users (user_id, username, first_name, referrer_id)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO NOTHING
                """, user_id, username, first_name, referrer_id)
                
                if referrer_id:
                    await conn.execute("""
                        INSERT INTO referrals (referrer_id, referral_id)
                        VALUES ($1, $2)
                        ON CONFLICT (referral_id) DO NOTHING
                    """, referrer_id, user_id)
                    
                    await cls.update_balance(referrer_id, 1000)
                    
                    # GLC за реферала
                    await cls.update_glc(referrer_id, 100)
    
    @classmethod
    async def update_balance(cls, user_id: int, amount: int) -> int:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                UPDATE users 
                SET balance_lc = balance_lc + $1 
                WHERE user_id = $2 
                RETURNING balance_lc
            """, amount, user_id)
            return result
    
    @classmethod
    async def update_glc(cls, user_id: int, amount: int) -> int:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                UPDATE users 
                SET balance_glc = balance_glc + $1 
                WHERE user_id = $2 
                RETURNING balance_glc
            """, amount, user_id)
            return result
    
    @classmethod
    async def add_game_stat(cls, user_id: int, game: str, win: bool, bet: int, win_amount: int):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_stats (user_id, game_type, win, bet, win_amount)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, game, win, bet, win_amount)
            
            if not win:
                await conn.execute("""
                    UPDATE users SET total_lost = total_lost + $1 WHERE user_id = $2
                """, bet, user_id)

db = Database()
