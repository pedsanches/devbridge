from sqlalchemy import Boolean, Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class DerivedArtifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "derived_artifacts"

    entity_type = Column(String(50), nullable=False)  # activity, commit, pr
    entity_id = Column(UUID(as_uuid=False), nullable=False, index=True)  # Logical link to entity
    artifact_type = Column(String(50), nullable=False)  # embedding, summary
    pipeline_version = Column(
        String(200), nullable=False
    )  # {prompt_hash}:{model_id}:{code_version}
    content_hash = Column(String(64), nullable=False)
    storage_ref = Column(Text, nullable=True)  # Qdrant ID or S3 path

    supersedes_artifact_id = Column(
        UUID(as_uuid=False), ForeignKey("derived_artifacts.id"), nullable=True
    )
    is_current = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "entity_id",
            "artifact_type",
            "pipeline_version",
            "content_hash",
            name="uq_artifact",
        ),
    )
