"""
Organization Model.

Represents a tenant in the multi-tenant SaaS architecture.
"""

import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Organization(Base, UUIDMixin, TimestampMixin):
    """Organization (Tenant) model.

    This is the root entity for multi-tenancy. All data is scoped to an organization.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[PlanType] = mapped_column(
        Enum(PlanType),
        default=PlanType.FREE,
        nullable=False,
    )

    # Relationships
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    repositories = relationship(
        "Repository", back_populates="organization", cascade="all, delete-orphan"
    )
    memberships = relationship(
        "Membership", back_populates="organization", cascade="all, delete-orphan"
    )
    settings = relationship(
        "OrganizationSettings",
        uselist=False,
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    conversations = relationship(
        "Conversation", back_populates="organization", cascade="all, delete-orphan"
    )
