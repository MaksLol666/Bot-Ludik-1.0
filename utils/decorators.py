from functools import wraps
from aiogram.types import Message, CallbackQuery
from config import CHANNEL_ID, ADMIN_IDS
from aiogram.enums import ChatMemberStatus

def check_subscription():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            event = args[0]
            bot = event.bot
            
            if isinstance(event, (Message, CallbackQuery)):
                user_id = event.from_user.id
                
                try:
                    chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
                    
                    if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                        text = "🔒 Для доступа к этой функции нужно подписаться на канал!"
                        
                        if isinstance(event, Message):
                            await event.answer(text)
                        else:
                            await event.answer(text, show_alert=True)
                        return
                except:
                    pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def admin_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            event = args[0]
            
            user_id = event.from_user.id
            
            if user_id not in ADMIN_IDS:
                text = "⛔ Эта команда только для администратора!"
                
                if isinstance(event, Message):
                    await event.answer(text)
                else:
                    await event.answer(text, show_alert=True)
                return
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
