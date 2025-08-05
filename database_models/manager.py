# /database_models/manager.py (Final, Corrected Version)

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from dotenv import load_dotenv
# --- THIS IS THE CRITICAL FIX ---
from sqlalchemy import (Column, BigInteger, DateTime, ForeignKey, Integer, JSON,
                        MetaData, Numeric, String, Table) # <-- 'Table' has been re-added to this import.
# ---------------------------------
from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine)
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

metadata = MetaData()

if not DATABASE_URL:
    logger.critical("DATABASE_URL environment variable is not set! Database connection will fail.")
    engine = None
    AsyncSessionLocal = None
else:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

# --- Table Definitions ---
users = Table(
    "users",
    metadata,
    Column("telegram_id", BigInteger, primary_key=True),
    Column("username", String, nullable=True),
    Column("phone_number", String, nullable=True, unique=True),
    Column("status", String, nullable=False, default="unregistered"),
    Column("balance", Numeric(10, 2), nullable=False, default=0.00),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)

games = Table(
    "games",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("creator_id", BigInteger, ForeignKey("users.telegram_id"), nullable=False),
    Column("opponent_id", BigInteger, ForeignKey("users.telegram_id"), nullable=True),
    Column("stake", Numeric(10, 2), nullable=False),
    Column("pot", Numeric(10, 2), nullable=False),
    Column("win_condition", Integer, nullable=False),
    Column("board_state", JSON, nullable=True),
    Column("current_turn_id", BigInteger, nullable=True),
    Column("last_action_timestamp", DateTime, nullable=True),
    Column("status", String, nullable=False, default="lobby"),
    Column("winner_id", BigInteger, ForeignKey("users.telegram_id"), nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
)

transactions = Table(
    "transactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, ForeignKey("users.telegram_id"), nullable=False),
    Column("amount", Numeric(10, 2), nullable=False),
    Column("type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("chapa_tx_ref", String, nullable=True, unique=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)

# --- Database Session Management ---
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise ConnectionError("Database is not configured. Check DATABASE_URL.")
    
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# --- Database Initialization ---
async def init_db():
    if engine is None:
        logger.error("Cannot initialize database because the engine is not available.")
        return
        
    async with engine.begin() as conn:
        logger.info("Creating all tables...")
        await conn.run_sync(metadata.create_all)
        logger.info("Database tables created successfully.")

if __name__ == "__main__":
    import asyncio
    logger.info("Running database initialization directly...")
    asyncio.run(init_db())