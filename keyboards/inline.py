from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📰 Подписаться", url="https://t.me/BotLudik_chanels"),
        InlineKeyboardButton(text="🔄 Проверить", callback_data="check_sub")
    )
    builder.row(InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"))
    return builder.as_markup()

def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Казино", callback_data="casino_menu"),
        InlineKeyboardButton(text="🎟 Лотерея", callback_data="lottery_menu")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Донат", callback_data="donate_menu"),
        InlineKeyboardButton(text="🎁 Бонус", callback_data="get_bonus")
    )
    builder.row(
        InlineKeyboardButton(text="💼 Бизнес", callback_data="business_menu"),
        InlineKeyboardButton(text="👤 Моя стата", callback_data="my_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Топы", callback_data="top_menu"),
        InlineKeyboardButton(text="🎫 Промокод", callback_data="activate_promo")
    )
    builder.row(
        InlineKeyboardButton(text="💎 VIP Маркет", callback_data="vip_market"),
        InlineKeyboardButton(text="💰 GLC", callback_data="glc_info")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Задания", callback_data="daily_quests"),
        InlineKeyboardButton(text="🏅 Достижения", callback_data="achievements")
    )
    builder.row(
        InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"),
        InlineKeyboardButton(text="👥 Рефералы", callback_data="referral_menu")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="live_stats"),
        InlineKeyboardButton(text="🚨 Жалоба", callback_data="complaint")
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")
    )
    return builder.as_markup()

def get_casino_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Рулетка", callback_data="game_roulette"),
        InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")
    )
    builder.row(
        InlineKeyboardButton(text="🎲 Кости", callback_data="game_dice"),
        InlineKeyboardButton(text="💣 Мины", callback_data="game_mines")
    )
    builder.row(
        InlineKeyboardButton(text="♠️ Покер", callback_data="game_poker"),
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="game_blackjack")
    )
    builder.row(
        InlineKeyboardButton(text="📈 Краш", callback_data="game_crash"),
        InlineKeyboardButton(text="🎲 Dice", callback_data="game_dice_game")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_business_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="20к (2.5к/день)", callback_data="buy_business_small"),
        InlineKeyboardButton(text="50к (5.5к/день)", callback_data="buy_business_medium")
    )
    builder.row(
        InlineKeyboardButton(text="100к (10.5к/день)", callback_data="buy_business_large"),
        InlineKeyboardButton(text="💎 500₽ (50к/день)", callback_data="buy_business_paid")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Собрать", callback_data="collect_business"),
        InlineKeyboardButton(text="📊 Мой бизнес", callback_data="my_business")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_vip_market_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1️⃣0️⃣0️⃣0️⃣ GLC", callback_data="vip_category_1000"),
        InlineKeyboardButton(text="2️⃣5️⃣0️⃣0️⃣ GLC", callback_data="vip_category_2500")
    )
    builder.row(
        InlineKeyboardButton(text="5️⃣0️⃣0️⃣0️⃣ GLC", callback_data="vip_category_5000"),
        InlineKeyboardButton(text="1️⃣0️⃣0️⃣0️⃣0️⃣ GLC", callback_data="vip_category_10000")
    )
    builder.row(
        InlineKeyboardButton(text="✨ Мои статусы", callback_data="my_vip_statuses")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_vip_statuses_keyboard(statuses: dict, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    sorted_statuses = sorted(statuses.items(), key=lambda x: x[1]['name'])
    
    row = []
    for i, (emoji, data) in enumerate(sorted_statuses, 1):
        row.append(InlineKeyboardButton(
            text=f"{emoji} {data['name']}", 
            callback_data=f"buy_vip_{emoji}"
        ))
        if i % 2 == 0:
            builder.row(*row)
            row = []
    
    if row:
        builder.row(*row)
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="vip_market")
    )
    
    return builder.as_markup()

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}_purchase"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{action}_purchase")
    )
    return builder.as_markup()

def get_inventory_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_daily_quests_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎁 Забрать награды", callback_data="claim_quests")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_blackjack_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎴 Взять карту", callback_data="bj_hit"),
        InlineKeyboardButton(text="✋ Остановиться", callback_data="bj_stand")
    )
    return builder.as_markup()

def get_crash_keyboard(game_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Забрать", callback_data=f"crash_cashout_{game_id}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"crash_check_{game_id}")
    )
    return builder.as_markup()

def get_poker_keyboard(game_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"join_poker_{game_id}")
    )
    return builder.as_markup()

def get_poker_start_keyboard(game_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="▶️ Начать игру", callback_data=f"start_poker_{game_id}")
    )
    return builder.as_markup()

def get_poker_actions_keyboard(game_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Чек", callback_data=f"poker_check_{game_id}"),
        InlineKeyboardButton(text="💰 Бет", callback_data=f"poker_bet_{game_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Фолд", callback_data=f"poker_fold_{game_id}")
    )
    return builder.as_markup()
