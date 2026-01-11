"""Models package - SQLAlchemy ORM models."""

from app.models.activity import Activity, ActivityType, BusinessUpdate, ImpactLevel
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.code_review import CodeReview, ReviewState
from app.models.contributor_stats import ContributorStats
from app.models.conversation import (
    ChatMessage,
    Conversation,
    ConversationStatus,
    MessageRole,
)
from app.models.developer_profile import DeveloperProfile
from app.models.issue import Issue, IssueState
from app.models.magic_link import MagicLink
from app.models.membership import MemberRole, Membership
from app.models.organization import Organization, PlanType
from app.models.organization_settings import OrganizationSettings
from app.models.repo import Repository
from app.models.report import Report, ReportType
from app.models.report_template import ReportTemplate
from app.models.team import Team, team_repositories
from app.models.team_metrics import TeamMetrics
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
    "team_repositories",
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
    "CodeReview",
    "ReviewState",
    "DeveloperProfile",
    "ContributorStats",
    "TeamMetrics",
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
