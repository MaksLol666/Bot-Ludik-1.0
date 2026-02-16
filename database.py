import os
import asyncpg
from asyncpg import Pool
from typing import Optional, Dict, Any
import datetime

class Database:
    _pool: Optional[Pool] = None

    @classmethod
    async def connect(cls):
        """Подключение к БД с поддержкой Docker"""
        # Берем URL из переменных окружения
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ludik_db")
        
        cls._pool = await asyncpg.create_pool(database_url)
        
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
                    wins INT DEFAULT 0,
                    losses INT DEFAULT 0,
                    total_bets INT DEFAULT 0,
                    total_won BIGINT DEFAULT 0,
                    total_lost BIGINT DEFAULT 0,
                    win BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Индексы для быстрого поиска
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_stats_user_id ON game_stats(user_id);
                CREATE INDEX IF NOT EXISTS idx_game_stats_game_type ON game_stats(game_type);
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
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    week_number TEXT,
                    ticket_count INT DEFAULT 0,
                    purchase_date TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, week_number)
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
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT REFERENCES users(user_id),
                    referral_id BIGINT UNIQUE REFERENCES users(user_id),
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
            
            print("✅ Все таблицы успешно созданы!")
    
    @classmethod
    async def get_pool(cls) -> Pool:
        """Получить пул соединений"""
        if not cls._pool:
            await cls.connect()
        return cls._pool
    
    @classmethod
    async def close(cls):
        """Закрыть соединение"""
        if cls._pool:
            await cls._pool.close()
            print("🔌 Соединение с БД закрыто")
    
    @classmethod
    async def get_user(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по ID"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None
    
    @classmethod
    async def create_user(cls, user_id: int, username: str, first_name: str, referrer_id: int = None):
        """Создать нового пользователя"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Создаем пользователя
                await conn.execute("""
                    INSERT INTO users (user_id, username, first_name, referrer_id)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO NOTHING
                """, user_id, username, first_name, referrer_id)
                
                # Если есть реферер, записываем в таблицу рефералов и даем бонус
                if referrer_id:
                    await conn.execute("""
                        INSERT INTO referrals (referrer_id, referral_id)
                        VALUES ($1, $2)
                        ON CONFLICT (referral_id) DO NOTHING
                    """, referrer_id, user_id)
                    
                    # Бонус рефереру: 1000 LC + 100 GLC
                    await cls.update_balance(referrer_id, 1000)
                    await cls.update_glc(referrer_id, 100)
    
    @classmethod
    async def update_balance(cls, user_id: int, amount: int) -> int:
        """Обновить LC баланс"""
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
        """Обновить GLC баланс"""
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
        """Добавить статистику игры"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Добавляем запись в статистику
                await conn.execute("""
                    INSERT INTO game_stats (user_id, game_type, win, wins, losses, total_bets, total_won, total_lost)
                    VALUES ($1, $2, $3, 
                            CASE WHEN $3 THEN 1 ELSE 0 END,
                            CASE WHEN $3 THEN 0 ELSE 1 END,
                            1,
                            CASE WHEN $3 THEN $5 ELSE 0 END,
                            CASE WHEN $3 THEN 0 ELSE $4 END)
                """, user_id, game, win, bet, win_amount)
                
                # Обновляем агрегированную статистику
                if win:
                    await conn.execute("""
                        INSERT INTO game_stats_agg (user_id, game_type, wins, total_bets, total_won)
                        VALUES ($1, $2, 1, 1, $3)
                        ON CONFLICT (user_id, game_type) 
                        DO UPDATE SET 
                            wins = game_stats_agg.wins + 1,
                            total_bets = game_stats_agg.total_bets + 1,
                            total_won = game_stats_agg.total_won + $3
                    """, user_id, game, win_amount)
                else:
                    await conn.execute("""
                        INSERT INTO game_stats_agg (user_id, game_type, losses, total_bets, total_lost)
                        VALUES ($1, $2, 1, 1, $3)
                        ON CONFLICT (user_id, game_type) 
                        DO UPDATE SET 
                            losses = game_stats_agg.losses + 1,
                            total_bets = game_stats_agg.total_bets + 1,
                            total_lost = game_stats_agg.total_lost + $3
                    """, user_id, game, bet)
                    
                    # Обновляем total_lost в users
                    await conn.execute("""
                        UPDATE users 
                        SET total_lost = total_lost + $1 
                        WHERE user_id = $2
                    """, bet, user_id)
    
    @classmethod
    async def get_user_stats(cls, user_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя по всем играм"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT game_type, wins, losses, total_bets, total_won, total_lost
                FROM game_stats_agg
                WHERE user_id = $1
            """, user_id)
            
            stats = {}
            for row in rows:
                stats[row['game_type']] = dict(row)
            
            return stats
    
    @classmethod
    async def get_top_balance(cls, limit: int = 10):
        """Топ по балансу"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch("""
                SELECT user_id, username, balance_lc 
                FROM users 
                WHERE is_banned = FALSE 
                ORDER BY balance_lc DESC 
                LIMIT $1
            """, limit)
    
    @classmethod
    async def get_top_game(cls, game: str, limit: int = 10):
        """Топ по игре"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch("""
                SELECT u.user_id, u.username, 
                       COALESCE(g.wins, 0) as wins,
                       COALESCE(g.total_won, 0) as total_won
                FROM users u
                LEFT JOIN game_stats_agg g ON u.user_id = g.user_id AND g.game_type = $1
                WHERE u.is_banned = FALSE
                ORDER BY total_won DESC, wins DESC
                LIMIT $2
            """, game, limit)

# Создаем глобальный экземпляр БД
db = Database()
