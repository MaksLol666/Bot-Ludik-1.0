from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from handlers.glc import add_glc
from keyboards.inline import get_back_button

router = Router()

ACHIEVEMENTS = {
    "first_win": {
        "name": "Первая победа 🎉",
        "desc": "Выиграть первую игру",
        "reward_lc": 1000,
        "reward_glc": 50,
        "hidden": False,
        "target": 1
    },
    "lucky_7": {
        "name": "Счастливое число 7️⃣",
        "desc": "Выиграть 7 раз подряд",
        "reward_lc": 5000,
        "reward_glc": 200,
        "hidden": False,
        "target": 7
    },
    "high_roller": {
        "name": "Высокий роллер 💰",
        "desc": "Сделать ставку 100k LC",
        "reward_lc": 10000,
        "reward_glc": 500,
        "hidden": False,
        "target": 100000
    },
    "collector": {
        "name": "Коллекционер 🎒",
        "desc": "Купить 10 статусов",
        "reward_lc": 5000,
        "reward_glc": 300,
        "hidden": False,
        "target": 10
    },
    "vip": {
        "name": "VIP 💎",
        "desc": "Потратить 50k GLC",
        "reward_lc": 20000,
        "reward_glc": 1000,
        "hidden": False,
        "target": 50000
    },
    "popular": {
        "name": "Популярный 👥",
        "desc": "Пригласить 10 друзей",
        "reward_lc": 15000,
        "reward_glc": 500,
        "hidden": False,
        "target": 10
    },
    "supporter": {
        "name": "Поддержка 💝",
        "desc": "Сделать первый донат",
        "reward_lc": 5000,
        "reward_glc": 200,
        "hidden": False,
        "target": 1
    },
    "whale": {
        "name": "Кит 🐋",
        "desc": "Потратить 100k ₽ на донаты",
        "reward_lc": 100000,
        "reward_glc": 5000,
        "hidden": True,
        "target": 100000
    },
    "lucky": {
        "name": "Везунчик 🍀",
        "desc": "Выиграть в лотерею",
        "reward_lc": 10000,
        "reward_glc": 300,
        "hidden": False,
        "target": 1
    },
    "miner": {
        "name": "Шахтёр ⛏️",
        "desc": "Открыть 100 клеток в минах без подрыва",
        "reward_lc": 8000,
        "reward_glc": 250,
        "hidden": False,
        "target": 100
    },
    "gambler": {
        "name": "Игрок 🎰",
        "desc": "Сыграть 1000 игр",
        "reward_lc": 20000,
        "reward_glc": 1000,
        "hidden": False,
        "target": 1000
    },
    "millionaire": {
        "name": "Миллионер 💰",
        "desc": "Накопить 1 млн LC",
        "reward_lc": 50000,
        "reward_glc": 2000,
        "hidden": False,
        "target": 1000000
    },
}

@router.message(Command("achievements"))
@router.callback_query(F.data == "achievements")
async def show_achievements(event: Message | CallbackQuery):
    """Показать достижения"""
    user_id = event.from_user.id
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        unlocked = await conn.fetch("""
            SELECT achievement_key FROM achievements WHERE user_id = $1
        """, user_id)
        
        progress = await conn.fetch("""
            SELECT * FROM achievement_progress WHERE user_id = $1
        """, user_id)
    
    unlocked_keys = [u['achievement_key'] for u in unlocked]
    progress_dict = {p['achievement_key']: p for p in progress}
    
    text = f"🏆 <b>ДОСТИЖЕНИЯ</b>\n\n"
    text += f"Разблокировано: {len(unlocked_keys)}/{len(ACHIEVEMENTS)}\n\n"
    
    for key, ach in ACHIEVEMENTS.items():
        if ach.get('hidden') and key not in unlocked_keys:
            continue
            
        status = "✅" if key in unlocked_keys else "❌"
        text += f"{status} <b>{ach['name']}</b>\n"
        text += f"   {ach['desc']}\n"
        
        if key in progress_dict and key not in unlocked_keys:
            p = progress_dict[key]
            text += f"   Прогресс: {p['progress']}/{p['target']}\n"
        
        if key not in unlocked_keys:
            text += f"   Награда: {ach['reward_lc']} LC + {ach['reward_glc']} GLC\n"
        text += "\n"
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_back_button())
    else:
        await event.message.edit_text(text, reply_markup=get_back_button())
        await event.answer()

async def check_achievement(user_id: int, achievement_key: str, progress_amount: int = 1):
    """Проверить прогресс достижения и разблокировать если нужно"""
    if achievement_key not in ACHIEVEMENTS:
        return
    
    ach = ACHIEVEMENTS[achievement_key]
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        unlocked = await conn.fetchrow("""
            SELECT * FROM achievements WHERE user_id = $1 AND achievement_key = $2
        """, user_id, achievement_key)
        
        if unlocked:
            return
        
        result = await conn.fetchrow("""
            INSERT INTO achievement_progress (user_id, achievement_key, progress, target)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, achievement_key) 
            DO UPDATE SET progress = achievement_progress.progress + $3
            RETURNING progress
        """, user_id, achievement_key, progress_amount, ach['target'])
        
        if result['progress'] >= ach['target']:
            await conn.execute("""
                INSERT INTO achievements (user_id, achievement_key) VALUES ($1, $2)
            """, user_id, achievement_key)
            
            await db.update_balance(user_id, ach['reward_lc'])
            if ach['reward_glc'] > 0:
                await add_glc(user_id, ach['reward_glc'], f"Achievement: {ach['name']}")
            
            await conn.execute("""
                DELETE FROM achievement_progress WHERE user_id = $1 AND achievement_key = $2
            """, user_id, achievement_key)
            
            return True
    
    return False
