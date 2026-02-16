from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import asyncio

from database import db
from handlers.status import update_user_status
from handlers.glc import check_win_streak
from handlers.daily_quests import update_quest_progress
from config import MIN_BET, MAX_BET
from keyboards.inline import get_back_button

router = Router()

# Карты
SUITS = ['♥️', '♦️', '♣️', '♠️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}

# Активные игры
active_poker_games = {}

class PokerStates(StatesGroup):
    waiting_for_players = State()
    betting = State()
    flop = State()
    turn = State()
    river = State()
    showdown = State()

class PokerGame:
    def __init__(self, creator_id, creator_name, bet):
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.bet = bet
        self.players = {creator_id: {'name': creator_name, 'hand': [], 'chips': bet, 'folded': False}}
        self.status = 'waiting'
        self.deck = []
        self.community_cards = []
        self.pot = 0
        self.current_player = None
        self.dealer_pos = 0
        self.small_blind = bet // 10
        self.big_blind = bet // 5
        self.game_id = None

    def create_deck(self):
        self.deck = [(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)

    def deal_card(self):
        return self.deck.pop()

    def deal_hands(self):
        for _ in range(2):
            for player_id in self.players:
                if not self.players[player_id]['folded']:
                    self.players[player_id]['hand'].append(self.deal_card())

    def deal_flop(self):
        self.community_cards = [self.deal_card() for _ in range(3)]

    def deal_turn(self):
        self.community_cards.append(self.deal_card())

    def deal_river(self):
        self.community_cards.append(self.deal_card())

    def evaluate_hand(self, hand, community):
        all_cards = hand + community
        ranks = [card[0] for card in all_cards]
        suits = [card[1] for card in all_cards]
        
        flush = any(suits.count(s) >= 5 for s in SUITS)
        
        rank_values = sorted([RANK_VALUES[r] for r in ranks])
        straight = False
        for i in range(len(rank_values)-4):
            if rank_values[i+4] - rank_values[i] == 4:
                straight = True
                break
        
        rank_counts = {r: ranks.count(r) for r in set(ranks)}
        
        if flush and straight:
            return 8
        elif 4 in rank_counts.values():
            return 7
        elif 3 in rank_counts.values() and 2 in rank_counts.values():
            return 6
        elif flush:
            return 5
        elif straight:
            return 4
        elif 3 in rank_counts.values():
            return 3
        elif list(rank_counts.values()).count(2) == 2:
            return 2
        elif 2 in rank_counts.values():
            return 1
        else:
            return 0

@router.message(F.text.lower().startswith(("покер", "poker")))
async def create_poker(message: Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Формат: покер [ставка]")
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
    
    if bet < MIN_BET * 10:
        await message.answer(f"❌ Минимальная ставка для покера: {MIN_BET * 10} LC")
        return
    
    if bet > user['balance_lc']:
        await message.answer("❌ Недостаточно средств!")
        return
    
    game = PokerGame(user_id, message.from_user.full_name, bet)
    game.game_id = f"poker_{user_id}_{message.message_id}"
    active_poker_games[game.game_id] = game
    
    await db.update_balance(user_id, -bet)
    
    from keyboards.inline import get_poker_keyboard
    await message.answer(
        f"♠️ <b>Покерная игра создана!</b>\n\n"
        f"👤 Создатель: {message.from_user.full_name}\n"
        f"💰 Ставка: {bet} LC\n"
        f"👥 Игроков: 1/6\n\n"
        f"Ждём игроков...",
        reply_markup=get_poker_keyboard(game.game_id)
    )
    
    await state.set_state(PokerStates.waiting_for_players)
    await state.update_data(game_id=game.game_id)

@router.callback_query(F.data.startswith("join_poker_"))
async def join_poker(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace("join_poker_", "")
    
    if game_id not in active_poker_games:
        await callback.answer("❌ Игра уже неактуальна", show_alert=True)
        return
    
    game = active_poker_games[game_id]
    
    if len(game.players) >= 6:
        await callback.answer("❌ Игра уже заполнена", show_alert=True)
        return
    
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Ты не зарегистрирован!", show_alert=True)
        return
    
    if user['is_banned']:
        await callback.answer("⛔ Ты забанен!", show_alert=True)
        return
    
    if game.bet > user['balance_lc']:
        await callback.answer(f"❌ Недостаточно средств! Нужно {game.bet} LC", show_alert=True)
        return
    
    game.players[user_id] = {
        'name': callback.from_user.full_name,
        'hand': [],
        'chips': game.bet,
        'folded': False
    }
    
    await db.update_balance(user_id, -game.bet)
    
    await callback.answer(f"✅ Ты присоединился к игре!", show_alert=True)
    
    if len(game.players) >= 2:
        from keyboards.inline import get_poker_start_keyboard
        await callback.message.edit_reply_markup(
            reply_markup=get_poker_start_keyboard(game_id)
        )

@router.callback_query(F.data.startswith("start_poker_"))
async def start_poker(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace("start_poker_", "")
    
    if game_id not in active_poker_games:
        await callback.answer("❌ Игра не найдена", show_alert=True)
        return
    
    game = active_poker_games[game_id]
    
    if callback.from_user.id != game.creator_id:
        await callback.answer("❌ Только создатель может начать игру", show_alert=True)
        return
    
    if len(game.players) < 2:
        await callback.answer("❌ Нужно минимум 2 игрока", show_alert=True)
        return
    
    game.status = 'playing'
    game.create_deck()
    game.deal_hands()
    game.pot = game.bet * len(game.players)
    
    player_list = list(game.players.keys())
    game.current_player = player_list[0]
    
    await show_poker_table(callback.message, game)

async def show_poker_table(message, game):
    text = f"♠️ <b>Покерный стол</b>\n\n"
    text += f"💰 Банк: {game.pot} LC\n"
    
    if game.community_cards:
        cards_str = ' '.join([f"{rank}{suit}" for rank, suit in game.community_cards])
        text += f"🃏 Стол: {cards_str}\n\n"
    
    text += "<b>Игроки:</b>\n"
    for pid, pdata in game.players.items():
        if pdata['folded']:
            status = "❌"
        elif pid == game.current_player:
            status = "👉"
        else:
            status = "✅"
        
        hand_str = ' '.join([f"{rank}{suit}" for rank, suit in pdata['hand']]) if not pdata['folded'] else "❌❌"
        text += f"{status} {pdata['name']}: {hand_str}\n"
    
    from keyboards.inline import get_poker_actions_keyboard
    await message.edit_text(text, reply_markup=get_poker_actions_keyboard(game.game_id))
