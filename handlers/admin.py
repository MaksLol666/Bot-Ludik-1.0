from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS
from database_sqlite import db
from handlers.donate import process_paid_donate

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не админ!")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Использование: /ban user_id причина")
        return
    
    try:
        user_id = int(args[1])
        reason = args[2]
    except:
        await message.answer("❌ Неверный формат. Пример: /ban 123456789 Спам")
        return
    
    conn = db.get_connection()
    conn.execute(
        "UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?",
        (reason, user_id)
    )
    conn.commit()
    
    await message.answer(f"✅ Пользователь {user_id} забанен.\nПричина: {reason}")

@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не админ!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /unban user_id")
        return
    
    try:
        user_id = int(args[1])
    except:
        await message.answer("❌ Неверный ID")
        return
    
    conn = db.get_connection()
    conn.execute(
        "UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    
    await message.answer(f"✅ Пользователь {user_id} разбанен.")

@router.message(Command("money"))
async def cmd_money(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не админ!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Использование: /money user_id сумма")
        return
    
    try:
        user_id = int(args[1])
        amount = int(args[2])
    except:
        await message.answer("❌ Неверные числа")
        return
    
    new_balance = db.update_balance(user_id, amount)
    await message.answer(f"✅ Баланс пользователя {user_id} изменен на {amount}. Текущий: {new_balance}")

@router.message(Command("add_promo"))
async def cmd_add_promo(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не админ!")
        return
    
    args = message.text.split()
    if len(args) < 4:
        await message.answer("❌ Использование: /add_promo КОД СУММА ЛИМИТ")
        return
    
    code = args[1]
    try:
        reward = int(args[2])
        max_uses = int(args[3])
    except:
        await message.answer("❌ Сумма и лимит должны быть числами")
        return
    
    conn = db.get_connection()
    conn.execute("""
        INSERT INTO promocodes (code, reward, max_uses)
        VALUES (?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            reward = ?,
            max_uses = ?,
            used_count = 0
    """, (code, reward, max_uses, reward, max_uses))
    conn.commit()
    
    await message.answer(f"✅ Промокод {code} создан! Награда: {reward}, лимит: {max_uses}")

@router.message(Command("promolist"))
async def cmd_promolist(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не админ!")
        return
    
    conn = db.get_connection()
    cursor = conn.execute("SELECT * FROM promocodes ORDER BY used_count DESC")
    promos = cursor.fetchall()
    
    if not promos:
        await message.answer("📭 Нет промокодов")
        return
    
    text = "📋 <b>Список промокодов:</b>\n\n"
    for p in promos:
        text += f"• <code>{p[0]}</code>: {p[1]} LC | {p[3]}/{p[2]}\n"
    
    await message.answer(text)

@router.message(Command("donate_confirm"))
async def cmd_donate_confirm(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не админ!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Использование: /donate_confirm user_id сумма [business]")
        return
    
    try:
        user_id = int(args[1])
        amount = int(args[2])
        is_business = len(args) > 3 and args[3] == "business"
    except:
        await message.answer("❌ Неверный формат")
        return
    
    # Здесь нужно вызывать асинхронно
    await message.answer("✅ Донат подтвержден (заглушка)")
