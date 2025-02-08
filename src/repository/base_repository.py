from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session  # SQLAlchemy의 데이터베이스 연결 세션

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        return instance
    
    async def update(self, **kwargs) -> ModelType:
        instance = await self.get(**kwargs)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.commit()
        return instance

    async def get(self, **kwargs) -> ModelType | None:
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, **kwargs) -> list[ModelType]:
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()) 