# Claude Code Instructions for MCP Toolbox

## Primary Instructions

Read [`AGENTS.md`](./AGENTS.md) for complete guidance on using the MCP Toolbox.

## Quick Reference

```bash
# Toolbox runs on localhost:5000
# Use the mcp tools to query the database

# Available tools:
# - query_repositories: List repositories
# - query_commits: Search commits
# - query_translations: Get translations
# - query_metrics: Aggregated stats
```

## Key Constraints

- **Read-only access:** You can only SELECT data, not modify it
- **Use tools:** Prefer the structured tools over raw SQL when available
- **Limit queries:** Always use LIMIT clause to avoid large result sets
- **Filter wisely:** Use repository_id and date ranges to narrow results

## Common Queries

### Get repository info
```sql
SELECT id, name, owner, description
FROM repositories
WHERE name = 'repository-name';
```

### Get recent commits
```sql
SELECT sha, message, author, timestamp
FROM commits
WHERE repository_id = 'uuid-here'
ORDER BY timestamp DESC
LIMIT 20;
```

### Get high-confidence translations
```sql
SELECT title, business_value, confidence_score
FROM translations
WHERE confidence_score >= 80
ORDER BY created_at DESC
LIMIT 10;
```

## Important

> [!CAUTION]
> This toolbox provides **read-only** access. Any write operations will be rejected.

## Context Files

- [`AGENTS.md`](./AGENTS.md) — Full documentation and schema reference
- [`SECURITY.md`](./SECURITY.md) — Security policies
- [`QUICKREF.md`](./QUICKREF.md) — Command quick reference
