import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database_sqlite import db
from handlers.status import update_user_status
from config import MIN_BET, MAX_BET

router = Router()

# Значения карт
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

CARDS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♥️', '♦️', '♣️', '♠️']

class BlackjackStates(StatesGroup):
    playing = State()

def create_deck():
    """Создание колоды"""
    deck = []
    for suit in SUITS:
        for card in CARDS:
            deck.append(f"{card}{suit}")
    random.shuffle(deck)
    return deck

def calculate_hand(hand):
    """Подсчет очков в руке"""
    total = 0
    aces = 0
    for card in hand:
        value = card[:-1]  # убираем масть
        if value == 'A':
            aces += 1
            total += 11
        else:
            total += CARD_VALUES[value]
    
    # Если перебор и есть тузы, меняем 11 на 1
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    
    return total

def hand_to_string(hand):
    """Преобразование руки в строку"""
    return ' '.join(hand)

@router.message(F.text.lower().startswith("бджек"))
@router.message(F.text.lower().startswith("blackjack"))
async def start_blackjack(message: Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: бджек [ставка]")
        return
    
    try:
        bet = int(parts[1])
    except:
        await message.answer("❌ Ставка должна быть числом")
        return
    
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован! Напиши /start")
        return
    
    if user['is_banned']:
        await message.answer("⛔ Ты забанен!")
        return
    
    if bet < MIN_BET:
        await message.answer(f"❌ Минимальная ставка: {MIN_BET} LC")
        return
    
    if bet > user['balance_lc']:
        await message.answer("❌ Недостаточно средств!")
        return
    
    if bet > MAX_BET:
        await message.answer(f"❌ Максимальная ставка: {MAX_BET} LC")
        return
    
    # Списываем ставку
    await db.update_balance(user_id, -bet)
    
    # Создаем игру
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    player_score = calculate_hand(player_hand)
    dealer_score = calculate_hand([dealer_hand[0]])  # только первая карта дилера
    
    # Проверка на блэкджек
    if player_score == 21:
        # Блэкджек у игрока
        win_amount = int(bet * 2.5)
        await db.update_balance(user_id, win_amount)
        await db.add_game_stat(user_id, "blackjack", True, bet, win_amount)
        await update_user_status(user_id)
        
        await message.answer(
            f"🃏 <b>БЛЭКДЖЕК!</b>\n\n"
            f"Твои карты: {hand_to_string(player_hand)} (21)\n"
            f"Карты дилера: {hand_to_string(dealer_hand)} ({calculate_hand(dealer_hand)})\n\n"
            f"💰 Выигрыш: +{win_amount} LC"
        )
        return
    
    # Сохраняем состояние
    await state.set_state(BlackjackStates.playing)
    await state.update_data(
        bet=bet,
        deck=deck,
        player_hand=player_hand,
        dealer_hand=dealer_hand
    )
    
    # Показываем клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Еще", callback_data="bj_hit"),
         InlineKeyboardButton(text="⏹ Хватит", callback_data="bj_stand")]
    ])
    
    await message.answer(
        f"🃏 <b>Блэкджек</b>\n\n"
        f"Твои карты: {hand_to_string(player_hand)} ({player_score})\n"
        f"Карты дилера: {hand_to_string([dealer_hand[0]])} + ?\n\n"
        f"💰 Ставка: {bet} LC",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("bj_"), BlackjackStates.playing)
async def blackjack_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("bj_", "")
    data = await state.get_data()
    
    bet = data['bet']
    deck = data['deck']
    player_hand = data['player_hand']
    dealer_hand = data['dealer_hand']
    user_id = callback.from_user.id
    
    if action == "hit":
        # Игрок берет карту
        player_hand.append(deck.pop())
        player_score = calculate_hand(player_hand)
        
        if player_score > 21:
            # Перебор - игрок проиграл
            await db.add_game_stat(user_id, "blackjack", False, bet, 0)
            await update_user_status(user_id)
            
            await callback.message.edit_text(
                f"💔 <b>ПЕРЕБОР!</b>\n\n"
                f"Твои карты: {hand_to_string(player_hand)} ({player_score})\n"
                f"Карты дилера: {hand_to_string(dealer_hand)} ({calculate_hand(dealer_hand)})\n\n"
                f"💰 Потеряно: {bet} LC"
            )
            await state.clear()
            await callback.answer()
            return
        
        # Обновляем состояние
        await state.update_data(player_hand=player_hand, deck=deck)
        
        # Показываем обновленную руку
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Еще", callback_data="bj_hit"),
             InlineKeyboardButton(text="⏹ Хватит", callback_data="bj_stand")]
        ])
        
        await callback.message.edit_text(
            f"🃏 <b>Блэкджек</b>\n\n"
            f"Твои карты: {hand_to_string(player_hand)} ({player_score})\n"
            f"Карты дилера: {hand_to_string([dealer_hand[0]])} + ?\n\n"
            f"💰 Ставка: {bet} LC",
            reply_markup=keyboard
        )
        await callback.answer()
        
    elif action == "stand":
        # Игрок останавливается - ходит дилер
        player_score = calculate_hand(player_hand)
        dealer_score = calculate_hand(dealer_hand)
        
        # Дилер берет карты пока не наберет 17+
        while dealer_score < 17:
            dealer_hand.append(deck.pop())
            dealer_score = calculate_hand(dealer_hand)
        
        # Определяем результат
        if dealer_score > 21:
            # Дилер перебрал - игрок выиграл
            win_amount = bet * 2
            await db.update_balance(user_id, win_amount)
            await db.add_game_stat(user_id, "blackjack", True, bet, win_amount)
            result_text = f"🎉 <b>Ты выиграл! Дилер перебрал</b>\n\n+{win_amount} LC"
        elif dealer_score > player_score:
            # Дилер выиграл
            await db.add_game_stat(user_id, "blackjack", False, bet, 0)
            result_text = f"💔 <b>Дилер выиграл</b>\n\n💰 Потеряно: {bet} LC"
        elif dealer_score < player_score:
            # Игрок выиграл
            win_amount = bet * 2
            await db.update_balance(user_id, win_amount)
            await db.add_game_stat(user_id, "blackjack", True, bet, win_amount)
            result_text = f"🎉 <b>Ты выиграл!</b>\n\n+{win_amount} LC"
        else:
            # Ничья - возврат ставки
            await db.update_balance(user_id, bet)
            await db.add_game_stat(user_id, "blackjack", False, bet, 0)
            result_text = f"🤝 <b>Ничья</b>\n\n💰 Ставка возвращена: {bet} LC"
        
        await update_user_status(user_id)
        
        await callback.message.edit_text(
            f"🃏 <b>Блэкджек</b>\n\n"
            f"Твои карты: {hand_to_string(player_hand)} ({player_score})\n"
            f"Карты дилера: {hand_to_string(dealer_hand)} ({dealer_score})\n\n"
            f"{result_text}"
        )
        await state.clear()
        await callback.answer()
