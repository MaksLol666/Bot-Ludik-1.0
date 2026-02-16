# database.py

import os
import asyncpg
from asyncpg import Pool
from typing import Optional, Dict, Any, List
import datetime

class Database:
    _pool: Optional[Pool] = None

    @classmethod
    async def connect(cls):
        """Подключение к БД и создание всех таблиц"""
        # Берем URL из переменных окружения или используем локальный по умолчанию
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ludik_db")
        cls._pool = await asyncpg.create_pool(database_url)

        async with cls._pool.acquire() as conn:
            # --- Таблица пользователей ---
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

            # --- Таблица статистики игр (детальная) ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    game_type TEXT,
                    bet BIGINT,
                    win BOOLEAN DEFAULT FALSE,
                    win_amount BIGINT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # --- Таблица агрегированной статистики игр (для быстрых топов) ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_stats_agg (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    game_type TEXT,
                    wins INT DEFAULT 0,
                    losses INT DEFAULT 0,
                    total_bets INT DEFAULT 0,
                    total_won BIGINT DEFAULT 0,
                    total_lost BIGINT DEFAULT 0,
                    PRIMARY KEY (user_id, game_type)
                )
            """)

            # --- Таблица промокодов ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    reward BIGINT,
                    max_uses INT,
                    used_count INT DEFAULT 0
                )
            """)

            # --- Таблица использованных промокодов ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS used_promocodes (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    code TEXT REFERENCES promocodes(code) ON DELETE CASCADE,
                    used_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, code)
                )
            """)

            # --- Таблица бизнеса ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS business (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                    business_type TEXT,
                    last_collected TIMESTAMP
                )
            """)

            # --- Таблица билетов лотереи ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lottery_tickets (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    week_number TEXT,
                    ticket_count INT DEFAULT 0,
                    purchase_date TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, week_number)
                )
            """)

            # --- Таблица результатов лотереи ---
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

            # --- Таблица рефералов ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    referral_id BIGINT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
                    registered_at TIMESTAMP DEFAULT NOW(),
                    donat_amount BIGINT DEFAULT 0
                )
            """)

            # --- Таблица статусов игроков (для отображения иконок) ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_status (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                    status TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # --- Таблица инвентаря (купленные VIP статусы) ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_inventory (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    emoji TEXT,
                    name TEXT,
                    price INT,
                    is_equipped BOOLEAN DEFAULT FALSE,
                    purchased_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # --- Таблица достижений ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    achievement_key TEXT,
                    unlocked_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, achievement_key)
                )
            """)

            # --- Таблица прогресса достижений ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS achievement_progress (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    achievement_key TEXT,
                    progress INT DEFAULT 0,
                    target INT,
                    PRIMARY KEY (user_id, achievement_key)
                )
            """)

            # --- Таблица ежедневных квестов ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_quests (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    quest_date DATE,
                    quest_id TEXT,
                    quest_type TEXT,
                    target INT,
                    progress INT DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    claimed BOOLEAN DEFAULT FALSE,
                    reward_lc INT,
                    reward_glc INT,
                    UNIQUE(user_id, quest_date, quest_id)
                )
            """)

            # --- Таблица жалоб ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id SERIAL PRIMARY KEY,
                    complainant_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
                    accused_id BIGINT,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    reviewed_at TIMESTAMP,
                    reviewed_by BIGINT
                )
            """)

            # --- Таблица донатов ---
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
                    amount INT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # --- Создание индексов для ускорения запросов ---
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_stats_user_id ON game_stats(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_stats_game_type ON game_stats(game_type);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_game_stats_created ON game_stats(created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_quests_user ON daily_quests(user_id, quest_date);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);")

            print("✅ Все таблицы успешно созданы или уже существуют!")

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

    # --- Методы для работы с пользователями ---
    @classmethod
    async def get_user(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по ID"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
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
        """Обновить LC баланс. amount может быть отрицательным."""
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
        """Обновить GLC баланс. amount может быть отрицательным."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                UPDATE users
                SET balance_glc = balance_glc + $1
                WHERE user_id = $2
                RETURNING balance_glc
            """, amount, user_id)
            return result

    # --- Методы для статистики игр ---
    @classmethod
    async def add_game_stat(cls, user_id: int, game: str, win: bool, bet: int, win_amount: int):
        """Добавить статистику игры"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Добавляем запись в детальную статистику
                await conn.execute("""
                    INSERT INTO game_stats (user_id, game_type, win, bet, win_amount)
                    VALUES ($1, $2, $3, $4, $5)
                """, user_id, game, win, bet, win_amount)

                # Обновляем агрегированную статистику
                if win:
                    await conn.execute("""
                        INSERT INTO game_stats_agg (user_id, game_type, wins, total_bets, total_won)
                        VALUES ($1, $2, 1, 1, $3)
                        ON CONFLICT (user_id, game_type) DO UPDATE SET
                            wins = game_stats_agg.wins + 1,
                            total_bets = game_stats_agg.total_bets + 1,
                            total_won = game_stats_agg.total_won + $3
                    """, user_id, game, win_amount)
                else:
                    await conn.execute("""
                        INSERT INTO game_stats_agg (user_id, game_type, losses, total_bets, total_lost)
                        VALUES ($1, $2, 1, 1, $3)
                        ON CONFLICT (user_id, game_type) DO UPDATE SET
                            losses = game_stats_agg.losses + 1,
                            total_bets = game_stats_agg.total_bets + 1,
                            total_lost = game_stats_agg.total_lost + $3
                    """, user_id, game, bet)

                    # Обновляем общую сумму проигрыша в таблице users
                    await conn.execute("""
                        UPDATE users SET total_lost = total_lost + $1 WHERE user_id = $2
                    """, bet, user_id)

    @classmethod
    async def get_top_balance(cls, limit: int = 10) -> List[asyncpg.Record]:
        """Топ по балансу LC"""
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
    async def get_top_game(cls, game: str, limit: int = 10) -> List[asyncpg.Record]:
        """Топ по сумме выигрыша в конкретной игре"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch("""
                SELECT u.user_id, u.username,
                       COALESCE(g.wins, 0) as wins,
                       COALESCE(g.total_won, 0) as total_won
                FROM users u
                LEFT JOIN game_stats_agg g ON u.user_id = g.user_id AND g.game_type = $1
                WHERE u.is_banned = FALSE
                ORDER BY total_won DESC
                LIMIT $2
            """, game, limit)


# Создаем глобальный экземпляр БД для импорта в других модулях
db = Database()
