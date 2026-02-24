from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from keyboards.inline import get_back_button, get_glc_shop_keyboard

router = Router()

# Статусы за GLC
GLC_STATUSES = {
    # 2.500
    "dev": {"name": "Разработчик", "icon": "👨‍💻", "price": 2500},
    "smoke": {"name": "Курильщик", "icon": "🚬", "price": 2500},
    
    # 3.000
    "star": {"name": "Звезда", "icon": "⭐", "price": 3000},
    "lightning": {"name": "Молния", "icon": "⚡", "price": 3000},
    "devil": {"name": "Дьявол", "icon": "😈", "price": 3000},
    "clown": {"name": "Клоун", "icon": "🤡", "price": 3000},
    "ogre": {"name": "Огр", "icon": "👹", "price": 3000},
    
    # 5.000
    "alien": {"name": "Инопланетянин", "icon": "👾", "price": 5000},
    "eye": {"name": "Всевидящий", "icon": "👁️‍🗨️", "price": 5000},
    "speech": {"name": "Болтун", "icon": "🗨️", "price": 5000},
    "eyeball": {"name": "Глаз", "icon": "👁️", "price": 5000},
    
    # 6.500
    "globe": {"name": "Глобус", "icon": "🌐", "price": 6500},
    "watch": {"name": "Часы", "icon": "⌚", "price": 6500},
    "exchange": {"name": "Биржа", "icon": "💱", "price": 6500},
    "money": {"name": "Деньги", "icon": "💸", "price": 6500},
    "card": {"name": "Карта", "icon": "💳", "price": 6500},
    
    # 7.777
    "medal": {"name": "Медаль", "icon": "🎖️", "price": 7777},
    "moai": {"name": "Моаи", "icon": "🗿", "price": 7777},
    "coffin": {"name": "Гроб", "icon": "⚰️", "price": 7777},
    "18plus": {"name": "18+", "icon": "🔞", "price": 7777},
    
    # 10.000 - Флаги
    "belarus": {"name": "Беларусь", "icon": "🇧🇾", "price": 10000},
    "germany": {"name": "Германия", "icon": "🇩🇪", "price": 10000},
    "guatemala": {"name": "Гватемала", "icon": "🇬🇹", "price": 10000},
    "israel": {"name": "Израиль", "icon": "🇮🇱", "price": 10000},
    "kazakhstan": {"name": "Казахстан", "icon": "🇰🇿", "price": 10000},
    "russia": {"name": "Россия", "icon": "🇷🇺", "price": 10000},
    "usa": {"name": "США", "icon": "🇺🇸", "price": 10000},
    "ukraine": {"name": "Украина", "icon": "🇺🇦", "price": 10000},
    
    # 11.111
    "theater": {"name": "Театр", "icon": "🎭", "price": 11111},
    
    # 15.000
    "dollar": {"name": "Доллар", "icon": "💵", "price": 15000},
    "euro": {"name": "Евро", "icon": "💶", "price": 15000},
    "chart": {"name": "График", "icon": "📈", "price": 15000},
    
    # 25.000
    "pills": {"name": "Таблетки", "icon": "💊", "price": 25000},
    "syringe": {"name": "Шприц", "icon": "💉", "price": 25000},
    
    # 30.000
    "rose": {"name": "Роза", "icon": "🌹", "price": 30000},
    "cherry": {"name": "Сакура", "icon": "🌸", "price": 30000},
    "tulip": {"name": "Тюльпан", "icon": "🌷", "price": 30000},
    
    # 35.000
    "banana": {"name": "Банан", "icon": "🍌", "price": 35000},
    "eggplant": {"name": "Баклажан", "icon": "🍆", "price": 35000},
    "peach": {"name": "Персик", "icon": "🍑", "price": 35000},
    "cucumber": {"name": "Огурец", "icon": "🥒", "price": 35000},
    
    # 40.000
    "lobster": {"name": "Омар", "icon": "🦞", "price": 40000},
    
    # 50.000
    "watch_premium": {"name": "Премиум часы", "icon": "⌚", "price": 50000},
    
    # 66.666
    "fire": {"name": "Огонь", "icon": "🔥", "price": 66666},
    "snow": {"name": "Снег", "icon": "❄️", "price": 66666},
    
    # 77.777
    "crown": {"name": "Корона", "icon": "👑", "price": 77777},
    "diamond": {"name": "Бриллиант", "icon": "💎", "price": 77777},
    
    # 99.999
    "wilted": {"name": "Увядший цветок", "icon": "🥀", "price": 99999},
}

@router.message(Command("glc"))
async def cmd_glc(message: Message):
    """Информация о GLC"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован!")
        return
    
    owned_statuses = get_user_glc_statuses(user_id)
    
    status_text = "Твои статусы:\n"
    if owned_statuses:
        for s in owned_statuses:
            status_text += f"• {s['status_icon']} {s['status_name']}\n"
    else:
        status_text = "У тебя нет купленных статусов\n"
    
    text = (
        f"💰 <b>GLC — Премиальная валюта</b>\n\n"
        f"Твой баланс GLC: {user['balance_glc']} #GLC\n\n"
        f"{status_text}\n"
        f"<b>Как получить GLC:</b>\n"
        f"• 👥 За реферала: +100 GLC\n"
        f"• 💵 За донат: +10 GLC за каждые 10₽\n"
        f"• 📅 В ежедневном бонусе: шанс получить GLC\n"
        f"• 🔥 За серию побед (5+): +50 GLC\n\n"
        f"<b>На что потратить GLC:</b>\n"
        f"• 👑 Уникальные статусы (магазин ниже)"
    )
    
    await message.answer(text, reply_markup=get_glc_shop_keyboard())

@router.callback_query(F.data == "glc_shop")
async def glc_shop(callback: CallbackQuery):
    """Магазин статусов за GLC"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    owned = get_user_glc_statuses(user_id)
    owned_keys = [s['status_key'] for s in owned]
    
    all_statuses = list(GLC_STATUSES.items())
    pages = [all_statuses[i:i+10] for i in range(0, len(all_statuses), 10)]
    
    await show_shop_page(callback.message, user, owned_keys, pages, 0)

async def show_shop_page(message: Message, user: dict, owned_keys: list, pages: list, page: int):
    """Показать страницу магазина"""
    text = f"💰 <b>Магазин статусов</b>\n\nТвой баланс GLC: {user['balance_glc']}\n\n"
    text += f"<b>Страница {page + 1}/{len(pages)}</b>\n\n"
    
    for key, status in pages[page]:
        if key in owned_keys:
            text += f"✅ {status['icon']} {status['name']} — {status['price']} GLC (Куплено)\n"
        else:
            text += f"⬜ {status['icon']} {status['name']} — {status['price']} GLC\n"
    
    await message.edit_text(text, reply_markup=get_glc_shop_keyboard(page, len(pages)))

@router.callback_query(F.data.startswith("shop_page_"))
async def shop_page_callback(callback: CallbackQuery):
    """Переключение страниц магазина"""
    page = int(callback.data.replace("shop_page_", ""))
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    owned = get_user_glc_statuses(user_id)
    owned_keys = [s['status_key'] for s in owned]
    
    all_statuses = list(GLC_STATUSES.items())
    pages = [all_statuses[i:i+10] for i in range(0, len(all_statuses), 10)]
    
    await show_shop_page(callback.message, user, owned_keys, pages, page)
    await callback.answer()

@router.callback_query(F.data.startswith("buy_status_"))
async def buy_status(callback: CallbackQuery):
    """Покупка статуса за GLC"""
    status_key = callback.data.replace("buy_status_", "")
    user_id = callback.from_user.id
    
    if status_key not in GLC_STATUSES:
        await callback.answer("❌ Статус не найден")
        return
    
    status = GLC_STATUSES[status_key]
    user = db.get_user(user_id)
    
    if user['balance_glc'] < status['price']:
        await callback.answer(f"❌ Недостаточно GLC! Нужно {status['price']}", show_alert=True)
        return
    
    if has_glc_status(user_id, status_key):
        await callback.answer("❌ У тебя уже есть этот статус!", show_alert=True)
        return
    
    conn = db.get_connection()
    conn.execute("UPDATE users SET balance_glc = balance_glc - ? WHERE user_id = ?", (status['price'], user_id))
    conn.execute("""
        INSERT INTO glc_statuses (user_id, status_key, status_name, status_icon)
        VALUES (?, ?, ?, ?)
    """, (user_id, status_key, status['name'], status['icon']))
    conn.commit()
    
    db.log_action(user_id, "glc_shop", f"купил статус {status['name']} за {status['price']} GLC")
    
    await callback.answer(f"✅ Ты купил статус {status['icon']} {status['name']}!", show_alert=True)
    
    # Возвращаемся в магазин
    user = db.get_user(user_id)
    owned = get_user_glc_statuses(user_id)
    owned_keys = [s['status_key'] for s in owned]
    all_statuses = list(GLC_STATUSES.items())
    pages = [all_statuses[i:i+10] for i in range(0, len(all_statuses), 10)]
    await show_shop_page(callback.message, user, owned_keys, pages, 0)

@router.callback_query(F.data == "glc_info")
async def glc_info_callback(callback: CallbackQuery):
    """Возврат к информации о GLC"""
    await cmd_glc(callback.message)
    await callback.answer()

def get_user_glc_statuses(user_id: int):
    """Получить все купленные GLC статусы"""
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM glc_statuses WHERE user_id = ? ORDER BY purchased_at DESC",
        (user_id,)
    )
    return [dict(row) for row in cursor.fetchall()]

def has_glc_status(user_id: int, status_key: str) -> bool:
    """Проверяет, есть ли у пользователя конкретный статус"""
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM glc_statuses WHERE user_id = ? AND status_key = ?",
        (user_id, status_key)
    )
    return cursor.fetchone() is not None

def get_display_name_with_glc(user_id: int, username: str) -> str:
    """Получить имя со статусами"""
    from handlers.status import get_user_status
    game_status = get_user_status(user_id)
    glc_statuses = get_user_glc_statuses(user_id)
    glc_icon = glc_statuses[0]['status_icon'] if glc_statuses else ""
    
    if glc_icon and game_status:
        return f"{glc_icon} {game_status} @{username}"
    elif glc_icon:
        return f"{glc_icon} @{username}"
    elif game_status:
        return f"{game_status} @{username}"
    else:
        return f"@{username}"

def add_glc(user_id: int, amount: int, reason: str = ""):
    """Добавить GLC пользователю"""
    conn = db.get_connection()
    conn.execute("UPDATE users SET balance_glc = balance_glc + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    db.log_action(user_id, "glc", f"+{amount} | {reason}")
    return True

# ===== НОВЫЕ ФУНКЦИИ ДЛЯ REPLY КНОПОК =====

async def glc_menu_reply(message: Message):
    """Меню GLC для Reply кнопки"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован!")
        return
    
    owned_statuses = get_user_glc_statuses(user_id)
    
    status_text = "Твои статусы:\n"
    if owned_statuses:
        for s in owned_statuses:
            status_text += f"• {s['status_icon']} {s['status_name']}\n"
    else:
        status_text = "У тебя нет купленных статусов\n"
    
    text = (
        f"💰 <b>GLC — Премиальная валюта</b>\n\n"
        f"Твой баланс GLC: {user['balance_glc']} #GLC\n\n"
        f"{status_text}\n"
        f"<b>Как получить GLC:</b>\n"
        f"• 👥 За реферала: +100 GLC\n"
        f"• 💵 За донат: +10 GLC за каждые 10₽\n"
        f"• 📅 В ежедневном бонусе: шанс получить GLC\n"
        f"• 🔥 За серию побед (5+): +50 GLC\n\n"
        f"<b>На что потратить GLC:</b>\n"
        f"• 👑 Уникальные статусы (магазин ниже)"
    )
    
    from keyboards.reply import get_glc_reply_keyboard
    await message.answer(text, reply_markup=get_glc_reply_keyboard())

async def glc_shop_reply(message: Message):
    """Магазин статусов для Reply кнопки"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    owned = get_user_glc_statuses(user_id)
    owned_keys = [s['status_key'] for s in owned]
    
    all_statuses = list(GLC_STATUSES.items())
    pages = [all_statuses[i:i+10] for i in range(0, len(all_statuses), 10)]
    
    text = f"💰 <b>Магазин статусов</b>\n\nТвой баланс GLC: {user['balance_glc']}\n\n"
    text += f"<b>Страница 1/{len(pages)}</b>\n\n"
    
    for key, status in pages[0]:
        if key in owned_keys:
            text += f"✅ {status['icon']} {status['name']} — {status['price']} GLC (Куплено)\n"
        else:
            text += f"⬜ {status['icon']} {status['name']} — {status['price']} GLC\n"
    
    text += "\nДля покупки используй команду /buy_status [название]"
    
    from keyboards.reply import get_glc_reply_keyboard
    await message.answer(text, reply_markup=get_glc_reply_keyboard())
