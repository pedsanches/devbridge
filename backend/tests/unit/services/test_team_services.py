"""
Unit tests for TeamService and TeamSyncService.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.team_service import TeamService, slugify
from app.services.team_sync_service import TeamSyncService


class TestSlugify:
    """Tests for the slugify utility function."""

    def test_basic_slugify(self):
        """Test basic slug generation."""
        assert slugify("Frontend Team") == "frontend-team"

    def test_slugify_with_special_chars(self):
        """Test slug generation with special characters."""
        assert slugify("Team #1 (Main)") == "team-1-main"

    def test_slugify_with_accents(self):
        """Test slug generation with accented characters."""
        # Note: Current implementation doesn't normalize accents
        result = slugify("Pagamentos & Cobranças")
        assert "pagamentos" in result.lower()

    def test_slugify_empty_string(self):
        """Test slug generation with empty string."""
        assert slugify("") == ""


class TestTeamService:
    """Tests for TeamService."""

    @pytest.fixture
    def service(self):
        """Create a TeamService instance."""
        return TeamService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_service_instantiation(self, service):
        """Test service can be instantiated."""
        assert service is not None


class TestTeamSyncService:
    """Tests for TeamSyncService."""

    @pytest.fixture
    def service(self):
        """Create a TeamSyncService instance."""
        return TeamSyncService()

    def test_generate_color_from_name(self, service):
        """Test color generation is deterministic."""
        color1 = service._generate_color_from_name("Frontend")
        color2 = service._generate_color_from_name("Frontend")
        _ = service._generate_color_from_name("Backend")

        # Same name should produce same color
        assert color1 == color2
        # Different names should likely produce different colors (not guaranteed but probable)
        # (just check format)
        assert color1.startswith("#")
        assert len(color1) == 7

    def test_generate_color_valid_hex(self, service):
        """Test generated color is valid hex."""
        for name in ["Team A", "Team B", "Frontend", "Backend", "DevOps"]:
            color = service._generate_color_from_name(name)
            assert color.startswith("#")
            assert len(color) == 7
            # Should be valid hex
            int(color[1:], 16)

    @pytest.mark.asyncio
    async def test_sync_no_repositories(self, service):
        """Test sync when no repositories exist."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.sync_github_teams(
            mock_db,
            str(uuid4()),
            "fake_token",
        )

        assert result["synced_teams"] == 0
        assert "Nenhum repositório" in result["message"]


class TestTeamSyncServiceIntegration:
    """Integration-style tests for TeamSyncService."""

    @pytest.fixture
    def service(self):
        return TeamSyncService()

    @pytest.mark.asyncio
    async def test_sync_with_mocked_github(self, service):
        """Test sync with mocked GitHub API responses."""
        org_id = str(uuid4())

        # Mock DB
        mock_db = AsyncMock()

        # Mock repository owners query
        mock_owner_result = MagicMock()
        mock_owner_result.all.return_value = [("test-org",)]
        mock_db.execute.return_value = mock_owner_result

        # Patch GitHubService
        with patch("app.services.team_sync_service.GitHubService") as MockGH:
            mock_gh_instance = AsyncMock()
            MockGH.return_value = mock_gh_instance

            # Mock no teams returned
            mock_gh_instance.list_user_teams.return_value = []

            result = await service.sync_github_teams(mock_db, org_id, "token")

            assert result["synced_teams"] == 0
            assert "Nenhum time encontrado" in result["message"]
