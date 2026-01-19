"""
Tests for Chat Citations (BR-012).

Tests that sources include ref_id (R1, R2, ...) and external_id for verifiable citations.
Also tests architectural hardening: BaseAIService decoupling, consistent R# generation.
"""

from app.schemas.chat import SourceItem
from app.services.chat_service import build_sources_with_citations


class TestChatCitations:
    """Tests for the citation system in chat responses."""

    def test_build_sources_with_citations_generates_sequential_ref_ids(self):
        """build_sources_with_citations should generate R1, R2, R3, etc."""
        activities = [
            {
                "title": "First PR",
                "repository": "repo1",
                "type": "PULL_REQUEST",
                "external_id": "123",
            },
            {
                "title": "Second commit",
                "repository": "repo2",
                "type": "COMMIT",
                "external_id": "abc1234def",
            },
            {
                "title": "Third PR",
                "repository": "repo1",
                "type": "PULL_REQUEST",
                "external_id": "456",
            },
        ]

        sources = build_sources_with_citations(activities, limit=5)

        assert len(sources) == 3
        assert sources[0].ref_id == "R1"
        assert sources[1].ref_id == "R2"
        assert sources[2].ref_id == "R3"

    def test_build_sources_with_citations_formats_pr_external_id(self):
        """PR external_id should be formatted as PR#<number>."""
        activities = [
            {"title": "Fix bug", "repository": "repo", "type": "PULL_REQUEST", "external_id": "42"},
        ]

        sources = build_sources_with_citations(activities)

        assert sources[0].external_id == "PR#42"

    def test_build_sources_with_citations_formats_commit_sha(self):
        """Commit external_id should show first 7 characters of SHA."""
        activities = [
            {
                "title": "Add feature",
                "repository": "repo",
                "type": "COMMIT",
                "external_id": "abc1234567890def",
            },
        ]

        sources = build_sources_with_citations(activities)

        assert sources[0].external_id == "abc1234"

    def test_build_sources_with_citations_handles_missing_external_id(self):
        """Should handle activities without external_id gracefully."""
        activities = [
            {"title": "Old activity", "repository": "repo", "type": "COMMIT"},
        ]

        sources = build_sources_with_citations(activities)

        assert sources[0].ref_id == "R1"
        assert sources[0].external_id is None

    def test_build_sources_with_citations_respects_limit(self):
        """Should respect the limit parameter."""
        activities = [
            {
                "title": f"Activity {i}",
                "repository": "repo",
                "type": "COMMIT",
                "external_id": f"sha{i}",
            }
            for i in range(10)
        ]

        sources = build_sources_with_citations(activities, limit=3)

        assert len(sources) == 3
        assert sources[0].ref_id == "R1"
        assert sources[1].ref_id == "R2"
        assert sources[2].ref_id == "R3"

    def test_build_sources_with_citations_empty_list(self):
        """Should return empty list when no activities."""
        sources = build_sources_with_citations([])

        assert sources == []
        # No citations when no activities (short-circuit behavior)

    def test_build_sources_with_citations_preserves_all_fields(self):
        """Should preserve all SourceItem fields."""
        activities = [
            {
                "title": "Important PR",
                "repository": "main-repo",
                "type": "PULL_REQUEST",
                "author": "developer1",
                "url": "https://github.com/org/repo/pull/123",
                "external_id": "123",
            },
        ]

        sources = build_sources_with_citations(activities)

        assert sources[0].title == "Important PR"
        assert sources[0].repository == "main-repo"
        assert sources[0].type == "PULL_REQUEST"
        assert sources[0].author == "developer1"
        assert sources[0].url == "https://github.com/org/repo/pull/123"
        assert sources[0].ref_id == "R1"
        assert sources[0].external_id == "PR#123"

    def test_source_item_schema_backward_compatible(self):
        """SourceItem should be backward compatible (new fields are optional)."""
        # Should work without ref_id and external_id (backward compatibility)
        source = SourceItem(
            title="Test",
            repository="repo",
            type="COMMIT",
        )

        assert source.ref_id is None
        assert source.external_id is None

        # Should work with new fields
        source_with_citations = SourceItem(
            title="Test",
            repository="repo",
            type="COMMIT",
            ref_id="R1",
            external_id="abc1234",
        )

        assert source_with_citations.ref_id == "R1"
        assert source_with_citations.external_id == "abc1234"


class TestBaseAIServiceDecoupling:
    """Tests that BaseAIService does NOT know about citations."""

    def test_base_ai_service_context_has_no_citation_refs(self):
        """BaseAIService._format_activities_context should NOT include [R#]."""
        from app.services.ai.base import BaseAIService

        service = BaseAIService()
        activities = [
            {"title": "Test PR", "repository": "repo", "type": "PULL_REQUEST"},
            {"title": "Test Commit", "repository": "repo", "type": "COMMIT"},
        ]

        context = service._format_activities_context(activities)

        # Should NOT contain citation references
        assert "[R1]" not in context
        assert "[R2]" not in context
        assert "ref_id" not in context.lower()
        # Should contain neutral numbering
        assert "1. [" in context
        assert "2. [" in context


class TestConversationAICitations:
    """Tests that ConversationAI correctly formats citations."""

    def test_format_activities_with_citations_includes_ref_ids(self):
        """ConversationAI.format_activities_with_citations should include [R#]."""
        from app.services.ai.conversation import ConversationAI

        service = ConversationAI()
        activities = [
            {"title": "Test PR", "repository": "repo", "type": "PULL_REQUEST", "external_id": "42"},
            {
                "title": "Test Commit",
                "repository": "repo",
                "type": "COMMIT",
                "external_id": "abc1234",
            },
        ]

        context = service.format_activities_with_citations(activities)

        # Should contain citation references
        assert "[R1]" in context
        assert "[R2]" in context
        # Should contain formatted external IDs
        assert "PR#42" in context
        assert "abc1234" in context

    def test_format_activities_with_citations_uses_sources_ref_ids(self):
        """format_activities_with_citations should use sources' ref_id if provided."""
        from app.services.ai.conversation import ConversationAI

        service = ConversationAI()
        activities = [
            {"title": "PR 1", "repository": "repo", "type": "PULL_REQUEST", "external_id": "1"},
            {"title": "PR 2", "repository": "repo", "type": "PULL_REQUEST", "external_id": "2"},
        ]
        sources = [
            SourceItem(title="PR 1", repository="repo", type="PULL_REQUEST", ref_id="R1"),
            SourceItem(title="PR 2", repository="repo", type="PULL_REQUEST", ref_id="R2"),
        ]

        context = service.format_activities_with_citations(activities, sources)

        # Should use ref_id from sources
        assert "[R1]" in context
        assert "[R2]" in context

    def test_format_activities_with_citations_empty_returns_message(self):
        """format_activities_with_citations with empty list returns helpful message."""
        from app.services.ai.conversation import ConversationAI

        service = ConversationAI()
        context = service.format_activities_with_citations([])

        assert "Nenhuma atividade encontrada" in context


class TestHonestyClauseCitationRules:
    """Tests that HONESTY_CLAUSE contains citation rules."""

    def test_honesty_clause_includes_citation_rules(self):
        """HONESTY_CLAUSE should include citation rules."""
        from app.services.ai.conversation import HONESTY_CLAUSE

        # Core citation rules should be present
        assert "REGRAS DE CITAÇÃO" in HONESTY_CLAUSE
        assert "(R#)" in HONESTY_CLAUSE or "[R#]" in HONESTY_CLAUSE
        assert "Conceito Geral" in HONESTY_CLAUSE

    def test_honesty_clause_includes_when_to_use_citations(self):
        """HONESTY_CLAUSE should explain when to use and not use citations."""
        from app.services.ai.conversation import HONESTY_CLAUSE

        # When to use
        assert "factual" in HONESTY_CLAUSE.lower() or "fato" in HONESTY_CLAUSE.lower()
        # When NOT to use
        assert "intenção" in HONESTY_CLAUSE.lower() or "hipótese" in HONESTY_CLAUSE.lower()
