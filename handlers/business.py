from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
import datetime

from database_sqlite import db
from keyboards.inline import get_business_menu, get_back_button

router = Router()

BUSINESS_TYPES = {
    "small": {"price": 20000, "daily": 2500, "name": "Малый бизнес"},
    "medium": {"price": 50000, "daily": 5500, "name": "Средний бизнес"},
    "large": {"price": 100000, "daily": 10500, "name": "Крупный бизнес"},
    "paid": {"price": 500, "daily": 50000, "name": "💎 Богатый бизнес", "donat": True}
}

@router.callback_query(F.data == "business_menu")
async def business_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    business = cursor.fetchone()
    
    text = "💼 <b>Бизнес система</b>\n\n"
    
    if business:
        biz = BUSINESS_TYPES.get(business[1], {})
        text += f"✅ У тебя есть: {biz.get('name', 'Unknown')}\n"
        
        if business[2]:  # last_collected
            last = datetime.datetime.strptime(business[2], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            delta = now - last
            
            if delta.total_seconds() >= 86400:
                text += "💰 Доступен сбор дохода!"
            else:
                hours_left = 24 - (delta.total_seconds() / 3600)
                text += f"⏳ Следующий сбор через: {hours_left:.1f} ч."
    else:
        text += "У тебя пока нет бизнеса.\nКупи один из вариантов ниже:"
    
    await callback.message.edit_text(text, reply_markup=get_business_menu())
    await callback.answer()

@router.callback_query(F.data.startswith("buy_business_"))
async def buy_business(callback: CallbackQuery):
    biz_type = callback.data.replace("buy_business_", "")
    user_id = callback.from_user.id
    
    if biz_type not in BUSINESS_TYPES:
        await callback.answer("❌ Неверный тип бизнеса")
        return
    
    biz = BUSINESS_TYPES[biz_type]
    user = db.get_user(user_id)
    
    if biz.get("donat"):
        await callback.answer("💎 Это платный бизнес за 500₽. Используй /donate", show_alert=True)
        return
    
    if user['balance_lc'] < biz['price']:
        await callback.answer(f"❌ Недостаточно средств! Нужно {biz['price']} LC", show_alert=True)
        return
    
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    existing = cursor.fetchone()
    
    if existing:
        await callback.answer("❌ У тебя уже есть бизнес!", show_alert=True)
        return
    
    db.update_balance(user_id, -biz['price'])
    
    conn.execute("""
        INSERT INTO business (user_id, business_type, last_collected)
        VALUES (?, ?, datetime('now'))
    """, (user_id, biz_type))
    conn.commit()
    
    await callback.answer(f"✅ Бизнес '{biz['name']}' куплен!", show_alert=True)
    await business_menu(callback)

@router.callback_query(F.data == "collect_business")
async def collect_business(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    business = cursor.fetchone()
    
    if not business:
        await callback.answer("❌ У тебя нет бизнеса!", show_alert=True)
        return
    
    biz = BUSINESS_TYPES.get(business[1])
    if not biz:
        await callback.answer("❌ Ошибка бизнеса")
        return
    
    last = datetime.datetime.strptime(business[2], '%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    
    if (now - last).total_seconds() < 86400:
        await callback.answer("⏳ Еще не прошло 24 часа!", show_alert=True)
        return
    
    conn.execute(
        "UPDATE business SET last_collected = datetime('now') WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    
    db.update_balance(user_id, biz['daily'])
    
    await callback.answer(f"💰 Собрано: {biz['daily']} LC!", show_alert=True)
    await business_menu(callback)

@router.callback_query(F.data == "my_business")
async def my_business(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    business = cursor.fetchone()
    
    if not business:
        await callback.answer("❌ У тебя нет бизнеса", show_alert=True)
        return
    
    biz = BUSINESS_TYPES.get(business[1])
    last = datetime.datetime.strptime(business[2], '%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    delta = now - last
    hours_passed = delta.total_seconds() / 3600
    
    text = (
        f"💼 <b>Мой бизнес</b>\n\n"
        f"🏢 Тип: {biz['name']}\n"
        f"💰 Инвестировано: {biz['price']} LC\n"
        f"📈 Доход в день: +{biz['daily']} LC\n\n"
        f"⏱ Последний сбор: {last.strftime('%Y-%m-%d %H:%M')}\n"
        f"⌛️ Прошло: {hours_passed:.1f} ч.\n"
    )
    
    if hours_passed >= 24:
        text += "\n✅ Можно собирать доход!"
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

# ===== НОВЫЕ ФУНКЦИИ ДЛЯ REPLY КНОПОК =====

async def business_menu_reply(message: Message):
    """Меню бизнеса для Reply кнопки"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    business = cursor.fetchone()
    
    text = "💼 <b>Бизнес система</b>\n\n"
    
    if business:
        biz = BUSINESS_TYPES.get(business[1], {})
        text += f"✅ У тебя есть: {biz.get('name', 'Unknown')}\n"
        
        if business[2]:
            last = datetime.datetime.strptime(business[2], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            delta = now - last
            
            if delta.total_seconds() >= 86400:
                text += "💰 Доступен сбор дохода!"
            else:
                hours_left = 24 - (delta.total_seconds() / 3600)
                text += f"⏳ Следующий сбор через: {hours_left:.1f} ч."
    else:
        text += "У тебя пока нет бизнеса.\nКупи один из вариантов ниже:"
    
    from keyboards.reply import get_business_reply_keyboard
    await message.answer(text, reply_markup=get_business_reply_keyboard())

async def buy_business_reply(message: Message, biz_type: str):
    """Покупка бизнеса через Reply кнопку"""
    user_id = message.from_user.id
    
    if biz_type not in BUSINESS_TYPES:
        await message.answer("❌ Неверный тип бизнеса")
        return
    
    biz = BUSINESS_TYPES[biz_type]
    user = db.get_user(user_id)
    
    if biz.get("donat"):
        await message.answer("💎 Это платный бизнес за 500₽. Используй /donate")
        return
    
    if user['balance_lc'] < biz['price']:
        await message.answer(f"❌ Недостаточно средств! Нужно {biz['price']} LC")
        return
    
    conn = db.get_connection()
    
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    existing = cursor.fetchone()
    
    if existing:
        await message.answer("❌ У тебя уже есть бизнес!")
        return
    
    db.update_balance(user_id, -biz['price'])
    
    conn.execute("""
        INSERT INTO business (user_id, business_type, last_collected)
        VALUES (?, ?, datetime('now'))
    """, (user_id, biz_type))
    conn.commit()
    
    await message.answer(f"✅ Бизнес '{biz['name']}' куплен!")
    await business_menu_reply(message)

async def collect_business_reply(message: Message):
    """Сбор дохода с бизнеса через Reply кнопку"""
    user_id = message.from_user.id
    
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    business = cursor.fetchone()
    
    if not business:
        await message.answer("❌ У тебя нет бизнеса!")
        return
    
    biz = BUSINESS_TYPES.get(business[1])
    if not biz:
        await message.answer("❌ Ошибка бизнеса")
        return
    
    last = datetime.datetime.strptime(business[2], '%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    
    if (now - last).total_seconds() < 86400:
        await message.answer("⏳ Еще не прошло 24 часа!")
        return
    
    conn.execute(
        "UPDATE business SET last_collected = datetime('now') WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    
    db.update_balance(user_id, biz['daily'])
    
    await message.answer(f"💰 Собрано: {biz['daily']} LC!")
    await business_menu_reply(message)

async def my_business_reply(message: Message):
    """Информация о бизнесе через Reply кнопку"""
    user_id = message.from_user.id
    
    conn = db.get_connection()
    cursor = conn.execute(
        "SELECT * FROM business WHERE user_id = ?",
        (user_id,)
    )
    business = cursor.fetchone()
    
    if not business:
        await message.answer("❌ У тебя нет бизнеса")
        return
    
    biz = BUSINESS_TYPES.get(business[1])
    last = datetime.datetime.strptime(business[2], '%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    delta = now - last
    hours_passed = delta.total_seconds() / 3600
    
    text = (
        f"💼 <b>Мой бизнес</b>\n\n"
        f"🏢 Тип: {biz['name']}\n"
        f"💰 Инвестировано: {biz['price']} LC\n"
        f"📈 Доход в день: +{biz['daily']} LC\n\n"
        f"⏱ Последний сбор: {last.strftime('%Y-%m-%d %H:%M')}\n"
        f"⌛️ Прошло: {hours_passed:.1f} ч.\n"
    )
    
    if hours_passed >= 24:
        text += "\n✅ Можно собирать доход!"
    
    from keyboards.reply import get_business_reply_keyboard
    await message.answer(text, reply_markup=get_business_reply_keyboard())
