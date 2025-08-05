# /bot/handlers.py (Final, Perfected Version)

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

# --- Get Environment Variable ---
WEB_APP_URL = os.getenv("WEBHOOK_URL")


# --- 1. Defensively Create the Keyboard Layout ---
# This code is already perfect and prevents crashes.
keyboard_layout = []
if WEB_APP_URL:
    web_app_info = WebAppInfo(url=f"{WEB_APP_URL}/lobby/index.html")
    keyboard_layout.append(
        [KeyboardButton("Play Ludo Games 🎮", web_app=web_app_info)]
    )
else:
    logger.error("CRITICAL ERROR: WEBHOOK_URL not found! The Play button will show an error.")
    keyboard_layout.append(
        [KeyboardButton("Play 🎮 (Error: Not Configured)")]
    )
keyboard_layout.extend([
    [KeyboardButton("My Wallet 💰"), KeyboardButton("Support 📞")]
])
REPLY_MARKUP = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)


# --- 2. Define Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main menu keyboard."""
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=REPLY_MARKUP
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles data sent back from the Web App (e.g., when a user clicks 'Join')."""
    data_str = update.effective_message.web_app_data.data
    logger.info(f"Received data from Web App: {data_str}")
    
    if data_str.startswith("join_game_"):
        game_id = data_str.split('_')[-1]
        await update.message.reply_text(f"Joining game #{game_id}...")
        # TODO: Add full game joining logic here.

# --- NEW: Handler for typed "Play" message ---
async def play_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles when a user types 'Play' instead of tapping the Web App button.
    This makes the bot more user-friendly.
    """
    logger.info("User typed 'Play'. Guiding them to the Web App button.")
    await update.message.reply_text(
        "To see the game lobby, please tap the special 'Play Ludo Games 🎮' button on your keyboard below.",
        reply_markup=REPLY_MARKUP
    )


# --- 3. Define the Setup Function ---
def setup_handlers(ptb_app: Application) -> Application:
    """Attaches all handlers to the application."""
    # Add the handler for the /start command
    ptb_app.add_handler(CommandHandler("start", start_command))
    
    # Add the special handler that listens for data from our Web App
    ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # NEW: Add the handler for typed "Play" messages
    # This listens for a text message that exactly matches "Play 🎮"
    ptb_app.add_handler(MessageHandler(filters.Regex("^Play 🎮$"), play_text_handler))
    
    # TODO: You can add handlers for other text buttons ("My Wallet", etc.) here.
    
    return ptb_app