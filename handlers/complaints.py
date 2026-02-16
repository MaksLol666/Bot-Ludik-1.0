from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from config import ADMIN_IDS
from keyboards.inline import get_back_button

router = Router()

class ComplaintState(StatesGroup):
    waiting_for_id = State()
    waiting_for_reason = State()

@router.message(Command("complaint"))
async def complaint_start(message: Message, state: FSMContext):
    """Начать жалобу"""
    await message.answer(
        "🚨 <b>Система жалоб</b>\n\n"
        "Введи ID пользователя, на которого хочешь пожаловаться:",
        reply_markup=get_back_button()
    )
    await state.set_state(ComplaintState.waiting_for_id)

@router.message(ComplaintState.waiting_for_id)
async def complaint_get_id(message: Message, state: FSMContext):
    """Получить ID нарушителя"""
    try:
        accused_id = int(message.text)
    except:
        await message.answer("❌ Введите корректный ID!")
        return
    
    if accused_id == message.from_user.id:
        await message.answer("❌ Нельзя жаловаться на самого себя!")
        return
    
    await state.update_data(accused_id=accused_id)
    await message.answer(
        "📝 Опиши причину жалобы (максимум 200 символов):"
    )
    await state.set_state(ComplaintState.waiting_for_reason)

@router.message(ComplaintState.waiting_for_reason)
async def complaint_get_reason(message: Message, state: FSMContext):
    """Получить причину жалобы"""
    reason = message.text[:200]
    
    data = await state.get_data()
    accused_id = data['accused_id']
    complainant_id = message.from_user.id
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        complaint_id = await conn.fetchval("""
            INSERT INTO complaints (complainant_id, accused_id, reason)
            VALUES ($1, $2, $3)
            RETURNING id
        """, complainant_id, accused_id, reason)
        
        accused = await db.get_user(accused_id)
        complainant = await db.get_user(complainant_id)
    
    admin_text = (
        f"🚨 <b>НОВАЯ ЖАЛОБА #{complaint_id}</b>\n\n"
        f"👤 От: @{message.from_user.username} (ID: {complainant_id})\n"
        f"👤 На: @{accused['username'] if accused else 'Unknown'} (ID: {accused_id})\n"
        f"📝 Причина: {reason}\n\n"
        f"<b>Действия:</b>\n"
        f"/resolve_complaint {complaint_id} — пометить как решённую\n"
        f"/reject_complaint {complaint_id} — отклонить"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_text)
        except:
            pass
    
    await message.answer(
        "✅ Жалоба отправлена администратору!\n"
        "Ожидай рассмотрения."
    )
    await state.clear()

@router.message(Command("resolve_complaint"))
async def resolve_complaint(message: Message):
    """Пометить жалобу как решённую (только админ)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        complaint_id = int(message.text.split()[1])
    except:
        await message.answer("❌ Формат: /resolve_complaint [ID]")
        return
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE complaints 
            SET status = 'reviewed', reviewed_at = NOW(), reviewed_by = $1
            WHERE id = $2
        """, message.from_user.id, complaint_id)
    
    await message.answer(f"✅ Жалоба #{complaint_id} помечена как решённая")

@router.message(Command("reject_complaint"))
async def reject_complaint(message: Message):
    """Отклонить жалобу (только админ)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        complaint_id = int(message.text.split()[1])
    except:
        await message.answer("❌ Формат: /reject_complaint [ID]")
        return
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE complaints 
            SET status = 'rejected', reviewed_at = NOW(), reviewed_by = $1
            WHERE id = $2
        """, message.from_user.id, complaint_id)
    
    await message.answer(f"✅ Жалоба #{complaint_id} отклонена")

@router.message(Command("complaints"))
async def list_complaints(message: Message):
    """Список активных жалоб (только админ)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        complaints = await conn.fetch("""
            SELECT * FROM complaints WHERE status = 'pending' ORDER BY created_at DESC
        """)
    
    if not complaints:
        await message.answer("📭 Нет активных жалоб")
        return
    
    text = "🚨 <b>Активные жалобы:</b>\n\n"
    for c in complaints[:10]:
        text += f"#{c['id']} от {c['created_at'].strftime('%d.%m %H:%M')}\n"
        text += f"👤 На ID: {c['accused_id']}\n"
        text += f"📝 {c['reason'][:50]}...\n\n"
    
    await message.answer(text)
