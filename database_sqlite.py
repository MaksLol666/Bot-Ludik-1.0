import sqlite3
import os
import aiosqlite  # нужно установить
from typing import Optional, Dict, Any, List
from datetime import datetime

class Database:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.db_path = "ludik_bot.db"

    async def get_connection(self):
        """Получить асинхронное соединение с БД"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def create_tables(self):
        """Создание всех таблиц"""
        conn = await self.get_connection()
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance_lc INTEGER DEFAULT 2500,
                balance_glc INTEGER DEFAULT 0,
                referrer_id INTEGER,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_bonus TIMESTAMP,
                total_lost INTEGER DEFAULT 0
            )
        """)
        
        # ... остальные CREATE TABLE ...
        
        await conn.commit()
        print("✅ Таблицы SQLite созданы")

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя"""
        conn = await self.get_connection()
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по username"""
        conn = await self.get_connection()
        cursor = await conn.execute("SELECT * FROM users WHERE username = ?", (username.replace('@', ''),))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def create_user(self, user_id: int, username: str, first_name: str, referrer_id: int = None):
        """Создать пользователя"""
        conn = await self.get_connection()
        
        await conn.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, referrer_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, referrer_id))
        
        if referrer_id:
            await conn.execute("""
                INSERT OR IGNORE INTO referrals (referrer_id, referral_id)
                VALUES (?, ?)
            """, (referrer_id, user_id))
            
            await self.update_balance(referrer_id, 1000)
            await self.update_glc(referrer_id, 100)
            
        await conn.commit()

    async def update_balance(self, user_id: int, amount: int) -> int:
        """Обновить баланс LC"""
        conn = await self.get_connection()
        await conn.execute("UPDATE users SET balance_lc = balance_lc + ? WHERE user_id = ?", (amount, user_id))
        await conn.commit()
        
        cursor = await conn.execute("SELECT balance_lc FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def update_glc(self, user_id: int, amount: int) -> int:
        """Обновить баланс GLC"""
        conn = await self.get_connection()
        await conn.execute("UPDATE users SET balance_glc = balance_glc + ? WHERE user_id = ?", (amount, user_id))
        await conn.commit()
        
        cursor = await conn.execute("SELECT balance_glc FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def add_game_stat(self, user_id: int, game: str, win: bool, bet: int, win_amount: int):
        """Добавить статистику игры"""
        conn = await self.get_connection()
        
        await conn.execute("""
            INSERT INTO game_stats (user_id, game_type, win, bet, win_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, game, win, bet, win_amount))
        
        if not win:
            await conn.execute("UPDATE users SET total_lost = total_lost + ? WHERE user_id = ?", (bet, user_id))
        
        await conn.commit()
        await self.log_action(user_id, f"игра_{game}", f"{'win' if win else 'lose'}: {bet}")

    async def transfer_lc(self, from_user: int, to_user: int, amount: int) -> tuple[bool, str]:
        """Перевод LC между пользователями"""
        conn = await self.get_connection()
        
        sender = await self.get_user(from_user)
        if not sender:
            return False, "Отправитель не найден"
        
        if sender['balance_lc'] < amount:
            return False, "Недостаточно средств"
        
        receiver = await self.get_user(to_user)
        if not receiver:
            return False, "Получатель не найден"
        
        await conn.execute("UPDATE users SET balance_lc = balance_lc - ? WHERE user_id = ?", (amount, from_user))
        await conn.execute("UPDATE users SET balance_lc = balance_lc + ? WHERE user_id = ?", (amount, to_user))
        
        await conn.execute("""
            INSERT INTO transfers (from_user, to_user, amount)
            VALUES (?, ?, ?)
        """, (from_user, to_user, amount))
        
        await conn.commit()
        
        await self.log_action(from_user, "перевод", f"отправил {amount} LC пользователю {to_user}")
        await self.log_action(to_user, "перевод", f"получил {amount} LC от {from_user}")
        
        return True, "Перевод выполнен успешно"

    async def log_action(self, user_id: int, action: str, details: str = ""):
        """Записать действие пользователя"""
        conn = await self.get_connection()
        await conn.execute("""
            INSERT INTO user_logs (user_id, action, details)
            VALUES (?, ?, ?)
        """, (user_id, action, details))
        await conn.commit()

    async def get_user_full_info(self, identifier) -> Dict[str, Any]:
        """Получить полную информацию о пользователе"""
        conn = await self.get_connection()
        
        if isinstance(identifier, int):
            cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (identifier,))
        else:
            cursor = await conn.execute("SELECT * FROM users WHERE username = ?", (identifier.replace('@', ''),))
        
        user_row = await cursor.fetchone()
        if not user_row:
            return {"error": "Пользователь не найден"}
        
        user = dict(user_row)
        user_id = user['user_id']
        
        # Статистика игр
        cursor = await conn.execute("""
            SELECT 
                game_type,
                COUNT(*) as total_games,
                SUM(CASE WHEN win THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN win THEN 0 ELSE 1 END) as losses,
                SUM(bet) as total_bet,
                SUM(win_amount) as total_won
            FROM game_stats
            WHERE user_id = ?
            GROUP BY game_type
        """, (user_id,))
        game_stats = [dict(row) async for row in cursor]
        
        # Логи
        cursor = await conn.execute("""
            SELECT action, details, created_at
            FROM user_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        logs = [dict(row) async for row in cursor]
        
        # Переводы
        cursor = await conn.execute("""
            SELECT * FROM transfers 
            WHERE from_user = ? OR to_user = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id, user_id))
        transfers = [dict(row) async for row in cursor]
        
        # Рефералы
        cursor = await conn.execute("""
            SELECT u.user_id, u.username, u.registered_at
            FROM referrals r
            JOIN users u ON r.referral_id = u.user_id
            WHERE r.referrer_id = ?
        """, (user_id,))
        referrals = [dict(row) async for row in cursor]
        
        return {
            "user": user,
            "game_stats": game_stats,
            "logs": logs,
            "transfers": transfers,
            "referrals": referrals,
            "total_games": sum(s['total_games'] for s in game_stats),
            "total_wins": sum(s['wins'] for s in game_stats),
            "total_losses": sum(s['losses'] for s in game_stats)
        }

# Создаем глобальный экземпляр
db = Database()
