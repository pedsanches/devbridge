"""
Report Template Schemas.

Pydantic schemas for customizable report templates.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# ============================================================
# Enums
# ============================================================


class SectionType(str, Enum):
    """Available section types for reports."""

    SUMMARY = "summary"
    METRICS = "metrics"
    HIGHLIGHTS = "highlights"
    RISKS = "risks"
    TECHNICAL = "technical"
    TIMELINE = "timeline"
    CONTRIBUTORS = "contributors"
    CUSTOM = "custom"


class DetailLevel(str, Enum):
    """Detail level for sections."""

    MINIMAL = "minimal"
    NORMAL = "normal"
    DETAILED = "detailed"


class Language(str, Enum):
    """Supported languages."""

    PT_BR = "pt-BR"
    EN_US = "en-US"
    ES = "es"


class Tone(str, Enum):
    """Report tone options."""

    NEUTRAL = "neutral"
    OPTIMISTIC = "optimistic"
    CAUTIOUS = "cautious"


class ContentFormat(str, Enum):
    """Content format options."""

    BULLETS = "bullets"
    PARAGRAPHS = "paragraphs"
    MIXED = "mixed"


class FontFamily(str, Enum):
    """Available font families for PDF."""

    INTER = "Inter"
    ROBOTO = "Roboto"
    ARIAL = "Arial"


class Watermark(str, Enum):
    """Watermark options."""

    CONFIDENTIAL = "CONFIDENTIAL"
    DRAFT = "DRAFT"


class HeaderStyle(str, Enum):
    """PDF header style options."""

    MINIMAL = "minimal"
    FULL = "full"


# ============================================================
# Configuration Schemas
# ============================================================


class DataFilters(BaseModel):
    """Filters for report data selection."""

    repositories: list[str] | None = Field(None, description="Repository IDs or names to include")
    authors: list[str] | None = Field(None, description="Author usernames to include")
    activity_types: list[Literal["COMMIT", "PULL_REQUEST"]] | None = Field(
        None, description="Activity types to include"
    )
    impact_levels: list[Literal["LOW", "MEDIUM", "HIGH"]] | None = Field(
        None, description="Impact levels to include"
    )
    value_tags: list[str] | None = Field(None, description="Value tags to filter by")
    labels: list[str] | None = Field(None, description="PR labels to filter by")


class SectionConfig(BaseModel):
    """Configuration for a single report section."""

    type: SectionType = Field(..., description="Section type")
    title: str = Field(..., description="Custom section title")
    enabled: bool = Field(True, description="Whether this section is enabled")
    order: int = Field(..., description="Display order (0-based)")
    detail_level: DetailLevel = Field(DetailLevel.NORMAL, description="Level of detail")
    custom_prompt: str | None = Field(None, description="Custom AI prompt for this section")


class LanguageConfig(BaseModel):
    """Language and tone configuration."""

    language: Language = Field(Language.PT_BR, description="Output language")
    formality: int = Field(3, ge=1, le=5, description="Formality level (1=casual, 5=formal)")
    jargon_level: int = Field(2, ge=1, le=5, description="Technical jargon (1=none, 5=full)")
    verbosity: int = Field(3, ge=1, le=5, description="Verbosity (1=concise, 5=detailed)")
    tone: Tone = Field(Tone.NEUTRAL, description="Report tone")
    format: ContentFormat = Field(ContentFormat.BULLETS, description="Content format")


class VisualConfig(BaseModel):
    """Visual/styling configuration for PDF export."""

    primary_color: str = Field("#3B82F6", description="Primary color (hex)")
    secondary_color: str = Field("#1E40AF", description="Secondary color (hex)")
    font_family: FontFamily = Field(FontFamily.INTER, description="Font family")
    logo_url: str | None = Field(None, description="Custom logo URL")
    show_charts: bool = Field(True, description="Include metric charts")
    watermark: Watermark | None = Field(None, description="Optional watermark")
    header_style: HeaderStyle = Field(HeaderStyle.FULL, description="PDF header style")


# ============================================================
# Template CRUD Schemas
# ============================================================


class ReportTemplateCreate(BaseModel):
    """Schema for creating a new report template."""

    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: str | None = Field(None, description="Template description")
    is_default: bool = Field(False, description="Set as default template")
    data_filters: DataFilters | None = Field(None, description="Data filter configuration")
    sections_config: list[SectionConfig] = Field(..., description="Section configurations")
    language_config: LanguageConfig | None = Field(None, description="Language configuration")
    visual_config: VisualConfig | None = Field(None, description="Visual configuration")


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    is_default: bool | None = None
    data_filters: DataFilters | None = None
    sections_config: list[SectionConfig] | None = None
    language_config: LanguageConfig | None = None
    visual_config: VisualConfig | None = None


class ReportTemplateResponse(BaseModel):
    """Full response schema for a report template."""

    id: str
    name: str
    description: str | None
    is_default: bool
    data_filters: DataFilters | None
    sections_config: list[SectionConfig]
    language_config: LanguageConfig | None
    visual_config: VisualConfig | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportTemplateListItem(BaseModel):
    """Compact schema for template list."""

    id: str
    name: str
    description: str | None
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReportTemplateListResponse(BaseModel):
    """Paginated list of templates."""

    items: list[ReportTemplateListItem]
    total: int
    page: int
    page_size: int


# ============================================================
# Report Generation with Template
# ============================================================


class GenerateReportWithTemplate(BaseModel):
    """Request to generate a report using a template."""

    template_id: str | None = Field(None, description="Template ID (None for defaults)")
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")
    # Optional overrides
    data_filters: DataFilters | None = Field(None, description="Override data filters")
    sections_config: list[SectionConfig] | None = Field(None, description="Override sections")
    language_config: LanguageConfig | None = Field(None, description="Override language config")
    visual_config: VisualConfig | None = Field(None, description="Override visual config")


class ExportPDFRequest(BaseModel):
    """Request to export a report as PDF."""

    report_id: str | None = Field(None, description="Saved report ID to export")
    # Or generate new
    template_id: str | None = Field(None, description="Template ID for new report")
    period_start: datetime | None = None
    period_end: datetime | None = None
    # Visual overrides for export
    visual_config: VisualConfig | None = Field(None, description="Override visual config")


# ============================================================
# Default Sections
# ============================================================

DEFAULT_SECTIONS: list[SectionConfig] = [
    SectionConfig(
        type=SectionType.SUMMARY,
        title="Resumo Executivo",
        order=0,
        enabled=True,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
    SectionConfig(
        type=SectionType.METRICS,
        title="Métricas e KPIs",
        order=1,
        enabled=True,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
    SectionConfig(
        type=SectionType.HIGHLIGHTS,
        title="Destaques",
        order=2,
        enabled=True,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
    SectionConfig(
        type=SectionType.RISKS,
        title="Riscos e Atenções",
        order=3,
        enabled=True,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
    SectionConfig(
        type=SectionType.TECHNICAL,
        title="Detalhes Técnicos",
        order=4,
        enabled=False,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
    SectionConfig(
        type=SectionType.TIMELINE,
        title="Linha do Tempo",
        order=5,
        enabled=False,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
    SectionConfig(
        type=SectionType.CONTRIBUTORS,
        title="Contribuidores",
        order=6,
        enabled=False,
        detail_level=DetailLevel.NORMAL,
        custom_prompt=None,
    ),
]
