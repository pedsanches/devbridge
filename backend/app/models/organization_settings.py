"""
Organization Settings Model.

Stores configuration per organization (Slack webhook, GitHub App, .devbridge.yaml).
"""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class OrganizationSettings(Base, UUIDMixin, TimestampMixin):
    """Organization Settings model.

    Stores per-organization configuration including:
    - .devbridge.yaml content (as JSONB)
    - Slack webhook URL
    - GitHub App installation ID
    """

    __tablename__ = "organization_settings"

    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    devbridge_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    slack_webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_app_installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="settings")
