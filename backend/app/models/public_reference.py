from sqlalchemy import Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PublicReference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "public_references"

    code = Column(String(30), unique=True, nullable=False)  # R-{TEAM}-{SEQ}
    team_id = Column(
        UUID(as_uuid=False),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=False), nullable=False)
    external_url = Column(Text, nullable=True)

    # Relationships
    team = relationship("Team")

    __table_args__ = (
        UniqueConstraint("team_id", "entity_type", "entity_id", name="uq_ref_entity"),
    )
