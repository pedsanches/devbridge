"""
Report Template Model.

SQLAlchemy model for customizable report templates.
Supports multi-tenancy, data filters, section configuration, language and visual settings.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReportTemplate(Base, UUIDMixin, TimestampMixin):
    """
    Customizable report template.

    Stores all configuration for generating custom reports including:
    - Data filters (repos, authors, activity types)
    - Section configuration (enabled sections, order, detail level)
    - Language settings (idiom, tone, verbosity)
    - Visual settings (colors, fonts, logo)
    """

    __tablename__ = "report_templates"

    # Multi-tenancy
    organization_id = Column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # None = organization-wide template
        index=True,
    )

    # Template metadata
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Configuration (JSONB for flexibility)
    data_filters = Column(
        JSONB,
        nullable=True,
        comment="Filters: repositories, authors, activity_types, impact_levels, value_tags, labels",
    )
    sections_config = Column(
        JSONB,
        nullable=False,
        comment="Section configs: type, title, enabled, order, detail_level, custom_prompt",
    )
    language_config = Column(
        JSONB,
        nullable=True,
        comment="Language: language, formality, jargon_level, verbosity, tone, format",
    )
    visual_config = Column(
        JSONB,
        nullable=True,
        comment="Visual: primary_color, secondary_color, font_family, logo_url, show_charts, watermark",
    )

    # Relationships
    organization = relationship("Organization", back_populates="report_templates")
    user = relationship("User", back_populates="report_templates")

    def __repr__(self) -> str:
        return f"<ReportTemplate(id={self.id}, name='{self.name}')>"
