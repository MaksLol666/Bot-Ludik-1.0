from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database_sqlite import db
from config import ADMIN_USERNAME

router = Router()

DONATE_TARIFFS = {
    100: 20000,
    200: 30000,
    300: 40000,
    400: 50000,
    500: 60000,
    600: 70000,
    700: 80000,
    800: 90000,
    900: 100000,
    1000: 110000
}

BUSINESS_TARIFF = 500

@router.message(Command("donate"))
async def show_donate(message: Message):
    text = "💰 <b>ДОНАТ</b>\n\n"
    text += "Пополни баланс и получи бонус!\n\n"
    text += "<b>Тарифы:</b>\n"
    
    for rub, lc in DONATE_TARIFFS.items():
        text += f"• {rub}₽ — {lc} #LC\n"
    
    text += f"\n💎 <b>Специальное предложение:</b>\n"
    text += f"• 500₽ — Богатый бизнес (50к #LC/день)\n\n"
    text += f"Для оплаты напиши админу: {ADMIN_USERNAME}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_rows = []
    for rub, lc in list(DONATE_TARIFFS.items())[:5]:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{rub}₽ → {lc} LC", 
                callback_data=f"donate_{rub}"
            )
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="💎 Бизнес 500₽", 
            callback_data="donate_business"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("donate_"))
async def process_donate(callback: CallbackQuery):
    from handlers.referral import add_referral_donat
    
    data = callback.data.replace("donate_", "")
    
    if data == "business":
        amount = 500
        biz_type = "paid"
        text = "💎 Богатый бизнес"
    else:
        amount = int(data)
        biz_type = None
    
    admin_text = (
        f"💰 <b>ЗАПРОС ДОНАТА</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {callback.from_user.id})\n"
        f"💵 Сумма: {amount}₽\n"
    )
    
    if biz_type:
        admin_text += f"🎁 Покупка: Богатый бизнес"
    
    await callback.bot.send_message(1691654877, admin_text)
    
    await callback.message.edit_text(
        f"✅ <b>Запрос отправлен!</b>\n\n"
        f"Ты выбрал: {amount}₽\n"
        f"Ожидай подтверждения от админа.\n"
        f"После оплаты напиши ему: @CIM_KAPTbI_BIO"
    )
    await callback.answer()

def process_paid_donate(admin_bot, user_id: int, amount_rub: int, is_business: bool = False):
    if is_business:
        conn = db.get_connection()
        
        cursor = conn.execute(
            "SELECT * FROM business WHERE user_id = ?",
            (user_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            return False, "У пользователя уже есть бизнес"
        
        conn.execute("""
            INSERT INTO business (user_id, business_type, last_collected)
            VALUES (?, 'paid', datetime('now'))
        """, (user_id,))
        conn.commit()
        
        # Уведомление
        # await admin_bot.send_message(...) - это асинхронно, нужно вызывать из асинхронной функции
        
        return True, "Бизнес выдан"
    else:
        if amount_rub in DONATE_TARIFFS:
            lc_amount = DONATE_TARIFFS[amount_rub]
        else:
            lc_amount = amount_rub * 200
        
        new_balance = db.update_balance(user_id, lc_amount)
        
        from handlers.referral import add_referral_donat
        referrer_id, bonus = add_referral_donat(user_id, amount_rub)
        
        text = (
            f"💰 <b>Донат зачислен!</b>\n\n"
            f"Ты получил: +{lc_amount} #LC\n"
            f"Текущий баланс: {new_balance} #LC\n\n"
            f"Спасибо за поддержку! 🎰"
        )
        
        if referrer_id:
            text += f"\n👥 Твой реферер получил бонус: +{bonus} LC"
        
        # await admin_bot.send_message(...) - асинхронно
        
        return True, f"Начислено {lc_amount} LC"
