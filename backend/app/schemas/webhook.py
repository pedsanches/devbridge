"""
Webhook Schemas.

Pydantic schemas for parsing GitHub webhook payloads.
"""

from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    """GitHub user from webhook payload."""

    login: str
    id: int
    email: str | None = None


class GitHubCommit(BaseModel):
    """Commit data from GitHub push webhook."""

    id: str  # SHA
    message: str
    timestamp: str
    author: GitHubUser | dict[str, str]  # Can be nested object or simple dict
    url: str
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)


class GitHubRepository(BaseModel):
    """Repository data from GitHub webhook."""

    id: int
    name: str
    full_name: str  # "owner/repo"
    html_url: str
    private: bool = False


class GitHubPushPayload(BaseModel):
    """GitHub push event webhook payload."""

    ref: str  # "refs/heads/main"
    before: str  # Previous HEAD SHA
    after: str  # New HEAD SHA
    repository: GitHubRepository
    pusher: GitHubUser | dict[str, str]
    sender: GitHubUser
    commits: list[GitHubCommit] = Field(default_factory=list)
    head_commit: GitHubCommit | None = None

    @property
    def branch(self) -> str:
        """Extract branch name from ref."""
        return self.ref.replace("refs/heads/", "")


class GitHubPRUser(BaseModel):
    """User in PR payload."""

    login: str
    id: int


class GitHubPullRequest(BaseModel):
    """Pull request data from GitHub webhook."""

    id: int
    number: int
    title: str
    body: str | None = None
    state: str  # "open", "closed"
    html_url: str
    user: GitHubPRUser
    merged: bool = False
    draft: bool = False
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class GitHubPRPayload(BaseModel):
    """GitHub pull_request event webhook payload."""

    action: str  # "opened", "closed", "synchronize", etc.
    number: int
    repository: GitHubRepository
    sender: GitHubUser
    pull_request: GitHubPullRequest
