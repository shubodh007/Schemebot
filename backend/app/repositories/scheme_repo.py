from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.document import SavedScheme
from app.models.scheme import Scheme, SchemeCategory, SchemeEligibilityRule
from app.repositories.base import BaseRepository


class SchemeRepository(BaseRepository[Scheme]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Scheme, session)

    async def search(
        self,
        query: str,
        category_id: Optional[UUID] = None,
        level: Optional[str] = None,
        state_code: Optional[str] = None,
        status: Optional[str] = "active",
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Scheme], int]:
        conditions = []

        if query:
            search_pattern = f"%{query}%"
            conditions.append(
                or_(
                    Scheme.title.ilike(search_pattern),
                    Scheme.description.ilike(search_pattern),
                    Scheme.title_hi.ilike(search_pattern),
                    Scheme.title_te.ilike(search_pattern),
                    Scheme.tags.any(query),
                )
            )

        if category_id:
            conditions.append(Scheme.category_id == category_id)
        if level:
            conditions.append(Scheme.level == level)
        if state_code:
            conditions.append(Scheme.state_code == state_code)
        if status:
            conditions.append(Scheme.status == status)
        if tags:
            for tag in tags:
                conditions.append(Scheme.tags.any(tag))

        return await self.get_many(*conditions, skip=skip, limit=limit)

    async def get_with_rules(self, scheme_id: UUID) -> Optional[Scheme]:
        stmt = (
            select(Scheme)
            .options(joinedload(Scheme.eligibility_rules), joinedload(Scheme.category))
            .where(Scheme.id == scheme_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Scheme]:
        stmt = select(Scheme).where(Scheme.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_category(self, category_id: UUID) -> List[Scheme]:
        items, _ = await self.get_many(
            Scheme.category_id == category_id,
            Scheme.status == "active",
        )
        return items

    async def get_matching_schemes(
        self,
        profile_data: Dict[str, Any],
        skip: int = 0,
        limit: int = 50,
    ) -> List[Scheme]:
        stmt = (
            select(Scheme)
            .options(joinedload(Scheme.eligibility_rules), joinedload(Scheme.category))
            .where(Scheme.status == "active")
            .order_by(Scheme.beneficiaries_count.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def bulk_upsert(self, schemes_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        updated = 0
        created = 0
        for data in schemes_data:
            slug = data.get("slug", "")
            existing = await self.get_by_slug(slug)
            if existing:
                for key, value in data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                updated += 1
            else:
                self.session.add(Scheme(**data))
                created += 1
        await self.session.flush()
        return created, updated


class SchemeCategoryRepository(BaseRepository[SchemeCategory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SchemeCategory, session)

    async def get_by_slug(self, slug: str) -> Optional[SchemeCategory]:
        stmt = select(SchemeCategory).where(SchemeCategory.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_counts(self) -> List[Dict[str, Any]]:
        stmt = (
            select(
                SchemeCategory.id,
                SchemeCategory.name,
                SchemeCategory.slug,
                SchemeCategory.icon_name,
                func.count(Scheme.id).label("scheme_count"),
            )
            .outerjoin(Scheme, Scheme.category_id == SchemeCategory.id)
            .group_by(SchemeCategory.id)
            .order_by(SchemeCategory.sort_order)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "id": str(row.id),
                "name": row.name,
                "slug": row.slug,
                "icon_name": row.icon_name,
                "scheme_count": row.scheme_count,
            }
            for row in rows
        ]


class SavedSchemeRepository(BaseRepository[SavedScheme]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SavedScheme, session)

    async def get_user_saved(self, user_id: UUID) -> List[SavedScheme]:
        stmt = (
            select(SavedScheme)
            .options(joinedload(SavedScheme.scheme))
            .where(SavedScheme.user_id == user_id)
            .order_by(SavedScheme.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_user_saved_ids(self, user_id: UUID) -> List[UUID]:
        stmt = select(SavedScheme.scheme_id).where(SavedScheme.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_user_and_scheme(self, user_id: UUID, scheme_id: UUID) -> bool:
        stmt = select(SavedScheme).where(
            and_(
                SavedScheme.user_id == user_id,
                SavedScheme.scheme_id == scheme_id,
            )
        )
        result = await self.session.execute(stmt)
        saved = result.scalar_one_or_none()
        if saved is None:
            return False
        await self.session.delete(saved)
        await self.session.flush()
        return True
