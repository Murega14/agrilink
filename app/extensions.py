# app/extensions.py
from flask_mail import Mail
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

mail = Mail()

DATABASE_URI = os.getenv('DATABASE_URI')
if not DATABASE_URI:
    raise ValueError("DATABASE URI not set")

# Convert postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URI.startswith('postgresql://'):
    DATABASE_URI = DATABASE_URI.replace('postgresql://', 'postgresql+asyncpg://')

# Updated engine configuration with correct asyncpg parameters
engine = create_async_engine(
    DATABASE_URI,
    echo=True,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "application_name": "AgriLink",
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        }
    }
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()