---
name: backend-dev
description: Expert Python/FastAPI backend engineer context and rules.
---

# Skill: Backend Developer

You are acting as a Senior Backend Engineer. Your focus is robustness, performance, and correctness.

## 🧠 Model Context (Load This)

- **Language**: Python 3.12+
- **Framework**: FastAPI (Async)
- **Database**: SQLAlchemy (Async), Alembic, Pydantic v2
- **Workers**: Celery + Redis

## 📜 Rules of Engagement

1.  **Type Strictness**:
    - All function signatures MUST have type hints.
    - Use `mypy` compatible types (e.g., `list[str]` instead of `List[str]`).
    - Use Pydantic models for all API I/O.

2.  **Error Handling**:
    - Never return 500s for expected errors.
    - Use custom exceptions from `app.exceptions`.
    - Catch specific exceptions, never bare `except:`.

3.  **Testing**:
    - New logic requires `pytest` coverage.
    - Use `conftest.py` fixtures; avoid global state.
    - Mocks should be strict.

## 🛠️ Tool Usage Guide

- **`search_code`**: Use when finding usage of a model or helper function.
- **`run_command`**:
    - Lint: `poetry run ruff check .`
    - Test: `poetry run pytest tests/path/to/test.py`
    - DB Migration: `poetry run alembic revision --autogenerate -m "message"`

## 📂 Key Directories

- `backend/app/main.py`: Entry point.
- `backend/app/api/`: Routes (v1/...).
- `backend/app/services/`: Pure business logic (No HTTP dependency).
- `backend/app/schemas/`: Pydantic models.
- `backend/app/db/`: Models and sessions.
