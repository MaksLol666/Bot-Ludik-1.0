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

        # Статистика игр
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

        # ПРОМОКОДЫ - ЭТОТ КОД ВАЖЕН!
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

        # Логи действий
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

        # Переводы
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

    # ... остальные методы БД (get_user, create_user, update_balance и т.д.) ...
