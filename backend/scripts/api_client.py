#!/usr/bin/env python3
"""
DevBridge API Test Client.

Usage:
    cd backend
    poetry run python scripts/api_client.py batch-generate-updates
    poetry run python scripts/api_client.py list-activities
    poetry run python scripts/api_client.py sync --repo pedsanches/devbridge

This script generates a valid JWT token for the test user and makes
authenticated API calls to the DevBridge backend.
"""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

import httpx

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we can import from app
from app.core.security import create_access_token
from app.services.repository_service import DEFAULT_ORG_ID


def get_test_token(user_id: str = "test-user", org_id: str = DEFAULT_ORG_ID) -> str:
    """Generate a valid JWT token for testing."""
    return create_access_token(
        data={
            "sub": user_id,
            "org_id": org_id,
        },
        expires_delta=timedelta(hours=1),
    )


class DevBridgeClient:
    """HTTP client for DevBridge API."""

    def __init__(self, base_url: str = "http://localhost:8001", token: str | None = None):
        self.base_url = base_url
        self.token = token or get_test_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an HTTP request."""
        url = f"{self.base_url}{path}"
        with httpx.Client() as client:
            response = client.request(method, url, headers=self.headers, timeout=120, **kwargs)
            if response.status_code >= 400:
                print(f"Error {response.status_code}: {response.text}")
                return {"error": response.text}
            return response.json()

    def list_activities(self, page: int = 1, page_size: int = 20) -> dict:
        """List activities."""
        return self._request("GET", f"/api/v1/activities?page={page}&page_size={page_size}")

    def batch_generate_updates(self) -> dict:
        """Run batch generation of business updates."""
        return self._request("POST", "/api/v1/activities/batch-generate-updates")

    def generate_update(self, activity_id: str) -> dict:
        """Generate business update for a single activity."""
        return self._request("POST", f"/api/v1/activities/{activity_id}/generate-update")

    def sync(self, repo_name: str) -> dict:
        """Sync a repository."""
        return self._request("POST", "/api/v1/sync", json={"repo_name": repo_name})

    def health(self) -> dict:
        """Check API health."""
        return self._request("GET", "/api/v1/health")


def main():
    parser = argparse.ArgumentParser(description="DevBridge API Client")
    parser.add_argument(
        "--org-id",
        type=str,
        default=None,
        help=f"Organization ID (default: {DEFAULT_ORG_ID})",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list-activities
    list_parser = subparsers.add_parser("list-activities", help="List activities")
    list_parser.add_argument("--page", type=int, default=1)
    list_parser.add_argument("--page-size", type=int, default=10)

    # batch-generate-updates
    subparsers.add_parser("batch-generate-updates", help="Batch generate business updates")

    # generate-update
    gen_parser = subparsers.add_parser(
        "generate-update", help="Generate update for single activity"
    )
    gen_parser.add_argument("activity_id", help="Activity ID")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync a repository")
    sync_parser.add_argument("--repo", required=True, help="Repository name (owner/repo)")

    # health
    subparsers.add_parser("health", help="Check API health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get org_id from args or use default
    org_id = getattr(args, "org_id", None) or DEFAULT_ORG_ID
    client = DevBridgeClient(token=get_test_token(org_id=org_id))

    print("🔧 DevBridge API Client")
    print(f"📍 Base URL: {client.base_url}")
    print(f"🔑 Token: {client.token[:20]}...")
    print("-" * 50)

    if args.command == "health":
        result = client.health()
        print(f"Health: {result}")

    elif args.command == "list-activities":
        result = client.list_activities(args.page, args.page_size)
        if "data" in result:
            print(f"Found {result['total']} activities (showing {len(result['data'])})")
            for act in result["data"]:
                has_update = "✅" if act.get("business_update") else "❌"
                print(f"  {has_update} {act['title'][:60]}...")
        else:
            print(result)

    elif args.command == "batch-generate-updates":
        print("Running batch generation... (this may take a while)")
        result = client.batch_generate_updates()
        print("\n📊 Results:")
        print(f"  Total:     {result.get('total', 'N/A')}")
        print(f"  Processed: {result.get('processed', 'N/A')}")
        print(f"  Failed:    {result.get('failed', 'N/A')}")
        print(f"  Skipped:   {result.get('skipped', 'N/A')}")

    elif args.command == "generate-update":
        result = client.generate_update(args.activity_id)
        if "business_update" in result:
            update = result["business_update"]
            print("✅ Generated update:")
            print(f"  Summary: {update['summary']}")
            print(f"  Impact:  {update['impact_level']}")
            print(f"  Category: {update.get('category', 'N/A')}")
        else:
            print(result)

    elif args.command == "sync":
        print(f"Syncing {args.repo}...")
        result = client.sync(args.repo)
        print("\n📊 Sync Results:")
        print(f"  Commits synced: {result.get('commits_synced', 'N/A')}")
        print(f"  PRs synced:     {result.get('prs_synced', 'N/A')}")


if __name__ == "__main__":
    main()
