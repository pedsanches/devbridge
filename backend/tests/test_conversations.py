"""Tests for Conversations API."""

import pytest
from httpx import AsyncClient

# Use existing conftest fixtures: async_client, db_session, authenticated_headers, test_user


@pytest.mark.asyncio
async def test_create_conversation(
    async_client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    """Test creating a new conversation."""
    response = await async_client.post(
        "/api/v1/conversations",
        headers=authenticated_headers,
        json={"message": "Hello, AI!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["message_count"] == 1
    assert data["title"] is not None
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello, AI!"


@pytest.mark.asyncio
async def test_list_conversations(
    async_client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    """Test listing conversations."""
    # First create one
    await async_client.post(
        "/api/v1/conversations",
        headers=authenticated_headers,
        json={"message": "Thread 1"},
    )

    response = await async_client.get(
        "/api/v1/conversations",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["conversations"]) >= 1
    assert data["conversations"][0]["title"]


@pytest.mark.asyncio
async def test_get_conversation_detail(
    async_client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    """Test getting conversation details."""
    # Create
    create_res = await async_client.post(
        "/api/v1/conversations",
        headers=authenticated_headers,
        json={"message": "Detail Test"},
    )
    conv_id = create_res.json()["id"]

    # Get
    response = await async_client.get(
        f"/api/v1/conversations/{conv_id}",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert len(data["messages"]) == 1


@pytest.mark.asyncio
async def test_update_conversation(
    async_client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    """Test updating conversation title."""
    # Create
    create_res = await async_client.post(
        "/api/v1/conversations",
        headers=authenticated_headers,
        json={"message": "Old Title"},
    )
    conv_id = create_res.json()["id"]

    # Update
    response = await async_client.patch(
        f"/api/v1/conversations/{conv_id}",
        headers=authenticated_headers,
        json={"title": "New Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_conversation(
    async_client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    """Test soft deleting conversation."""
    # Create
    create_res = await async_client.post(
        "/api/v1/conversations",
        headers=authenticated_headers,
        json={"message": "Delete Me"},
    )
    conv_id = create_res.json()["id"]

    # Delete
    response = await async_client.delete(
        f"/api/v1/conversations/{conv_id}",
        headers=authenticated_headers,
    )
    assert response.status_code == 204

    # Verify archived status directly in DB (API might filter archived)
    # But let's check via list API filter if implemented, or just check that get returns status

    # Re-fetch via GET (should be 404 or return archived?)
    # Our implementation throws 404 if not found, let's verify DB state manually or check list behavior
    # For now, let's assume it should still be fetchable via ID but status is archived?
    # Actually current implementation soft deletes setting status=ARCHIVED, but get_conversation filters by ID only.
    # So it should return conversation with status ARCHIVED.

    response = await async_client.get(
        f"/api/v1/conversations/{conv_id}",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "archived"
