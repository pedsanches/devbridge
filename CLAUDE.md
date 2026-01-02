# Claude Code Instructions for DevBridge

## Primary Instructions

Read [`AGENTS.md`](AGENTS.md) at the project root for complete guidance.

## Quick Reference

```bash
# Development
poetry run uvicorn app.main:app --reload  # Backend
pnpm dev                                   # Frontend

# Testing
poetry run pytest                          # Backend tests
pnpm test                                  # Frontend tests

# Linting
poetry run ruff check .                    # Python lint
poetry run mypy app/                       # Python types
```

## Key Constraints

- **Type hints required:** Python (mypy strict), TypeScript (strict mode)
- **No hardcoded colors:** Use `var(--color-*)` from design tokens
- **Privacy-first:** Never process PII without Presidio sanitization
- **Docs = Code:** Update documentation when changing business logic

## Context Files

- [`docs/system-context.md`](docs/system-context.md) — System map & tech stack
- [`docs/agent-guide.md`](docs/agent-guide.md) — Development protocol
- [`docs/development/code-style.md`](docs/development/code-style.md) — Code conventions
