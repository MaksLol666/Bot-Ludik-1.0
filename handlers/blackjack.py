from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import random

from database_sqlite import db
from handlers.status import update_user_status
from handlers.glc import check_win_streak
from handlers.daily_quests import update_quest_progress
from config import MIN_BET, MAX_BET
from keyboards.inline import get_back_button

router = Router()

SUITS = ['♥️', '♦️', '♣️', '♠️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class BlackjackGame:
    def __init__(self, bet):
        self.bet = bet
        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        
    def create_deck(self):
        self.deck = [(rank, suit) for suit in SUITS for rank in RANKS] * 4
        random.shuffle(self.deck)
    
    def deal_card(self):
        return self.deck.pop()
    
    def hand_value(self, hand):
        value = 0
        aces = 0
        for rank, _ in hand:
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)
        
        while value > 21 and aces:
            value -= 10
            aces -= 1
        
        return value
    
    def start_game(self):
        self.create_deck()
        self.player_hand = [self.deal_card(), self.deal_card()]
        self.dealer_hand = [self.deal_card(), self.deal_card()]
    
    def player_hit(self):
        self.player_hand.append(self.deal_card())
        return self.hand_value(self.player_hand) > 21
    
    def dealer_play(self):
        while self.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deal_card())
        return self.hand_value(self.dealer_hand)

active_blackjack = {}

@router.message(F.text.lower().startswith(("бдж", "bj", "blackjack")))
async def start_blackjack(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: бдж [ставка]")
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
    
    await db.update_balance(user_id, -bet)
    
    game = BlackjackGame(bet)
    game.start_game()
    active_blackjack[user_id] = game
    
    await show_blackjack_table(message, user_id)

async def show_blackjack_table(message, user_id):
    game = active_blackjack[user_id]
    
    player_value = game.hand_value(game.player_hand)
    dealer_value = game.hand_value([game.dealer_hand[0]])
    
    player_cards = ' '.join([f"{rank}{suit}" for rank, suit in game.player_hand])
    dealer_cards = f"{game.dealer_hand[0][0]}{game.dealer_hand[0][1]} ❓"
    
    text = (
        f"🃏 <b>БЛЭКДЖЕК</b>\n\n"
        f"💰 Ставка: {game.bet} LC\n\n"
        f"👤 <b>Твои карты:</b> {player_cards}\n"
        f"📊 Сумма: {player_value}\n\n"
        f"🤵 <b>Дилер:</b> {dealer_cards}\n"
        f"📊 Сумма: {dealer_value}\n"
    )
    
    from keyboards.inline import get_blackjack_keyboard
    await message.answer(text, reply_markup=get_blackjack_keyboard())

@router.callback_query(F.data == "bj_hit")
async def blackjack_hit(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in active_blackjack:
        await callback.answer("❌ Нет активной игры!", show_alert=True)
        return
    
    game = active_blackjack[user_id]
    
    bust = game.player_hit()
    
    if bust:
        await db.add_game_stat(user_id, "blackjack", False, game.bet, 0)
        await update_user_status(user_id)
        
        await update_quest_progress(user_id, "blackjack_bets", 1)
        await update_quest_progress(user_id, "total_bets", 1)
        
        await callback.message.edit_text(
            f"💔 <b>ПЕРЕБОР!</b>\n\n"
            f"Твои карты: {' '.join([f'{r}{s}' for r,s in game.player_hand])}\n"
            f"Сумма: {game.hand_value(game.player_hand)}\n\n"
            f"Ты проиграл {game.bet} LC"
        )
        del active_blackjack[user_id]
    else:
        await show_blackjack_table(callback.message, user_id)
    
    await callback.answer()

@router.callback_query(F.data == "bj_stand")
async def blackjack_stand(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in active_blackjack:
        await callback.answer("❌ Нет активной игры!", show_alert=True)
        return
    
    game = active_blackjack[user_id]
    
    dealer_value = game.dealer_play()
    player_value = game.hand_value(game.player_hand)
    
    dealer_cards = ' '.join([f"{r}{s}" for r,s in game.dealer_hand])
    
    result_text = f"🤵 <b>Карты дилера:</b> {dealer_cards}\n📊 Сумма: {dealer_value}\n\n"
    
    if dealer_value > 21:
        win_amount = game.bet * 2
        await db.update_balance(user_id, win_amount)
        await db.add_game_stat(user_id, "blackjack", True, game.bet, win_amount)
        await update_user_status(user_id)
        await check_win_streak(user_id, "blackjack")
        await update_quest_progress(user_id, "blackjack_wins", 1)
        
        result_text += f"🎉 <b>ДИЛЕР ПЕРЕБРАЛ! Ты выиграл!</b>\n+{win_amount} LC"
    elif dealer_value > player_value:
        await db.add_game_stat(user_id, "blackjack", False, game.bet, 0)
        await update_user_status(user_id)
        
        result_text += f"💔 <b>Дилер выиграл!</b>\nТы потерял {game.bet} LC"
    elif dealer_value < player_value:
        win_amount = game.bet * 2
        await db.update_balance(user_id, win_amount)
        await db.add_game_stat(user_id, "blackjack", True, game.bet, win_amount)
        await update_user_status(user_id)
        await check_win_streak(user_id, "blackjack")
        await update_quest_progress(user_id, "blackjack_wins", 1)
        
        result_text += f"🎉 <b>Ты выиграл!</b>\n+{win_amount} LC"
    else:
        await db.update_balance(user_id, game.bet)
        result_text += f"🤝 <b>Ничья!</b>\nСтавка возвращена"
    
    await update_quest_progress(user_id, "blackjack_bets", 1)
    await update_quest_progress(user_id, "total_bets", 1)
    
    await callback.message.edit_text(
        f"🃏 <b>БЛЭКДЖЕК - РЕЗУЛЬТАТ</b>\n\n"
        f"👤 Твои карты: {' '.join([f'{r}{s}' for r,s in game.player_hand])}\n"
        f"📊 Твоя сумма: {player_value}\n\n"
        f"{result_text}"
    )
    
    del active_blackjack[user_id]
    await callback.answer()
