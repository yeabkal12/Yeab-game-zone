# app.py (The Final, Complete, and Perfected Version)

import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles  # <-- CRITICAL: For serving the web app
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter

# --- Make sure all necessary components are imported ---
from bot.handlers import setup_handlers
from database_models.manager import get_db_session, games, users
from sqlalchemy import select

# --- 1. Setup & Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# --- 2. Global Application Instances ---
bot_app: Application | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles critical startup and shutdown events for the application."""
    logger.info("Application startup...")
    if bot_app:
        await bot_app.initialize()
        if WEBHOOK_URL:
            webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
            try:
                await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
                logger.info(f"Successfully set webhook to: {webhook_full_url}")
            except RetryAfter:
                logger.warning("Could not set webhook due to flood control. Another worker likely succeeded.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while setting webhook: {e}")
        else:
            logger.error("FATAL: WEBHOOK_URL environment variable is not set!")
    
    yield  # --- The application is now running ---
    
    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()


# --- 3. Main FastAPI Application Initialization ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

if not TELEGRAM_BOT_TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot will be disabled.")
else:
    ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = setup_handlers(ptb_application)
    logger.info("Telegram bot application created and handlers have been attached.")


# --- 4. API Endpoints ---
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Main webhook to receive updates from Telegram."""
    if not bot_app:
        return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return Response(status_code=500)

# --- THIS IS THE CRITICAL ENDPOINT THAT WAS MISSING ---
@app.get("/api/games")
async def get_open_games():
    """Endpoint for the web app to fetch open game lobbies."""
    live_games = []
    try:
        async with get_db_session() as session:
            stmt = select(games.c.id, games.c.stake, games.c.pot, users.c.username).\
                   join(users, games.c.creator_id == users.c.telegram_id).\
                   where(games.c.status == 'lobby').order_by(games.c.created_at.desc())
            result = await session.execute(stmt)
            for row in result.fetchall():
                live_games.append({
                    "id": row.id,
                    "creator_name": row.username or "Player",
                    "creator_avatar": f"https://i.pravatar.cc/40?u={row.id}",
                    "stake": float(row.stake),
                    "prize": float(row.pot * 0.9),
                })
    except Exception as e:
        logger.error(f"Failed to fetch open games from database: {e}")
        return {"games": []}
    return {"games": live_games}

@app.get("/health")
async def health_check():
    """A simple health check endpoint for Render."""
    return {"status": "healthy"}


# --- 5. Mount Static Files for Web App ---
# This line tells FastAPI to serve the files from your 'frontend' folder.
app.mount("/", StaticFiles(directory="frontend"), name="frontend")