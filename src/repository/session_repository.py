from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging

from src.config.psql_config import PSQLConfig
from src.model.session import Session
from .base_repository import BaseRepository

class SessionRepository:
    def __init__(self):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{PSQLConfig.user}:{PSQLConfig.password}@"
            f"{PSQLConfig.host}:{PSQLConfig.port}/{PSQLConfig.database}"
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_session(self, session_id: str) -> Session:
        """Create new session"""
        async with self.async_session() as session:
            repo = BaseRepository(Session, session)
            return await repo.create(session_id=session_id)

    async def get_session(self, session_id: str) -> Session | None:
        """Get session by id"""
        async with self.async_session() as session:
            repo = BaseRepository(Session, session)
            return await repo.get(session_id=session_id)

    async def disconnect(self):
        """Close the database connection"""
        await self.engine.dispose()
