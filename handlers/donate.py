from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from config import ADMIN_USERNAME, ADMIN_IDS
from handlers.referral import add_referral_donat
from handlers.live_stats import track_donation
from handlers.achievements import check_achievement

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
    
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(admin_id, admin_text)
        except:
            pass
    
    await callback.message.edit_text(
        f"✅ <b>Запрос отправлен!</b>\n\n"
        f"Ты выбрал: {amount}₽\n"
        f"Ожидай подтверждения от админа.\n"
        f"После оплаты напиши ему: {ADMIN_USERNAME}"
    )
    await callback.answer()

async def process_paid_donate(admin_bot, user_id: int, amount_rub: int, is_business: bool = False):
    if is_business:
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT * FROM business WHERE user_id = $1",
                user_id
            )
            
            if existing:
                return False, "У пользователя уже есть бизнес"
            
            await conn.execute("""
                INSERT INTO business (user_id, business_type, last_collected)
                VALUES ($1, 'paid', NOW())
            """, user_id)
        
        await admin_bot.send_message(
            user_id,
            "💎 <b>Тебе выдан Богатый бизнес!</b>\n\n"
            "Ты будешь получать по 50к #LC каждый день!"
        )
        
        await track_donation(user_id, amount_rub)
        await check_achievement(user_id, "supporter", 1)
        
        return True, "Бизнес выдан"
    else:
        if amount_rub in DONATE_TARIFFS:
            lc_amount = DONATE_TARIFFS[amount_rub]
        else:
            lc_amount = amount_rub * 200
        
        new_balance = await db.update_balance(user_id, lc_amount)
        
        glc_amount = (amount_rub // 10) * 10
        if glc_amount > 0:
            from handlers.glc import add_glc
            await add_glc(user_id, glc_amount, f"Donate {amount_rub}₽")
        
        referrer_id, bonus = await add_referral_donat(user_id, amount_rub)
        
        text = (
            f"💰 <b>Донат зачислен!</b>\n\n"
            f"Ты получил: +{lc_amount} #LC\n"
            f"💎 GLC: +{glc_amount}\n"
            f"Текущий баланс: {new_balance} #LC\n\n"
            f"Спасибо за поддержку! 🎰"
        )
        
        if referrer_id:
            text += f"\n👥 Твой реферер получил бонус: +{bonus} LC"
        
        await admin_bot.send_message(user_id, text)
        
        await track_donation(user_id, amount_rub)
        await check_achievement(user_id, "supporter", 1)
        
        # Проверка на кита
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            total_donated = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0) FROM donations WHERE user_id = $1
            """, user_id) or 0
        
        await check_achievement(user_id, "whale", total_donated)
        
        return True, f"Начислено {lc_amount} LC и {glc_amount} GLC"
