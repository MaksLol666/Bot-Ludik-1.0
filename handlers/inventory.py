from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from handlers.status import get_user_status, update_user_status
from keyboards.inline import get_back_button, get_inventory_keyboard

router = Router()

@router.message(Command("inventory"))
@router.callback_query(F.data == "inventory")
async def show_inventory(event: Message | CallbackQuery):
    """Показать инвентарь пользователя"""
    user_id = event.from_user.id
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        statuses = await conn.fetch("""
            SELECT * FROM user_inventory 
            WHERE user_id = $1 
            ORDER BY purchased_at DESC
        """, user_id)
        
        equipped = await conn.fetch("""
            SELECT emoji FROM user_inventory 
            WHERE user_id = $1 AND is_equipped = TRUE
        """, user_id)
    
    equipped_emojis = [e['emoji'] for e in equipped]
    
    text = f"🎒 <b>Твой инвентарь</b>\n\n"
    text += f"Всего статусов: {len(statuses)}\n"
    text += f"Экипировано: {len(equipped_emojis)}/10\n\n"
    
    if equipped_emojis:
        text += f"✨ Текущий статус: {' '.join(equipped_emojis)}\n\n"
    
    if statuses:
        text += "<b>Твои статусы:</b>\n"
        for s in statuses[:10]:
            equip_status = "✅" if s['is_equipped'] else "⭕"
            text += f"{equip_status} {s['emoji']} {s['name']} (куплен {s['purchased_at'].strftime('%d.%m.%Y')})\n"
    else:
        text += "У тебя пока нет статусов. Купи в VIP маркете!"
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_inventory_keyboard())
    else:
        await event.message.edit_text(text, reply_markup=get_inventory_keyboard())
        await event.answer()

@router.callback_query(F.data.startswith("equip_"))
async def equip_status(callback: CallbackQuery):
    """Экипировать статус"""
    emoji = callback.data.replace("equip_", "")
    user_id = callback.from_user.id
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        status = await conn.fetchrow("""
            SELECT * FROM user_inventory 
            WHERE user_id = $1 AND emoji = $2
        """, user_id, emoji)
        
        if not status:
            await callback.answer("❌ У тебя нет такого статуса!", show_alert=True)
            return
        
        equipped_count = await conn.fetchval("""
            SELECT COUNT(*) FROM user_inventory 
            WHERE user_id = $1 AND is_equipped = TRUE
        """, user_id)
        
        if equipped_count >= 10 and not status['is_equipped']:
            await callback.answer("❌ Можно экипировать максимум 10 статусов!", show_alert=True)
            return
        
        new_value = not status['is_equipped']
        await conn.execute("""
            UPDATE user_inventory 
            SET is_equipped = $1 
            WHERE user_id = $2 AND emoji = $3
        """, new_value, user_id, emoji)
        
        equipped = await conn.fetch("""
            SELECT emoji FROM user_inventory 
            WHERE user_id = $1 AND is_equipped = TRUE
            ORDER BY id
        """, user_id)
        
        new_status = ''.join([e['emoji'] for e in equipped])
        
        await conn.execute("""
            UPDATE user_status SET status = $1 WHERE user_id = $2
        """, new_status, user_id)
    
    action = "экипирован" if new_value else "снят"
    await callback.answer(f"✅ Статус {emoji} {action}!", show_alert=True)
    await show_inventory(callback)

@router.callback_query(F.data == "inventory_back")
async def inventory_back(callback: CallbackQuery):
    """Назад из инвентаря"""
    await callback.message.edit_text(
        "🎮 Главное меню:",
        reply_markup=callback.message.reply_markup
    )
    await callback.answer()
