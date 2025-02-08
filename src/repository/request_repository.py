from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import hashlib

from src.config.psql_config import PSQLConfig
from src.models.request import Request
from src.repository.base_repository import BaseRepository

class RequestRepository:
    def __init__(self):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{PSQLConfig.user}:{PSQLConfig.password}@"
            f"{PSQLConfig.host}:{PSQLConfig.port}/{PSQLConfig.database}"
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_request(self, request_id: str, command: str) -> Request:
        """Create new request"""
        async with self.async_session() as session:
            repo = BaseRepository(Request, session)
            return await repo.create(request_id=request_id, command=command)

    async def get_request(self, request_id: str) -> Request | None:
        """Get request by id"""
        async with self.async_session() as session:
            repo = BaseRepository(Request, session)
            return await repo.get(request_id=request_id)

    async def disconnect(self):
        """Close the database connection"""
        await self.engine.dispose() 

