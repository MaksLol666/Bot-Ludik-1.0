from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

from config import CHANNEL_ID, CHANNEL_LINK, ADMIN_USERNAME, BOT_VERSION, BOT_RELEASE_DATE
from database_sqlite import db
from keyboards.inline import get_start_keyboard, get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name
    
    # Обработка реферальной ссылки
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id == user_id:
                referrer_id = None
        except:
            referrer_id = None
    
    user = db.get_user(user_id)
    if not user:
        db.create_user(user_id, username, first_name, referrer_id)
        
        welcome_text = (
            f"🎰 <b>Добро пожаловать в Лудик {BOT_VERSION}!</b>\n\n"
            f"Привет, {first_name}!\n"
            f"Мир азарта и больших выигрышей ждет тебя! 🎲\n\n"
            f"👑 Владелец: {ADMIN_USERNAME}\n"
            f"📅 Релиз: {BOT_RELEASE_DATE}\n"
            f"📊 Версия: {BOT_VERSION}\n\n"
            f"👇 Выбери действие в меню ниже:"
        )
        
        try:
            chat_member = await message.bot.get_chat_member(CHANNEL_ID, user_id)
            if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                await message.answer(
                    f"🔒 <b>Для доступа к играм нужно подписаться на канал!</b>\n\n"
                    f"👉 {CHANNEL_LINK}\n\n"
                    f"После подписки нажми /play",
                    reply_markup=get_start_keyboard()
                )
            else:
                await message.answer(welcome_text, reply_markup=get_main_menu())
        except:
            await message.answer(welcome_text, reply_markup=get_main_menu())
    else:
        if user['is_banned']:
            await message.answer(
                f"⛔ <b>Вы заблокированы!</b>\n\n"
                f"Причина: {user['ban_reason']}\n"
                f"Для разблокировки обратитесь к {ADMIN_USERNAME}"
            )
            return
        
        await message.answer(
            f"🎲 <b>С возвращением, {first_name}!</b>\n\n"
            f"💰 Твой баланс: {user['balance_lc']} #LC",
            f"💎 GLC: {user['balance_glc']}",
            reply_markup=get_main_menu()
        )

# ... остальной код без изменений ...

@router.message(Command("play"))
async def cmd_play(message: Message):
    user_id = message.from_user.id
    
    user = await db.get_user(user_id)
    if user and user['is_banned']:
        await message.answer(f"⛔ Вы заблокированы!")
        return
    
    try:
        chat_member = await message.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            await message.answer(
                f"🔒 <b>Ты не подписан на канал!</b>\n\n"
                f"👉 {CHANNEL_LINK}",
                reply_markup=get_start_keyboard()
            )
        else:
            await message.answer("🎮 Игровой зал:", reply_markup=get_main_menu())
    except:
        await message.answer("🎮 Игровой зал:", reply_markup=get_main_menu())

@router.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    info_text = (
        f"<b>Информация о боте \"Лудик {BOT_VERSION}\"</b>\n\n"
        f"👑 <b>Владелец:</b> {ADMIN_USERNAME}\n"
        f"📅 <b>Релиз:</b> {BOT_RELEASE_DATE}\n"
        f"📊 <b>Версия:</b> {BOT_VERSION}\n"
        f"💬 <b>Чат:</b> {CHAT_LINK}\n\n"
        f"⚠️ <b>ВНИМАНИЕ:</b>\n"
        f"• Денежные средства не возвращаются.\n"
        f"• Вывод средств не предусмотрен.\n"
        f"• Играйте ответственно!"
    )
    await callback.message.edit_text(info_text, reply_markup=get_start_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("🎮 Главное меню:", reply_markup=get_main_menu())
    await callback.answer()

@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        chat_member = await callback.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            await callback.answer("❌ Ты все еще не подписан!", show_alert=True)
        else:
            await callback.answer("✅ Подписка подтверждена! Игры доступны.", show_alert=True)
            await callback.message.edit_text("🎮 Игровой зал:", reply_markup=get_main_menu())
    except:
        await callback.answer("❌ Ошибка проверки", show_alert=True)
