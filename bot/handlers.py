# /bot/handlers.py (Final Version - All Features Combined)

import logging
import uuid
from decimal import Decimal
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# Import our helper functions
from .wallet import send_otp_sms, initiate_chapa_deposit

logger = logging.getLogger(__name__)

# --- 1. Define Conversation States ---
# States for Game Creation
AWAITING_STAKE, AWAITING_WIN_CONDITION = range(2)
# States for Registration & Deposit
AWAITING_PHONE_FOR_REG, AWAITING_OTP, AWAITING_DEPOSIT_AMOUNT = range(2, 5)


# --- 2. Define the Main Keyboard Layout ---
main_keyboard = [
    [KeyboardButton("Play 🎮"), KeyboardButton("Register 👤")],
    [KeyboardButton("Deposit 💰"), KeyboardButton("Withdraw 💸")],
]
REPLY_MARKUP = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)


# --- 3. Main /start Command ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main menu keyboard."""
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Please choose an option below.", 
        reply_markup=REPLY_MARKUP
    )


# --- 4. Game Creation Conversation Handlers (Preserved) ---

async def play_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the game creation conversation."""
    stake_buttons = [
        [InlineKeyboardButton("20 ETB", callback_data="stake_20"), InlineKeyboardButton("50 ETB", callback_data="stake_50")],
        [InlineKeyboardButton("Cancel", callback_data="cancel_creation")]
    ]
    await update.message.reply_text("Please select a stake amount:", reply_markup=InlineKeyboardMarkup(stake_buttons))
    return AWAITING_STAKE

async def receive_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves stake and asks for win condition."""
    query = update.callback_query
    await query.answer()
    context.user_data['stake'] = int(query.data.split('_')[1])
    win_buttons = [
        [InlineKeyboardButton("1 Token Home", callback_data="win_1"), InlineKeyboardButton("2 Tokens Home", callback_data="win_2")],
        [InlineKeyboardButton("Cancel", callback_data="cancel_creation")]
    ]
    await query.edit_message_text("How many tokens to win?", reply_markup=InlineKeyboardMarkup(win_buttons))
    return AWAITING_WIN_CONDITION

async def receive_win_condition_and_create_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves win condition and creates the game lobby."""
    query = update.callback_query
    await query.answer()
    win_condition = int(query.data.split('_')[1])
    stake = context.user_data.get('stake', 'N/A')
    user = query.from_user
    game_id = 123 # Placeholder
    join_button = [[InlineKeyboardButton("Join Game", callback_data=f"join_{game_id}")]]
    lobby_message = f"📣 Game Lobby Created!\n👤 Creator: {user.first_name}\n💰 Stake: {stake} ETB\n🏆 Win: {win_condition} token(s)"
    await query.edit_message_text(text=lobby_message, reply_markup=InlineKeyboardMarkup(join_button))
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the game creation process."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Game creation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


# --- 5. Registration & Deposit Conversation Handlers (New) ---

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the registration process."""
    await update.message.reply_text("Please send your phone number to register (e.g., 0912345678).")
    return AWAITING_PHONE_FOR_REG

async def receive_phone_for_reg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives and saves the user's phone number."""
    # TODO: Save to DB with status 'unverified'
    await update.message.reply_text("Registration successful! Please use 'Deposit' to verify your account.", reply_markup=REPLY_MARKUP)
    return ConversationHandler.END

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the deposit process, checking for verification."""
    # TODO: Fetch user status from DB
    user_status = "unverified" # Placeholder
    if user_status == "verified":
        await update.message.reply_text("Please enter the amount to deposit.")
        return AWAITING_DEPOSIT_AMOUNT
    else:
        otp_button = [[InlineKeyboardButton("Send OTP 📲", callback_data="send_otp")]]
        await update.message.reply_text("🔐 Please verify your account to continue.", reply_markup=InlineKeyboardMarkup(otp_button))
        return AWAITING_OTP

async def send_otp_callback(updat