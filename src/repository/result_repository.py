from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config.psql_config import PSQLConfig
from src.models.result import Result, ResultStatus
from src.repository.base_repository import BaseRepository

class ResultRepository:
    def __init__(self):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{PSQLConfig.user}:{PSQLConfig.password}@"
            f"{PSQLConfig.host}:{PSQLConfig.port}/{PSQLConfig.database}"
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_result(self, result_id: str) -> None:
        """Save result to database"""
        async with self.async_session() as session:
            repo = BaseRepository(Result, session)
            await repo.create(
                result_id=result_id,
                status=ResultStatus.PENDING
            )
    
    async def update_status(self, result_id: str, status: ResultStatus) -> None:
        """Update result status"""
        async with self.async_session() as session:
            repo = BaseRepository(Result, session)
            await repo.update(result_id=result_id, status=status)
    
    async def update_result_path(self, result_id: str, result_path: str) -> None:
        """Update result path"""
        async with self.async_session() as session:
            repo = BaseRepository(Result, session)
            await repo.update(result_id=result_id, result_path=result_path)

    async def get_result(self, result_id: str) -> Result | None:
        """Get result by result_id"""
        async with self.async_session() as session:
            repo = BaseRepository(Result, session)
            return await repo.get(result_id=result_id)

    async def get_results_by_session(self, session_id: str) -> list[Result]:
        """Get all results for a session"""
        async with self.async_session() as session:
            repo = BaseRepository(Result, session)
            return await repo.get_all(session_id=session_id)

    async def disconnect(self):
        """Close the database connection"""
        await self.engine.dispose()
