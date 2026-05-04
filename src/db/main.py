from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from src.config import Config
from sqlmodel import SQLModel

# AsyncEngine wraps the normal engine to support await
engine = create_async_engine(
        url=Config.DATABASE_URL,   # reads from .env via config.py
        echo=True                  # prints every SQL query to terminal
)

async def initdb():
    """create our database models in the database"""

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session