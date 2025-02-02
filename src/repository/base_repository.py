from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from src.model.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        return instance

    async def get(self, **kwargs) -> ModelType:
        return await self.session.query(self.model).filter_by(**kwargs).first()

    async def get_all(self, **kwargs) -> list[ModelType]:
        return await self.session.query(self.model).filter_by(**kwargs).all() 