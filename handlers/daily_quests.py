from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime
import random

from database_sqlite import db
from handlers.glc import add_glc
from keyboards.inline import get_back_button, get_daily_quests_keyboard

router = Router()

# ТИПЫ КВЕСТОВ (со всеми играми, включая покер и блэкджек)
QUESTS = [
    # Рулетка
    {"id": "roulette_bets_5", "name": "🎰 Игрок в рулетку", "type": "roulette_bets", "target": 5, "reward_lc": 500, "reward_glc": 5},
    {"id": "roulette_wins_3", "name": "🎯 Счастливчик", "type": "roulette_wins", "target": 3, "reward_lc": 800, "reward_glc": 10},
    
    # Слоты
    {"id": "slots_bets_5", "name": "🍒 Слот-машина", "type": "slots_bets", "target": 5, "reward_lc": 500, "reward_glc": 5},
    {"id": "slots_wins_2", "name": "💎 Джекпот", "type": "slots_wins", "target": 2, "reward_lc": 800, "reward_glc": 10},
    
    # Кости
    {"id": "dice_bets_3", "name": "⚔️ Дуэлянт", "type": "dice_bets", "target": 3, "reward_lc": 600, "reward_glc": 8},
    {"id": "dice_wins_2", "name": "🏆 Победитель", "type": "dice_wins", "target": 2, "reward_lc": 900, "reward_glc": 12},
    
    # Мины
    {"id": "mines_bets_3", "name": "💣 Сапёр", "type": "mines_bets", "target": 3, "reward_lc": 600, "reward_glc": 8},
    {"id": "mines_wins_2", "name": "🔨 Обезвреживатель", "type": "mines_wins", "target": 2, "reward_lc": 900, "reward_glc": 12},
    
    # Лотерея
    {"id": "lottery_bets_1", "name": "🎟 Лотерейщик", "type": "lottery_bets", "target": 1, "reward_lc": 400, "reward_glc": 5},
    
    # Покер
    {"id": "poker_bets_2", "name": "🃏 Покерист", "type": "poker_bets", "target": 2, "reward_lc": 1000, "reward_glc": 15},
    {"id": "poker_wins_1", "name": "♠️ Король покера", "type": "poker_wins", "target": 1, "reward_lc": 1500, "reward_glc": 20},
    
    # Блэкджек
    {"id": "blackjack_bets_3", "name": "🃏 Блэкджек", "type": "blackjack_bets", "target": 3, "reward_lc": 700, "reward_glc": 10},
    {"id": "blackjack_wins_2", "name": "🎴 Счётчик карт", "type": "blackjack_wins", "target": 2, "reward_lc": 1100, "reward_glc": 15},
    
    # Краш
    {"id": "crash_bets_3", "name": "📈 Краш", "type": "crash_bets", "target": 3, "reward_lc": 700, "reward_glc": 10},
    {"id": "crash_wins_2", "name": "🚀 Космонавт", "type": "crash_wins", "target": 2, "reward_lc": 1200, "reward_glc": 18},
    
    # Dice (если есть отдельная игра Dice)
    {"id": "dice_game_bets_5", "name": "🎲 Dice", "type": "dice_game_bets", "target": 5, "reward_lc": 600, "reward_glc": 8},
    
    # Общее
    {"id": "total_bets_15", "name": "🎮 Азартный игрок", "type": "total_bets", "target": 15, "reward_lc": 1500, "reward_glc": 20},
]

async def init_quests_table():
    """Создание таблицы для квестов"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_quests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
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

async def get_daily_quests(user_id: int):
    """Получить квесты на сегодня"""
    pool = await db.get_pool()
    today = datetime.now().date()
    
    async with pool.acquire() as conn:
        existing = await conn.fetch("""
            SELECT * FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2
        """, user_id, today)
        
        if not existing:
            selected = random.sample(QUESTS, 3)
            for quest in selected:
                await conn.execute("""
                    INSERT INTO daily_quests 
                    (user_id, quest_date, quest_id, quest_type, target, reward_lc, reward_glc)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, user_id, today, quest['id'], quest['type'], quest['target'], 
                    quest['reward_lc'], quest['reward_glc'])
            
            existing = await conn.fetch("""
                SELECT * FROM daily_quests 
                WHERE user_id = $1 AND quest_date = $2
            """, user_id, today)
    
    return existing

@router.message(Command("quests"))
@router.callback_query(F.data == "daily_quests")
async def show_daily_quests(event: Message | CallbackQuery):
    """Показать ежедневные задания"""
    user_id = event.from_user.id
    today = datetime.now().date()
    
    quests = await get_daily_quests(user_id)
    
    text = f"📋 <b>ЕЖЕДНЕВНЫЕ ЗАДАНИЯ</b>\n\n"
    text += f"📅 {today.strftime('%d.%m.%Y')}\n\n"
    
    completed_count = 0
    for q in quests:
        # Находим название квеста
        quest_info = next((x for x in QUESTS if x['id'] == q['quest_id']), None)
        quest_name = quest_info['name'] if quest_info else q['quest_type']
        
        if q['completed']:
            status = "✅"
            progress_text = "выполнено"
            completed_count += 1
        else:
            status = "⏳"
            progress_text = f"{q['progress']}/{q['target']}"
        
        text += f"{status} <b>{quest_name}</b>\n"
        text += f"   • Прогресс: {progress_text}\n"
        text += f"   • Награда: {q['reward_lc']} LC + {q['reward_glc']} GLC\n\n"
    
    text += f"Выполнено: {completed_count}/3"
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_daily_quests_keyboard(quests))
    else:
        await event.message.edit_text(text, reply_markup=get_daily_quests_keyboard(quests))
        await event.answer()

async def update_quest_progress(user_id: int, quest_type: str, progress_amount: int = 1, win: bool = False):
    """Обновить прогресс задания (вызывается из игр)
    
    Аргументы:
        user_id: ID пользователя
        quest_type: тип квеста (roulette_bets, roulette_wins, etc.)
        progress_amount: сколько добавить (обычно 1)
        win: была ли победа (для квестов на победы)
    """
    today = datetime.now().date()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        # Получаем все активные квесты на сегодня
        quests = await conn.fetch("""
            SELECT * FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2 AND completed = FALSE
        """, user_id, today)
        
        for quest in quests:
            quest_info = next((x for x in QUESTS if x['id'] == quest['quest_id']), None)
            if not quest_info:
                continue
            
            # Проверяем, подходит ли тип квеста
            if quest['quest_type'] == quest_type:
                new_progress = quest['progress'] + progress_amount
                
                if new_progress >= quest['target']:
                    # Квест выполнен
                    await conn.execute("""
                        UPDATE daily_quests 
                        SET progress = $1, completed = TRUE 
                        WHERE id = $2
                    """, quest['target'], quest['id'])
                else:
                    # Обновляем прогресс
                    await conn.execute("""
                        UPDATE daily_quests SET progress = $1 WHERE id = $2
                    """, new_progress, quest['id'])

@router.callback_query(F.data.startswith("claim_quest_"))
async def claim_quest(callback: CallbackQuery):
    """Забрать награду за конкретный квест"""
    quest_id = int(callback.data.replace("claim_quest_", ""))
    user_id = callback.from_user.id
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        quest = await conn.fetchrow("""
            SELECT * FROM daily_quests 
            WHERE id = $1 AND user_id = $2 AND completed = TRUE AND claimed = FALSE
        """, quest_id, user_id)
        
        if not quest:
            await callback.answer("❌ Награда уже получена или квест не выполнен!", show_alert=True)
            return
        
        # Начисляем награду
        await db.update_balance(user_id, quest['reward_lc'])
        if quest['reward_glc'] > 0:
            await add_glc(user_id, quest['reward_glc'], f"Daily quest reward")
        
        # Отмечаем как полученное
        await conn.execute("""
            UPDATE daily_quests SET claimed = TRUE WHERE id = $1
        """, quest_id)
    
    await callback.answer(f"✅ Получено: {quest['reward_lc']} LC + {quest['reward_glc']} GLC!", show_alert=True)
    await show_daily_quests(callback)

@router.callback_query(F.data == "claim_all_quests")
async def claim_all_quests(callback: CallbackQuery):
    """Забрать награды за все выполненные задания"""
    user_id = callback.from_user.id
    today = datetime.now().date()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        completed = await conn.fetch("""
            SELECT * FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2 AND completed = TRUE AND claimed = FALSE
        """, user_id, today)
        
        if not completed:
            await callback.answer("❌ Нет доступных наград!", show_alert=True)
            return
        
        total_lc = sum(q['reward_lc'] for q in completed)
        total_glc = sum(q['reward_glc'] for q in completed)
        
        # Начисляем все награды
        await db.update_balance(user_id, total_lc)
        if total_glc > 0:
            await add_glc(user_id, total_glc, f"All daily quests reward")
        
        # Отмечаем все как полученные
        for q in completed:
            await conn.execute("""
                UPDATE daily_quests SET claimed = TRUE WHERE id = $1
            """, q['id'])
    
    await callback.answer(f"✅ Получено: {total_lc} LC + {total_glc} GLC!", show_alert=True)
    await show_daily_quests(callback)
