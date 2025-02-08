from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.config.psql_config import PSQLConfig
from src.models.request_result import request_result
from src.repository.base_repository import BaseRepository

class RequestResultRepository:
    def __init__(self):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{PSQLConfig.user}:{PSQLConfig.password}@"
            f"{PSQLConfig.host}:{PSQLConfig.port}/{PSQLConfig.database}"
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_relation(self, request_id: str, result_id: str) -> None:
        """Create relation between request and result"""
        async with self.async_session() as session:
            await session.execute(
                request_result.insert().values(
                    request_id=request_id,
                    result_id=result_id,
                    created_at=datetime.now()
                )
            )
            await session.commit() 