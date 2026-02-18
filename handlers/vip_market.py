from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from handlers.status import get_user_status, update_user_status
from handlers.achievements import check_achievement
from keyboards.inline import get_back_button, get_vip_market_keyboard

router = Router()

VIP_STATUSES = {
    "🥀": {"name": "Увядший", "price": 1000, "category": "1000"},
    "👨‍💻": {"name": "Программист", "price": 1000, "category": "1000"},
    "🚬": {"name": "Курильщик", "price": 1000, "category": "1000"},
    "⭐": {"name": "Звезда", "price": 1000, "category": "1000"},
    "⚡": {"name": "Молния", "price": 1000, "category": "1000"},
    "😈": {"name": "Демон", "price": 1000, "category": "1000"},
    
    "🤡": {"name": "Клоун", "price": 2500, "category": "2500"},
    "👹": {"name": "Огр", "price": 2500, "category": "2500"},
    "👾": {"name": "Инопланетянин", "price": 2500, "category": "2500"},
    "👁️": {"name": "Всевидящий", "price": 2500, "category": "2500"},
    
    "🌐": {"name": "Глобус", "price": 5000, "category": "5000"},
    "⌚": {"name": "Часы", "price": 5000, "category": "5000"},
    "🎖️": {"name": "Медаль", "price": 5000, "category": "5000"},
    
    "💱": {"name": "Обмен валют", "price": 10000, "category": "10000"},
    "💸": {"name": "Деньги", "price": 10000, "category": "10000"},
    "💳": {"name": "Карта", "price": 10000, "category": "10000"},
    "🗿": {"name": "Моаи", "price": 10000, "category": "10000"},
    "⚰️": {"name": "Гроб", "price": 10000, "category": "10000"},
    "🔞": {"name": "18+", "price": 10000, "category": "10000"},
    "🇧🇾": {"name": "Беларусь", "price": 10000, "category": "10000"},
    "🇩🇪": {"name": "Германия", "price": 10000, "category": "10000"},
    "🇮🇱": {"name": "Израиль", "price": 10000, "category": "10000"},
    "🇰🇿": {"name": "Казахстан", "price": 10000, "category": "10000"},
    "🇷🇺": {"name": "Россия", "price": 10000, "category": "10000"},
    "🇺🇸": {"name": "США", "price": 10000, "category": "10000"},
    "🇺🇦": {"name": "Украина", "price": 10000, "category": "10000"},
}

user_selected = {}

@router.message(Command("vip"))
@router.callback_query(F.data == "vip_market")
async def vip_market_menu(event: Message | CallbackQuery):
    """Главное меню VIP маркета"""
    user_id = event.from_user.id
    user = await db.get_user(user_id)
    
    current_status = await get_user_status(user_id)
    
    # Считаем количество купленных статусов
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        status_count = await conn.fetchval("""
            SELECT COUNT(*) FROM user_inventory WHERE user_id = $1
        """, user_id) or 0
    
    text = (
        f"💎 <b>VIP МАРКЕТ</b>\n\n"
        f"💰 Твой GLC: {user['balance_glc']}\n"
        f"✨ Твой текущий статус: {current_status or 'нет'}\n"
        f"📦 Статусов в инвентаре: {status_count}\n\n"
        f"<b>Доступные статусы:</b>\n"
        f"• 1️⃣0️⃣0️⃣0️⃣ GLC: 🥀 👨‍💻 🚬 ⭐ ⚡ 😈\n"
        f"• 2️⃣5️⃣0️⃣0️⃣ GLC: 🤡 👹 👾 👁️\n"
        f"• 5️⃣0️⃣0️⃣0️⃣ GLC: 🌐 ⌚ 🎖️\n"
        f"• 1️⃣0️⃣0️⃣0️⃣0️⃣ GLC: 💱 💸 💳 🗿 ⚰️ 🔞 и флаги\n\n"
        f"👇 Выбери категорию:"
    )
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_vip_market_keyboard())
    else:
        await event.message.edit_text(text, reply_markup=get_vip_market_keyboard())
        await event.answer()

@router.callback_query(F.data.startswith("vip_category_"))
async def show_category(callback: CallbackQuery):
    """Показать статусы определённой категории"""
    category = callback.data.replace("vip_category_", "")
    
    category_statuses = {
        emoji: data for emoji, data in VIP_STATUSES.items() 
        if data["category"] == category
    }
    
    if not category_statuses:
        await callback.answer("❌ Категория пуста")
        return
    
    from keyboards.inline import get_vip_statuses_keyboard
    await callback.message.edit_text(
        f"💎 <b>Статусы за {category} GLC</b>\n\n"
        f"Выбери статус для покупки:",
        reply_markup=get_vip_statuses_keyboard(category_statuses, category)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_vip_"))
async def buy_vip_status(callback: CallbackQuery):
    """Покупка VIP статуса"""
    emoji = callback.data.replace("buy_vip_", "")
    
    if emoji not in VIP_STATUSES:
        await callback.answer("❌ Статус не найден")
        return
    
    status_data = VIP_STATUSES[emoji]
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if user['balance_glc'] < status_data['price']:
        await callback.answer(
            f"❌ Недостаточно GLC! Нужно: {status_data['price']}, у тебя: {user['balance_glc']}",
            show_alert=True
        )
        return
    
    user_selected[user_id] = {
        'emoji': emoji,
        'name': status_data['name'],
        'price': status_data['price']
    }
    
    from keyboards.inline import get_confirm_keyboard
    await callback.message.edit_text(
        f"💎 <b>Подтверждение покупки</b>\n\n"
        f"Ты хочешь купить статус: {emoji} {status_data['name']}\n"
        f"💰 Цена: {status_data['price']} GLC\n"
        f"💳 Твой баланс: {user['balance_glc']} GLC\n\n"
        f"Подтверждаешь?",
        reply_markup=get_confirm_keyboard("vip")
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_vip_purchase")
async def confirm_vip_purchase(callback: CallbackQuery):
    """Подтверждение покупки VIP статуса"""
    user_id = callback.from_user.id
    
    if user_id not in user_selected:
        await callback.answer("❌ Нет активной покупки")
        return
    
    selected = user_selected[user_id]
    user = await db.get_user(user_id)
    
    if user['balance_glc'] < selected['price']:
        await callback.answer("❌ Недостаточно GLC!", show_alert=True)
        del user_selected[user_id]
        return
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET balance_glc = balance_glc - $1 WHERE user_id = $2
        """, selected['price'], user_id)
        
        await conn.execute("""
            INSERT INTO user_inventory (user_id, emoji, name, price, is_equipped)
            VALUES ($1, $2, $3, $4, TRUE)
        """, user_id, selected['emoji'], selected['name'], selected['price'])
        
        equipped = await conn.fetch("""
            SELECT emoji FROM user_inventory 
            WHERE user_id = $1 AND is_equipped = TRUE
            ORDER BY id
        """, user_id)
        
        new_status = ''.join([e['emoji'] for e in equipped])
        
        await conn.execute("""
            UPDATE user_status SET status = $1 WHERE user_id = $2
        """, new_status, user_id)
    
    # Проверяем достижение коллекционера
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        status_count = await conn.fetchval("""
            SELECT COUNT(*) FROM user_inventory WHERE user_id = $1
        """, user_id) or 0
    
    await check_achievement(user_id, "collector", status_count)
    
    del user_selected[user_id]
    
    await callback.message.edit_text(
        f"✅ <b>Покупка успешна!</b>\n\n"
        f"Ты приобрёл статус: {selected['emoji']} {selected['name']}\n"
        f"💰 Потрачено: {selected['price']} GLC\n"
        f"✨ Твой новый статус: {new_status}\n\n"
        f"Теперь он будет отображаться рядом с твоим ником!",
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_vip_purchase")
async def cancel_vip_purchase(callback: CallbackQuery):
    """Отмена покупки"""
    user_id = callback.from_user.id
    if user_id in user_selected:
        del user_selected[user_id]
    
    await vip_market_menu(callback)
    await callback.answer()

@router.callback_query(F.data == "my_vip_statuses")
async def my_vip_statuses(callback: CallbackQuery):
    """Мои купленные статусы"""
    from handlers.inventory import show_inventory
    await show_inventory(callback)
