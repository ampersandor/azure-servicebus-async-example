from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
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
        # Get primary key from kwargs
        pk_name = self.model.__mapper__.primary_key[0].name
        pk_value = kwargs.pop(pk_name)
        
        # Create update statement
        stmt = (
            update(self.model)
            .where(getattr(self.model, pk_name) == pk_value)
            .values(**kwargs)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        # Return updated instance
        return await self.get(**{pk_name: pk_value})

    async def get(self, **kwargs) -> ModelType | None:
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, **kwargs) -> list[ModelType]:
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()) 