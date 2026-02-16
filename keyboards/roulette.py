from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_roulette_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Играть в рулетку", callback_data="play_roulette")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="casino_menu")
    )
    return builder.as_markup()

def get_roulette_bet_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔴 Красное", callback_data="roulette_bet_red"),
        InlineKeyboardButton(text="⚫ Чёрное", callback_data="roulette_bet_black"),
        InlineKeyboardButton(text="🟢 0", callback_data="roulette_bet_0")
    )
    builder.row(
        InlineKeyboardButton(text="1-18", callback_data="roulette_bet_1_18"),
        InlineKeyboardButton(text="19-36", callback_data="roulette_bet_19_36")
    )
    builder.row(
        InlineKeyboardButton(text="Чёт", callback_data="roulette_bet_even"),
        InlineKeyboardButton(text="Нечёт", callback_data="roulette_bet_odd")
    )
    builder.row(
        InlineKeyboardButton(text="1-12", callback_data="roulette_bet_1_12"),
        InlineKeyboardButton(text="13-24", callback_data="roulette_bet_13_24"),
        InlineKeyboardButton(text="25-36", callback_data="roulette_bet_25_36")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 1 ряд", callback_data="roulette_bet_column_1"),
        InlineKeyboardButton(text="📊 2 ряд", callback_data="roulette_bet_column_2"),
        InlineKeyboardButton(text="📊 3 ряд", callback_data="roulette_bet_column_3")
    )
    
    builder.row(
        InlineKeyboardButton(text="1-3", callback_data="roulette_bet_street_1"),
        InlineKeyboardButton(text="4-6", callback_data="roulette_bet_street_2"),
        InlineKeyboardButton(text="7-9", callback_data="roulette_bet_street_3")
    )
    builder.row(
        InlineKeyboardButton(text="10-12", callback_data="roulette_bet_street_4"),
        InlineKeyboardButton(text="13-15", callback_data="roulette_bet_street_5"),
        InlineKeyboardButton(text="16-18", callback_data="roulette_bet_street_6")
    )
    builder.row(
        InlineKeyboardButton(text="19-21", callback_data="roulette_bet_street_7"),
        InlineKeyboardButton(text="22-24", callback_data="roulette_bet_street_8"),
        InlineKeyboardButton(text="25-27", callback_data="roulette_bet_street_9")
    )
    builder.row(
        InlineKeyboardButton(text="28-30", callback_data="roulette_bet_street_10"),
        InlineKeyboardButton(text="31-33", callback_data="roulette_bet_street_11"),
        InlineKeyboardButton(text="34-36", callback_data="roulette_bet_street_12")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="game_roulette")
    )
    
    return builder.as_markup()
