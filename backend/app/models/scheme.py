from __future__ import annotations

import enum
import uuid
from datetime import datetime, date, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SchemeCategoryName(str, enum.Enum):
    EDUCATION = "education"
    HEALTH = "health"
    AGRICULTURE = "agriculture"
    HOUSING = "housing"
    EMPLOYMENT = "employment"
    WOMEN = "women"
    CHILDREN = "children"
    ELDERLY = "elderly"
    DISABILITY = "disability"
    MINORITY = "minority"
    FINANCIAL = "financial"
    SKILL_DEVELOPMENT = "skill_development"
    SOCIAL_WELFARE = "social_welfare"
    OTHER = "other"


class SchemeLevel(str, enum.Enum):
    CENTRAL = "central"
    STATE = "state"
    DISTRICT = "district"
    LOCAL = "local"


class SchemeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    COMING_SOON = "coming_soon"
    ARCHIVED = "archived"


class EligibilityOp(str, enum.Enum):
    EQ = "eq"
    NEQ = "neq"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CONTAINS = "contains"


class SchemeCategory(Base):
    __tablename__ = "scheme_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_categories.id"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    children: Mapped[list[SchemeCategory]] = relationship(
        "SchemeCategory", backref="parent", remote_side=[id]
    )
    schemes: Mapped[list["Scheme"]] = relationship(
        "Scheme", back_populates="category"
    )


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    title_te: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    description_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_te: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheme_categories.id"), nullable=False
    )
    ministry: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[SchemeLevel] = mapped_column(
        Enum(SchemeLevel, name="scheme_level", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        nullable=False,
    )
    state_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SchemeStatus] = mapped_column(
        Enum(SchemeStatus, name="scheme_status", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        default=SchemeStatus.ACTIVE,
        nullable=False,
    )
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget_allocated: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    beneficiaries_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    application_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidelines_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    portal_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category: Mapped[SchemeCategory] = relationship("SchemeCategory", back_populates="schemes")
    eligibility_rules: Mapped[list["SchemeEligibilityRule"]] = relationship(
        "SchemeEligibilityRule", back_populates="scheme", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date > launch_date",
            name="schemes_end_after_launch",
        ),
        Index("idx_schemes_category", "category_id"),
        Index("idx_schemes_level", "level"),
        Index("idx_schemes_state", "state_code"),
        Index("idx_schemes_status", "status"),
        Index("idx_schemes_tags", "tags", postgresql_using="gin"),
        Index("idx_schemes_metadata", "metadata", postgresql_using="gin"),
    )


class SchemeEligibilityRule(Base):
    __tablename__ = "scheme_eligibility_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[EligibilityOp] = mapped_column(
        Enum(EligibilityOp, name="eligibility_op", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        nullable=False,
    )
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    scheme: Mapped[Scheme] = relationship("Scheme", back_populates="eligibility_rules")
