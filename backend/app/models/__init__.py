"""Models package - SQLAlchemy ORM models."""

from app.models.activity import Activity, ActivityType, BusinessUpdate, ImpactLevel
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.conversation import (
    ChatMessage,
    Conversation,
    ConversationStatus,
    MessageRole,
)
from app.models.issue import Issue, IssueState
from app.models.magic_link import MagicLink
from app.models.membership import MemberRole, Membership
from app.models.organization import Organization, PlanType
from app.models.organization_settings import OrganizationSettings
from app.models.repo import Repository
from app.models.report import Report, ReportType
from app.models.report_template import ReportTemplate
from app.models.team import Team
from app.models.user import User

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    # Multi-tenancy
    "Organization",
    "PlanType",
    "Team",
    "User",
    "Membership",
    "MemberRole",
    "OrganizationSettings",
    # Auth
    "MagicLink",
    # Core
    "Repository",
    "Activity",
    "BusinessUpdate",
    "ActivityType",
    "ImpactLevel",
    "Issue",
    "IssueState",
    # Chat
    "Conversation",
    "ChatMessage",
    "ConversationStatus",
    "MessageRole",
    # Reports
    "Report",
    "ReportType",
    "ReportTemplate",
]
