"""
Tests for no-context response helper (anti-hallucination gate).

Validates that build_no_context_response returns deterministic, helpful messages
when no activities are found.
"""

from app.services.chat_service import NO_CONTEXT_RESPONSE, build_no_context_response


class TestBuildNoContextResponse:
    """Tests for build_no_context_response function."""

    def test_returns_base_message_without_hints(self):
        """Should return base message when no filters are provided."""
        result = build_no_context_response()

        assert "Não encontrei atividades" in result
        assert "Período de tempo" in result
        assert "Repositórios selecionados" in result
        assert "ajuste os filtros" in result

    def test_includes_days_hint_when_low(self):
        """Should suggest increasing days when period is short."""
        result = build_no_context_response(days=7)

        assert "aumentar o período" in result
        assert "7 dias" in result

    def test_no_days_hint_when_already_high(self):
        """Should not suggest days increase when already 30+."""
        result = build_no_context_response(days=30)

        assert "aumentar o período" not in result

    def test_includes_repository_hint(self):
        """Should include repository in suggestion when filtered."""
        result = build_no_context_response(repository="my-repo")

        assert "my-repo" in result
        assert "possui atividades recentes" in result

    def test_includes_multiple_repositories_hint(self):
        """Should list all repositories when multiple are provided."""
        result = build_no_context_response(repository=["repo-a", "repo-b"])

        assert "repo-a" in result
        assert "repo-b" in result

    def test_combines_multiple_hints(self):
        """Should combine days and repository hints."""
        result = build_no_context_response(days=7, repository="my-repo")

        assert "7 dias" in result
        assert "my-repo" in result
        assert "Sugestão específica" in result

    def test_no_context_response_constant_exists(self):
        """NO_CONTEXT_RESPONSE constant should exist for simple use cases."""
        assert NO_CONTEXT_RESPONSE is not None
        assert "Não encontrei atividades" in NO_CONTEXT_RESPONSE
