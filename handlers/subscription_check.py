from aiogram import Router
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from functools import wraps

from config import CHANNEL_ID, CHANNEL_LINK
from database_sqlite import db

router = Router()

async def check_subscription(bot, user_id: int) -> bool:
    """Проверяет подписку пользователя на канал"""
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except:
        return False

def require_subscription():
    """Декоратор для проверки подписки перед игрой"""
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            user_id = message.from_user.id
            user = db.get_user(user_id)
            
            # Проверяем, зарегистрирован ли пользователь
            if not user:
                await message.answer("❌ Ты не зарегистрирован! Напиши /start")
                return
            
            # Проверяем, не забанен ли пользователь
            if user['is_banned']:
                await message.answer("⛔ Ты забанен!")
                return
            
            # Проверяем подписку
            is_subscribed = await check_subscription(message.bot, user_id)
            
            if not is_subscribed:
                await message.answer(
                    f"🔒 <b>Для доступа к играм нужно подписаться на канал!</b>\n\n"
                    f"👉 {CHANNEL_LINK}\n\n"
                    f"После подписки нажми /play"
                )
                return
            
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator
