from __future__ import annotations

import uuid
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.core.database import Base
from app.core.exceptions import NotFoundError

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_fail(self, id: uuid.UUID) -> ModelType:
        instance = await self.get_by_id(id)
        if instance is None:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return instance

    async def get_many(
        self,
        *filters: ColumnElement[bool],
        skip: int = 0,
        limit: int = 20,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[ModelType], int]:
        count_stmt = select(func.count()).select_from(self.model)
        query_stmt = select(self.model)

        for f in filters:
            count_stmt = count_stmt.where(f)
            query_stmt = query_stmt.where(f)

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        if sort_by and hasattr(self.model, sort_by):
            sort_col = getattr(self.model, sort_by)
            query_stmt = query_stmt.order_by(sort_col.desc() if sort_desc else sort_col)

        query_stmt = query_stmt.offset(skip).limit(limit)
        result = await self.session.execute(query_stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(self, id: uuid.UUID, **kwargs: Any) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def exists(self, **kwargs: Any) -> bool:
        stmt = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def count(self, *filters: ColumnElement[bool]) -> int:
        stmt = select(func.count()).select_from(self.model)
        for f in filters:
            stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
