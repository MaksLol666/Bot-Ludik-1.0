from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime
import random

from database import db
from handlers.glc import add_glc
from keyboards.inline import get_back_button, get_daily_quests_keyboard

router = Router()

QUESTS = [
    {"name": "Игрок в рулетку", "type": "roulette_bets", "target": 5, "reward_lc": 500, "reward_glc": 5},
    {"name": "Счастливчик", "type": "roulette_wins", "target": 3, "reward_lc": 800, "reward_glc": 10},
    {"name": "Слот-машина", "type": "slots_bets", "target": 5, "reward_lc": 500, "reward_glc": 5},
    {"name": "Джекпот", "type": "slots_wins", "target": 2, "reward_lc": 800, "reward_glc": 10},
    {"name": "Дуэлянт", "type": "dice_bets", "target": 3, "reward_lc": 600, "reward_glc": 8},
    {"name": "Победитель", "type": "dice_wins", "target": 2, "reward_lc": 900, "reward_glc": 12},
    {"name": "Сапёр", "type": "mines_bets", "target": 3, "reward_lc": 600, "reward_glc": 8},
    {"name": "Обезвреживатель", "type": "mines_wins", "target": 2, "reward_lc": 900, "reward_glc": 12},
    {"name": "Покерист", "type": "poker_bets", "target": 2, "reward_lc": 1000, "reward_glc": 15},
    {"name": "Блэкджек", "type": "blackjack_bets", "target": 3, "reward_lc": 700, "reward_glc": 10},
    {"name": "Краш", "type": "crash_bets", "target": 3, "reward_lc": 700, "reward_glc": 10},
    {"name": "Dice", "type": "dice_game_bets", "target": 5, "reward_lc": 600, "reward_glc": 8},
    {"name": "Ставки", "type": "total_bets", "target": 15, "reward_lc": 1500, "reward_glc": 20},
]

@router.message(Command("quests"))
@router.callback_query(F.data == "daily_quests")
async def show_daily_quests(event: Message | CallbackQuery):
    """Показать ежедневные задания"""
    user_id = event.from_user.id
    today = datetime.now().date()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        quests = await conn.fetch("""
            SELECT * FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2
        """, user_id, today)
        
        if not quests:
            selected = random.sample(QUESTS, 3)
            for q in selected:
                await conn.execute("""
                    INSERT INTO daily_quests 
                    (user_id, quest_date, quest_type, target, reward_lc, reward_glc)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, user_id, today, q['type'], q['target'], q['reward_lc'], q['reward_glc'])
            
            quests = await conn.fetch("""
                SELECT * FROM daily_quests 
                WHERE user_id = $1 AND quest_date = $2
            """, user_id, today)
    
    text = f"📋 <b>Ежедневные задания</b>\n\n"
    text += f"📅 {today.strftime('%d.%m.%Y')}\n\n"
    
    completed_count = 0
    for q in quests:
        status = "✅" if q['completed'] else "⏳"
        progress_text = f"{q['progress']}/{q['target']}" if not q['completed'] else "выполнено"
        text += f"{status} <b>{q['quest_type']}</b>\n"
        text += f"   • Прогресс: {progress_text}\n"
        text += f"   • Награда: {q['reward_lc']} LC + {q['reward_glc']} GLC\n\n"
        
        if q['completed']:
            completed_count += 1
    
    text += f"Выполнено: {completed_count}/3"
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_daily_quests_keyboard())
    else:
        await event.message.edit_text(text, reply_markup=get_daily_quests_keyboard())
        await event.answer()

@router.callback_query(F.data == "claim_quests")
async def claim_completed_quests(callback: CallbackQuery):
    """Забрать награды за выполненные задания"""
    user_id = callback.from_user.id
    today = datetime.now().date()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        completed = await conn.fetch("""
            SELECT * FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2 AND completed = TRUE
        """, user_id, today)
        
        if not completed:
            await callback.answer("❌ Нет выполненных заданий!", show_alert=True)
            return
        
        total_lc = sum(q['reward_lc'] for q in completed)
        total_glc = sum(q['reward_glc'] for q in completed)
        
        await db.update_balance(user_id, total_lc)
        for q in completed:
            if q['reward_glc'] > 0:
                await add_glc(user_id, q['reward_glc'], f"Daily quest: {q['quest_type']}")
        
        await conn.execute("""
            DELETE FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2 AND completed = TRUE
        """, user_id, today)
    
    await callback.answer(
        f"✅ Получено: {total_lc} LC + {total_glc} GLC!",
        show_alert=True
    )
    await show_daily_quests(callback)

async def update_quest_progress(user_id: int, quest_type: str, progress_amount: int = 1):
    """Обновить прогресс задания"""
    today = datetime.now().date()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        quest = await conn.fetchrow("""
            SELECT * FROM daily_quests 
            WHERE user_id = $1 AND quest_date = $2 
            AND quest_type = $3 AND completed = FALSE
        """, user_id, today, quest_type)
        
        if quest:
            new_progress = quest['progress'] + progress_amount
            if new_progress >= quest['target']:
                await conn.execute("""
                    UPDATE daily_quests 
                    SET progress = $1, completed = TRUE 
                    WHERE id = $2
                """, quest['target'], quest['id'])
            else:
                await conn.execute("""
                    UPDATE daily_quests SET progress = $1 WHERE id = $2
                """, new_progress, quest['id'])
