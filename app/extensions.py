from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncpg
import os
from flask_mail import Mail
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

mail = Mail()

DATABASE_URI = os.getenv('DATABASE_URI')
if not DATABASE_URI:
    raise ValueError("DATABASE URI not set")

# Convert to asyncpg connection string format
if DATABASE_URI.startswith('postgresql://'):
    DATABASE_URI = DATABASE_URI.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine with enhanced pool configuration
engine = create_async_engine(
    DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
)

# Async session maker
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def initialize_database():
    try:
        db_params = parse_database_uri(DATABASE_URI)
        
        pool = await asyncpg.create_pool(
            host=db_params['host'],
            port=db_params.get('port', 5432),
            user=db_params['user'],
            password=db_params['password'],
            database=db_params['database'],
            min_size=5,
            max_size=10,
            max_queries=10000,
            max_inactive_connection_lifetime=180.0,
            statement_cache_size=0
        )
        
        await verify_connection_pool(pool)
        
        logger.info("Database connection pool initialized successfully")
        return pool
    
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        raise

async def verify_connection_pool(pool):
    """
    Verify the functionality of the connection pool
    """
    try:
        async with pool.acquire() as conn:
            # Simple health check query
            await conn.fetchval("SELECT 1")
        
        # Log pool status
        logger.info(f"Connection Pool Status:")
        logger.info(f"Current Size: {pool.get_size()}")
        logger.info(f"Idle Connections: {pool.get_idle_size()}")
    
    except Exception as e:
        logger.error(f"Connection pool verification failed: {e}")
        raise

def parse_database_uri(uri):
    """
    Parse database URI into components for asyncpg connection
    """
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(uri)
    
    params = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
    }
    
    if parsed.query:
        params.update(parse_qs(parsed.query))
    
    return params

@asynccontextmanager
async def get_db():
    """
    Async context manager for database sessions with enhanced error handling
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def monitor_connection_pool(pool):
    """
    Background task to periodically log connection pool status
    """
    while True:
        try:
            logger.info(f"Connection Pool Status:")
            logger.info(f"Current Size: {pool.get_size()}")
            logger.info(f"Idle Connections: {pool.get_idle_size()}")
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Pool monitoring error: {e}")
            break