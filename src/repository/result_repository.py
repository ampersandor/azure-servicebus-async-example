from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config.psql_config import PSQLConfig
from src.model.result import Result
from .base_repository import BaseRepository

class ResultRepository:
    def __init__(self):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{PSQLConfig.user}:{PSQLConfig.password}@"
            f"{PSQLConfig.host}:{PSQLConfig.port}/{PSQLConfig.database}"
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def save_result(self, data: dict[str, str]) -> None:
        """Save result to database"""
        async with self.async_session() as session:
            repo = BaseRepository(Result, session)
            await repo.create(
                result_id=data["result_id"],
                command=data["command"],
                result_path=data["result_path"],
                session_id=data["session_id"]
            )

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
