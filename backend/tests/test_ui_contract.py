"""
Test UI Contract.

Verifies that the Enums in `ui_contract.py` match the expectations documented in
`docs/contracts/ui-contract.md`.
"""

from app.schemas.ui_contract import (
    ConfidenceLevel,
    EvidenceType,
    JobStatus,
    ReferenceType,
    Severity,
)


def test_severity_enums():
    """Verify Severity enums match UI contract expectations."""
    expected = {"info", "success", "warning", "error"}
    actual = {e.value for e in Severity}
    assert actual == expected, f"Severity mismatch. Expected {expected}, got {actual}"


def test_confidence_enums():
    """Verify ConfidenceLevel enums match UI contract expectations."""
    expected = {"high", "medium", "low"}
    actual = {e.value for e in ConfidenceLevel}
    assert actual == expected, f"Confidence mismatch. Expected {expected}, got {actual}"


def test_job_status_enums():
    """Verify JobStatus enums match UI contract expectations."""
    expected = {"queued", "running", "succeeded", "failed", "canceled"}
    actual = {e.value for e in JobStatus}
    assert actual == expected, f"JobStatus mismatch. Expected {expected}, got {actual}"


def test_reference_type_enums():
    """Verify ReferenceType enums contain core types."""
    # We check for SUPERSET, as backend might support newer types than front
    core_expected = {
        "pull_request",
        "issue",
        "commit",
        "doc",
        "slack",
        "url",
        "activity",
    }
    actual = {e.value for e in ReferenceType}
    assert core_expected.issubset(actual), f"Missing core ReferenceTypes: {core_expected - actual}"


def test_evidence_type_enums():
    """Verify EvidenceType enums."""
    core_expected = {
        "code_diff",
        "log_snippet",
        "metric_change",
        "rule_violation",
    }
    actual = {e.value for e in EvidenceType}
    assert core_expected.issubset(actual), f"Missing core EvidenceTypes: {core_expected - actual}"
