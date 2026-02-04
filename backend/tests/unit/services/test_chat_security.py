from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models import Activity
from app.models.membership import MemberRole
from app.services.chat_service import chat_service

# from app.models.team import team_repositories # This is harder to mock via simple import if it's a Table object.

# Mocks for DB setup would be complex, so relying on unit logic testing where possible
# or using existing fixtures if available.
# Assuming standard pytest-asyncio and database fixtures are not easily available in this context without deep exploration.
# I will simulate the logic by mocking the db session execution results.


@pytest.mark.asyncio
async def test_chat_security_boundary_viewer_sanitization():
    # Setup
    db = AsyncMock()

    # Mock Activity Return
    activity_id = uuid4()
    mock_activity = MagicMock(spec=Activity)
    mock_activity.id = activity_id
    mock_activity.type = MagicMock()
    mock_activity.type.value = "COMMIT"
    mock_activity.title = "Safe Title"
    mock_activity.content = "Sensitive Raw Content\nWith Code Diffs"
    mock_activity.author = "Author <email@corp.com>"
    mock_activity.occurred_at = None
    mock_activity.created_at = None
    mock_activity.files_touched = ["secret_key.pem"]
    mock_activity.labels = []
    mock_activity.linked_issues = []
    mock_activity.value_tags = []
    mock_activity.external_id = "abc12345secret"

    # Mock Result
    mock_result = MagicMock()
    mock_result.all.return_value = [(mock_activity, "repo-name")]
    db.execute.return_value = mock_result

    # 1. Test VIEWER Role
    activities_viewer = await chat_service.get_context_activities(
        db, team_id="team-123", user_role=MemberRole.VIEWER, limit=1
    )

    act_viewer = activities_viewer[0]
    assert act_viewer["title"] == "Safe Title"
    assert act_viewer["content"] == "Safe Title"  # Sanitized to title
    assert "Sensitive" not in act_viewer["content"]
    assert act_viewer["external_id"] is None  # Hidden
    assert act_viewer["files_touched"] == []  # Hidden

    # 2. Test MEMBER Role
    # Reset mock to return same object (iterator consumed)
    mock_result.all.return_value = [(mock_activity, "repo-name")]

    activities_member = await chat_service.get_context_activities(
        db, team_id="team-123", user_role=MemberRole.MEMBER, limit=1
    )

    act_member = activities_member[0]
    assert act_member["content"] == "Sensitive Raw Content\nWith Code Diffs"
    assert act_member["external_id"] == "abc12345secret"
    assert act_member["files_touched"] == ["secret_key.pem"]
