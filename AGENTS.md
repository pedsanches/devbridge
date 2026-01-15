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
poetry run mypy       # Type check Python
pnpm lint                  # Lint TypeScript
pnpm typecheck             # TypeScript strict verification
```

## Architecture

| Layer | Stack | Purpose |
|-------|-------|---------|
| **API** | FastAPI (async) | REST endpoints, webhooks |
| **Worker** | Celery + Redis | Async event processing |
| **AI** | LangGraph + Claude 3.5 | Agent orchestration |
| **Database** | PostgreSQL + Qdrant | Relational + Vector (Hybrid Search) |
| **Privacy** | Microsoft Presidio | PII sanitization before LLM |
| **Frontend** | Next.js 16, React 19, TailwindCSS | Dashboard & Chat UI |

**Pattern:** Event-Driven RAG → Webhooks → Queue → Worker → Agent

## Critical Rules

### ✅ DO
- Always use type hints (Python) and explicit types (TypeScript)
- Run `pytest` / `pnpm test` before committing
- Update documentation when changing business logic
- Use CSS variables from `docs/design/foundations.md` for styling
- Create ADRs for major architectural decisions
- **Use `?? fallback` for array index access** (TypeScript strict mode)
- **Add `| undefined` to optional props when passing undefined values**

### ❌ DON'T
- Never hardcode colors (use `var(--color-*)`)
- Never process PII without Presidio sanitization
- Never output "I will do that" without actually doing it
- Never skip tests for new logic
- **Never access array elements without null checks** (`noUncheckedIndexedAccess`)
- **Never use `setState` directly inside `useEffect`** (use refs or useSyncExternalStore)

## TypeScript Strict Mode Patterns

```typescript
// Array access - ALWAYS use fallback
const item = array[0] ?? defaultValue;

// Optional props - ALWAYS include | undefined
interface Props {
  onClick?: (() => void) | undefined;
}

// Spread array elements - ALWAYS check first
const item = array[index];
if (item) { array[index] = { ...item, newProp: value }; }
```

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
| Type check (Python) | `poetry run mypy` | Strict mode enabled |
| Type check (TS) | `pnpm typecheck` | Strict mode + extra checks |
| Pre-commit | `poetry run pre-commit run --all-files` | Runs all checks |

## Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code change without feature/fix
- `test:` adding tests

## Debug & Troubleshooting

**Always start with:**
```bash
make diagnose     # Full diagnostic
```

**Key debug commands:**
| Command | Purpose |
|---------|---------|
| `make diagnose` | Full system diagnostic |
| `make diagnose-env` | Validate .env configuration |
| `make diagnose-logs` | Show recent errors |
| `make health` | Quick service health check |

**Error response format:**
```json
{
  "error_id": "uuid",
  "trace_id": "trace-for-logs",
  "error_code": "AUTH_001",
  "message": "Human readable",
  "path": "/api/v1/endpoint"
}
```

**To find error details:**
```bash
docker logs devbridge-backend-1 2>&1 | grep "trace_id=YOUR_TRACE_ID"
```

**Common error codes:**
| Code | Meaning | Action |
|------|---------|--------|
| `AUTH_001` | Invalid token | Re-login |
| `VAL_001` | Validation failed | Check request body |
| `RES_001` | Resource not found | Verify ID |
| `EXT_001` | GitHub API error | Check token |
| `INT_001` | Internal error | Collect trace_id |

For detailed flows, see: [docs/development/debug-guide.md](docs/development/debug-guide.md)

## Deep Context

For detailed information, see:

| Document | Purpose |
|----------|---------|
| [docs/system-context.md](docs/system-context.md) | Full system map and tech stack |
| [docs/agent-guide.md](docs/agent-guide.md) | Development protocol for agents |
| [docs/development/code-style.md](docs/development/code-style.md) | Detailed code conventions |
| [docs/development/frontend-best-practices.md](docs/development/frontend-best-practices.md) | Frontend TypeScript/React patterns |
| [docs/development/debug-guide.md](docs/development/debug-guide.md) | **Debug flows and error resolution** |
| [docs/development/error-codes.md](docs/development/error-codes.md) | Full error code catalog (DVB-xxx) |
| [docs/business/rules-catalog.md](docs/business/rules-catalog.md) | Domain business rules |
| [docs/design/foundations.md](docs/design/foundations.md) | Design tokens (colors, typography) |
