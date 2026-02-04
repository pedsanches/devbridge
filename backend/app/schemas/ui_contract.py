"""
UI Contract Schemas.

This file is the SINGLE SOURCE OF TRUTH for enums shared between Backend and Frontend.
Any additions here must be reflected in `docs/contracts/ui-contract.md`.
"""

from enum import Enum


class Severity(str, Enum):
    """Severity levels for insights, alerts, and notifications."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ConfidenceLevel(str, Enum):
    """
    Confidence level of AI assertions.

    Mapping:
    - HIGH: >= 0.8
    - MEDIUM: >= 0.5 < 0.8
    - LOW: < 0.5
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class JobStatus(str, Enum):
    """Execution status for async jobs (reports, analysis)."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class ReferenceType(str, Enum):
    """
    Types of entities that can be referenced/linked in the UI.
    Matches icons in `SmartReference.tsx`.
    """

    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    COMMIT = "commit"
    DOC = "doc"
    SLACK = "slack"
    # Fallbacks/Generic
    URL = "url"
    ACTIVITY = "activity"


class EvidenceType(str, Enum):
    """Specific types of technical evidence."""

    CODE_DIFF = "code_diff"
    LOG_SNIPPET = "log_snippet"
    METRIC_CHANGE = "metric_change"
    RULE_VIOLATION = "rule_violation"
