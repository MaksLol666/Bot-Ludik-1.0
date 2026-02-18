from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database_sqlite import db
from keyboards.inline import get_back_button
from config import MIN_BET

router = Router()

class TransferState(StatesGroup):
    waiting_for_username = State()
    waiting_for_amount = State()

@router.message(Command("перевод"))
@router.message(F.text.lower() == "перевод")
async def cmd_transfer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован!")
        return
    
    if user['is_banned']:
        await message.answer("⛔ Ты забанен!")
        return
    
    await state.set_state(TransferState.waiting_for_username)
    await message.answer(
        "💸 <b>Перевод LC</b>\n\n"
        "Введи @username кому хочешь отправить LC:",
        reply_markup=get_back_button()
    )

@router.message(TransferState.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip()
    if username.startswith('@'):
        username = username[1:]
    
    receiver = db.get_user_by_username(username)
    
    if not receiver:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return
    
    if receiver['user_id'] == message.from_user.id:
        await message.answer("❌ Нельзя переводить самому себе")
        await state.clear()
        return
    
    await state.update_data(receiver_id=receiver['user_id'], receiver_username=username)
    await state.set_state(TransferState.waiting_for_amount)
    
    user = db.get_user(message.from_user.id)
    await message.answer(
        f"💰 Твой баланс: {user['balance_lc']} LC\n\n"
        f"Введи сумму для перевода пользователю @{username}:"
    )

@router.message(TransferState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введи число")
        return
    
    if amount < MIN_BET:
        await message.answer(f"❌ Минимальная сумма перевода: {MIN_BET} LC")
        return
    
    data = await state.get_data()
    receiver_id = data['receiver_id']
    receiver_username = data['receiver_username']
    sender_id = message.from_user.id
    
    success, msg = db.transfer_lc(sender_id, receiver_id, amount)
    
    if success:
        await message.answer(
            f"✅ <b>Перевод выполнен!</b>\n\n"
            f"Кому: @{receiver_username}\n"
            f"Сумма: {amount} LC\n\n"
            f"Спасибо за честность! 🤝"
        )
        
        # Уведомляем получателя
        try:
            await message.bot.send_message(
                receiver_id,
                f"💰 <b>Тебе перевели LC!</b>\n\n"
                f"От кого: @{message.from_user.username}\n"
                f"Сумма: +{amount} LC"
            )
        except:
            pass
    else:
        await message.answer(f"❌ {msg}")
    
    await state.clear()
