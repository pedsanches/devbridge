# DevBridge - AI Agent Instructions

> This file follows the [AGENTS.md](https://agents.md) open standard for tool-agnostic AI agent instructions.

## Quick Start

```bash
# Backend
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
pnpm install
pnpm dev

# Tests
poetry run pytest          # Backend
pnpm test                  # Frontend
```

## Code Style

| Language | Conventions | Tools |
|----------|-------------|-------|
| **Python** | `snake_case`, type hints required, Google-style docstrings | `ruff`, `mypy` |
| **TypeScript** | `camelCase` functions, `PascalCase` components, strict mode | ESLint, Prettier |

**Verification commands:**
```bash
poetry run ruff check .    # Lint Python
poetry run mypy app/       # Type check Python
pnpm lint                  # Lint TypeScript
```

## Architecture

| Layer | Stack | Purpose |
|-------|-------|---------|
| **API** | FastAPI (async) | REST endpoints, webhooks |
| **Worker** | Celery + Redis | Async event processing |
| **AI** | LangGraph + Claude 3.5 | Agent orchestration |
| **Database** | PostgreSQL + Qdrant | Relational + Vector (Hybrid Search) |
| **Privacy** | Microsoft Presidio | PII sanitization before LLM |
| **Frontend** | Next.js 15, Vercel AI SDK | Dashboard & Chat UI |

**Pattern:** Event-Driven RAG → Webhooks → Queue → Worker → Agent

## Critical Rules

### ✅ DO
- Always use type hints (Python) and explicit types (TypeScript)
- Run `pytest` / `pnpm test` before committing
- Update documentation when changing business logic
- Use CSS variables from `docs/design/foundations.md` for styling
- Create ADRs for major architectural decisions

### ❌ DON'T
- Never hardcode colors (use `var(--color-*)`)
- Never process PII without Presidio sanitization
- Never output "I will do that" without actually doing it
- Never skip tests for new logic

## File Structure

| Path | Contents |
|------|----------|
| `backend/app/services/` | Business logic (Python) |
| `backend/app/agents/` | LangGraph agent definitions |
| `frontend/src/components/ui/` | Shadcn/UI primitives |
| `docs/architecture/decisions/` | ADRs (Architecture Decision Records) |
| `docs/business/rules-catalog.md` | Domain business rules |
| `docs/design/` | Design system (tokens, components, brand) |

## Testing

| Type | Command | Notes |
|------|---------|-------|
| Unit (backend) | `poetry run pytest` | Required for new logic |
| Unit (frontend) | `pnpm test` | Vitest |
| Lint | `poetry run ruff check .` | Auto-fix: `ruff check . --fix` |
| Type check | `poetry run mypy app/` | Strict mode enabled |
| Pre-commit | `poetry run pre-commit run --all-files` | Runs all checks |

## Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code change without feature/fix
- `test:` adding tests

## Deep Context

For detailed information, see:

| Document | Purpose |
|----------|---------|
| [docs/system-context.md](docs/system-context.md) | Full system map and tech stack |
| [docs/agent-guide.md](docs/agent-guide.md) | Development protocol for agents |
| [docs/development/code-style.md](docs/development/code-style.md) | Detailed code conventions |
| [docs/business/rules-catalog.md](docs/business/rules-catalog.md) | Domain business rules |
| [docs/design/foundations.md](docs/design/foundations.md) | Design tokens (colors, typography) |
