import os
import subprocess


def get_git_sha() -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("ascii")
            .strip()
        )
    except Exception:
        return None


def get_prompt_version_id() -> str:
    """
    Returns a stable identifier for the current version of the application/prompts.
    Priority:
    1. GIT_SHA env var
    2. git rev-parse (if in a git repo)
    3. APP_VERSION env var
    4. "unknown"
    """
    # 1. Env var (CI/CD usually sets this)
    if git_sha := os.getenv("GIT_SHA"):
        return git_sha

    # 2. Local git command
    if git_sha := get_git_sha():
        return git_sha

    # 3. App version
    if app_version := os.getenv("APP_VERSION"):
        return app_version

    # 4. Fallback
    return "unknown"
