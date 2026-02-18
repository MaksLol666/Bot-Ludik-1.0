import sqlite3
import os
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
        if not os.path.exists(self.db_path):
            self.create_tables()

    def get_connection(self):
        """Получить соединение с БД"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def create_tables(self):
        """Создание всех таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Пользователи
        cursor.execute("""
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

        # Статистика игр (детальная)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_type TEXT,
                win BOOLEAN,
                bet INTEGER,
                win_amount INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Промокоды
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                reward INTEGER,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0
            )
        """)

        # Использованные промокоды
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS used_promocodes (
                user_id INTEGER,
                code TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (code) REFERENCES promocodes(code),
                PRIMARY KEY (user_id, code)
            )
        """)

        # Бизнес
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business (
                user_id INTEGER PRIMARY KEY,
                business_type TEXT,
                last_collected TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Лотерея
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lottery_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                week_number TEXT,
                ticket_count INTEGER DEFAULT 0,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, week_number)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lottery_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_number TEXT UNIQUE,
                draw_date TIMESTAMP,
                winners TEXT,
                total_tickets INTEGER,
                total_amount INTEGER
            )
        """)

        # Рефералы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referral_id INTEGER UNIQUE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                donat_amount INTEGER DEFAULT 0,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referral_id) REFERENCES users(user_id)
            )
        """)

        # Статусы игроков
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_status (
                user_id INTEGER PRIMARY KEY,
                status TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Логи действий (для админ-панели)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Переводы между пользователями
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER,
                to_user INTEGER,
                amount INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user) REFERENCES users(user_id),
                FOREIGN KEY (to_user) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        print("✅ Таблицы SQLite созданы")

    # ===== ОСНОВНЫЕ МЕТОДЫ =====

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.replace('@', ''),))
        row = cursor.fetchone()
        return dict(row) if row else None

    def create_user(self, user_id: int, username: str, first_name: str, referrer_id: int = None):
        """Создать пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, referrer_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, referrer_id))
        
        if referrer_id:
            cursor.execute("""
                INSERT OR IGNORE INTO referrals (referrer_id, referral_id)
                VALUES (?, ?)
            """, (referrer_id, user_id))
            
            # Бонус рефереру
            self.update_balance(referrer_id, 1000)
            self.update_glc(referrer_id, 100)
            
        conn.commit()

    def update_balance(self, user_id: int, amount: int) -> int:
        """Обновить баланс LC"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET balance_lc = balance_lc + ? 
            WHERE user_id = ? 
            RETURNING balance_lc
        """, (amount, user_id))
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else 0

    def update_glc(self, user_id: int, amount: int) -> int:
        """Обновить баланс GLC"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET balance_glc = balance_glc + ? 
            WHERE user_id = ? 
            RETURNING balance_glc
        """, (amount, user_id))
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else 0

    def add_game_stat(self, user_id: int, game: str, win: bool, bet: int, win_amount: int):
        """Добавить статистику игры"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO game_stats (user_id, game_type, win, bet, win_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, game, win, bet, win_amount))
        
        if not win:
            cursor.execute("""
                UPDATE users 
                SET total_lost = total_lost + ? 
                WHERE user_id = ?
            """, (bet, user_id))
        
        conn.commit()
        self.log_action(user_id, f"игра_{game}", f"{'win' if win else 'lose'}: {bet}")

    def transfer_lc(self, from_user: int, to_user: int, amount: int) -> tuple[bool, str]:
        """Перевод LC между пользователями"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем отправителя
        sender = self.get_user(from_user)
        if not sender:
            return False, "Отправитель не найден"
        
        if sender['balance_lc'] < amount:
            return False, "Недостаточно средств"
        
        # Проверяем получателя
        receiver = self.get_user(to_user)
        if not receiver:
            return False, "Получатель не найден"
        
        # Выполняем перевод
        cursor.execute("UPDATE users SET balance_lc = balance_lc - ? WHERE user_id = ?", (amount, from_user))
        cursor.execute("UPDATE users SET balance_lc = balance_lc + ? WHERE user_id = ?", (amount, to_user))
        
        # Логируем перевод
        cursor.execute("""
            INSERT INTO transfers (from_user, to_user, amount)
            VALUES (?, ?, ?)
        """, (from_user, to_user, amount))
        
        conn.commit()
        
        self.log_action(from_user, "перевод", f"отправил {amount} LC пользователю {to_user}")
        self.log_action(to_user, "перевод", f"получил {amount} LC от {from_user}")
        
        return True, "Перевод выполнен успешно"

    def log_action(self, user_id: int, action: str, details: str = ""):
        """Записать действие пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_logs (user_id, action, details)
            VALUES (?, ?, ?)
        """, (user_id, action, details))
        conn.commit()

    def get_user_full_info(self, identifier) -> Dict[str, Any]:
        """Получить полную информацию о пользователе (по id или username)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Определяем, что ищем
        if isinstance(identifier, int):
            user = self.get_user(identifier)
        else:
            user = self.get_user_by_username(identifier)
        
        if not user:
            return {"error": "Пользователь не найден"}
        
        user_id = user['user_id']
        
        # Получаем статистику по играм
        cursor.execute("""
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
        game_stats = [dict(row) for row in cursor.fetchall()]
        
        # Получаем логи действий
        cursor.execute("""
            SELECT action, details, created_at
            FROM user_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        logs = [dict(row) for row in cursor.fetchall()]
        
        # Получаем переводы
        cursor.execute("""
            SELECT * FROM transfers 
            WHERE from_user = ? OR to_user = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id, user_id))
        transfers = [dict(row) for row in cursor.fetchall()]
        
        # Получаем рефералов
        cursor.execute("""
            SELECT u.user_id, u.username, u.registered_at
            FROM referrals r
            JOIN users u ON r.referral_id = u.user_id
            WHERE r.referrer_id = ?
        """, (user_id,))
        referrals = [dict(row) for row in cursor.fetchall()]
        
        # Бизнес
        cursor.execute("SELECT * FROM business WHERE user_id = ?", (user_id,))
        business = cursor.fetchone()
        
        # Лотерея
        cursor.execute("""
            SELECT * FROM lottery_tickets 
            WHERE user_id = ? 
            ORDER BY purchase_date DESC
        """, (user_id,))
        lottery = [dict(row) for row in cursor.fetchall()]
        
        return {
            "user": dict(user),
            "game_stats": game_stats,
            "logs": logs,
            "transfers": transfers,
            "referrals": referrals,
            "business": dict(business) if business else None,
            "lottery": lottery,
            "total_games": sum(s['total_games'] for s in game_stats),
            "total_wins": sum(s['wins'] for s in game_stats),
            "total_losses": sum(s['losses'] for s in game_stats)
        }

# Создаем глобальный экземпляр
db = Database()
