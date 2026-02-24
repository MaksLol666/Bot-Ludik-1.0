async def show_donate_reply(message: Message):
    """Показать меню доната для Reply кнопки"""
    text = "💰 <b>ДОНАТ</b>\n\n"
    text += "Пополни баланс и получи бонус!\n\n"
    text += "<b>Тарифы:</b>\n"
    
    for rub, lc in DONATE_TARIFFS.items():
        text += f"• {rub}₽ — {lc} #LC\n"
    
    text += f"\n💎 <b>Специальное предложение:</b>\n"
    text += f"• 500₽ — Богатый бизнес (50к #LC/день)\n\n"
    text += f"Для оплаты напиши команду /donate или напиши админу: {ADMIN_USERNAME}"
    
    from keyboards.reply import get_main_menu_keyboard
    await message.answer(text, reply_markup=get_main_menu_keyboard())
