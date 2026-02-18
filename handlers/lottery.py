from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import random
from datetime import datetime, timedelta

from database_sqlite import db
from handlers.status import update_user_status
from handlers.daily_quests import update_quest_progress
from keyboards.inline import get_back_button

router = Router()

LOTTERY_PRICE = 10000
PRIZES = [100000, 30000, 15000]
PRIZE_NAMES = ["🥇 1 место", "🥈 2 место", "🥉 3 место"]

DRAW_DAY = 6  # Воскресенье

@router.callback_query(F.data == "lottery_menu")
async def lottery_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        current_week = await get_current_week_number()
        
        tickets_total = await conn.fetchval("""
            SELECT COALESCE(SUM(ticket_count), 0) 
            FROM lottery_tickets 
            WHERE week_number = $1
        """, current_week) or 0
        
        user_tickets = await conn.fetchval("""
            SELECT COALESCE(ticket_count, 0)
            FROM lottery_tickets 
            WHERE user_id = $1 AND week_number = $2
        """, user_id, current_week) or 0
        
        previous = await conn.fetch("""
            SELECT * FROM lottery_results 
            ORDER BY draw_date DESC 
            LIMIT 3
        """)
    
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday >= DRAW_DAY:
        days_until = (7 - weekday + 0) % 7
        if days_until == 0:
            days_until = 7
        next_draw = now + timedelta(days=days_until)
        status_text = f"📅 Следующий розыгрыш: {next_draw.strftime('%d.%m.%Y')} (воскресенье)"
    else:
        status_text = f"📅 Продажа билетов до воскресенья"
    
    prev_text = ""
    if previous:
        prev_text = "\n\n📊 <b>Прошлые розыгрыши:</b>\n"
        for p in previous[:3]:
            prev_text += f"{p['draw_date'].strftime('%d.%m')}: {p['winners']}\n"
    
    text = (
        "🎟 <b>ЛОТЕРЕЯ</b>\n\n"
        f"{status_text}\n\n"
        f"💰 <b>Цена билета:</b> {LOTTERY_PRICE} LC\n"
        f"🎫 <b>Продано билетов:</b> {tickets_total} шт.\n"
        f"👤 <b>Твои билеты:</b> {user_tickets} шт.\n\n"
        f"🏆 <b>ПРИЗЫ:</b>\n"
        f"🥇 1 место: {PRIZES[0]} LC\n"
        f"🥈 2 место: {PRIZES[1]} LC\n"
        f"🥉 3 место: {PRIZES[2]} LC\n"
        f"{prev_text}\n"
        f"👇 Купить билеты:\n"
        f"<code>/купить 1</code> — купить 1 билет\n"
        f"<code>/купить 5</code> — купить 5 билетов"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

@router.message(Command("купить"))
async def buy_lottery_tickets(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /купить [количество]")
        return
    
    try:
        count = int(args[1])
    except:
        await message.answer("❌ Количество должно быть числом")
        return
    
    if count <= 0:
        await message.answer("❌ Некорректное количество")
        return
    
    if datetime.now().weekday() >= DRAW_DAY:
        await message.answer("❌ Розыгрыш уже прошел! Жди следующего воскресенья 🎟")
        return
    
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован! Напиши /start")
        return
    
    if user['is_banned']:
        await message.answer("⛔ Ты забанен!")
        return
    
    total_cost = count * LOTTERY_PRICE
    
    if user['balance_lc'] < total_cost:
        await message.answer(f"❌ Недостаточно средств! Нужно {total_cost} LC")
        return
    
    current_week = await get_current_week_number()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await db.update_balance(user_id, -total_cost)
            
            await conn.execute("""
                INSERT INTO lottery_tickets (user_id, week_number, ticket_count)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, week_number) 
                DO UPDATE SET ticket_count = lottery_tickets.ticket_count + $3
            """, user_id, current_week, count)
            
            total_tickets = await conn.fetchval("""
                SELECT COALESCE(SUM(ticket_count), 0)
                FROM lottery_tickets 
                WHERE week_number = $1
            """, current_week)
    
    await update_quest_progress(user_id, "lottery", count)
    
    await message.answer(
        f"✅ <b>Билеты куплены!</b>\n\n"
        f"🎫 Куплено: {count} шт.\n"
        f"💰 Потрачено: {total_cost} LC\n"
        f"📊 Всего билетов: {total_tickets} шт.\n\n"
        f"🍀 Удачи в воскресенье!"
    )

@router.message(Command("моибилеты"))
async def my_tickets(message: Message):
    user_id = message.from_user.id
    current_week = await get_current_week_number()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tickets = await conn.fetchval("""
            SELECT ticket_count FROM lottery_tickets 
            WHERE user_id = $1 AND week_number = $2
        """, user_id, current_week) or 0
        
        total_tickets = await conn.fetchval("""
            SELECT COALESCE(SUM(ticket_count), 0)
            FROM lottery_tickets 
            WHERE week_number = $1
        """, current_week) or 0
    
    await message.answer(
        f"🎫 <b>Твои билеты</b>\n\n"
        f"Текущая лотерея:\n"
        f"• У тебя: {tickets} билетов\n"
        f"• Всего продано: {total_tickets} билетов\n"
    )

async def get_current_week_number() -> str:
    now = datetime.now()
    week = now.isocalendar()[1]
    return f"{now.year}-{week}"

async def draw_lottery(bot):
    current_week = await get_current_week_number()
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        participants = await conn.fetch("""
            SELECT user_id, ticket_count 
            FROM lottery_tickets 
            WHERE week_number = $1
        """, current_week)
        
        if not participants:
            await bot.send_message(
                "@BotLudik_chanels",
                "🎟 <b>РОЗЫГРЫШ ЛОТЕРЕИ</b>\n\n"
                "В этой неделе никто не купил билеты 😢"
            )
            return
        
        tickets_pool = []
        for p in participants:
            tickets_pool.extend([p['user_id']] * p['ticket_count'])
        
        random.shuffle(tickets_pool)
        
        winners = []
        winners_pool = tickets_pool.copy()
        
        while len(winners) < 3 and winners_pool:
            winner = random.choice(winners_pool)
            
            if winner not in [w['user_id'] for w in winners]:
                place = len(winners)
                winners.append({
                    'user_id': winner,
                    'place': place,
                    'prize': PRIZES[place]
                })
            
            winners_pool = [x for x in winners_pool if x != winner]
        
        results_text = "🎟 <b>РЕЗУЛЬТАТЫ ЛОТЕРЕИ</b>\n\n"
        
        for winner in winners:
            user = await db.get_user(winner['user_id'])
            username = user.get('username') or f"id{winner['user_id']}"
            
            await db.update_balance(winner['user_id'], winner['prize'])
            
            await db.add_game_stat(
                winner['user_id'], 
                "lottery", 
                True, 
                LOTTERY_PRICE * next((p['ticket_count'] for p in participants if p['user_id'] == winner['user_id']), 1),
                winner['prize']
            )
            await update_user_status(winner['user_id'])
            await update_quest_progress(winner['user_id'], "lottery", 1)
            
            results_text += f"{PRIZE_NAMES[winner['place']]}: @{username} — {winner['prize']} LC\n"
        
        for p in participants:
            if p['user_id'] not in [w['user_id'] for w in winners]:
                await db.add_game_stat(
                    p['user_id'],
                    "lottery",
                    False,
                    p['ticket_count'] * LOTTERY_PRICE,
                    0
                )
                await update_user_status(p['user_id'])
                await update_quest_progress(p['user_id'], "lottery", 1)
        
        winners_str = ", ".join([f"@{w['user_id']}" for w in winners])
        await conn.execute("""
            INSERT INTO lottery_results (week_number, draw_date, winners, total_tickets, total_amount)
            VALUES ($1, NOW(), $2, $3, $4)
        """, current_week, winners_str, len(tickets_pool), sum(PRIZES))
        
        await conn.execute("DELETE FROM lottery_tickets WHERE week_number = $1", current_week)
    
    await bot.send_message("@BotLudik_chanels", results_text)
    return results_text
