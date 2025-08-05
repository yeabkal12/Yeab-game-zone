# /database_models/manager.py (Final, Perfected Version with Driver Fix)

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import (Column, BigInteger, DateTime, ForeignKey, Integer, JSON,
                        MetaData, Numeric, String, Table)
from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine)
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
load_dotenv()

# --- 1. Get and Correct the Database URL ---
DATABASE_URL = os.getenv("DATABASE_URL")

# THIS IS THE FINAL, CRITICAL FIX:
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # SQLAlchemy's async engine needs the URL to specify the 'asyncpg' driver.
    # We replace the beginning of the URL to ensure the correct driver is used.
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    logger.info("Database URL has been adapted for asyncpg driver.")


# --- 2. Database Engine & Metadata ---
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

# --- 3. Table Definitions (No changes needed) ---
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
# ... (rest of your tables: games, transactions) ...

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

# --- 4. Database Session Management (No changes needed) ---
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise ConnectionError("Database is not configured.")
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# --- 5. Database Initialization (No changes needed) ---
async def init_db():
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        logger.info("Database tables created successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())