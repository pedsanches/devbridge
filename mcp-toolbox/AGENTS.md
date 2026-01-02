# MCP Toolbox - AI Agent Instructions

> This file follows the [AGENTS.md](https://agents.md) open standard for tool-agnostic AI agent instructions.

## Purpose

The MCP Toolbox provides **read-only database access** for AI agents working on the DevBridge project. It enables agents to query PostgreSQL data through structured tools without direct database credentials.

## Quick Start

```bash
# Start the toolbox
./toolbox --tools_file tools-secure.yaml --address 127.0.0.1 --port 5000

# Health check
curl http://localhost:5000/health
```

## Available Tools

### Database Query Tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `query_repositories` | List monitored repositories | Repository metadata |
| `query_commits` | Search commits by repo/date/author | Commit details |
| `query_translations` | Get business translations | Translation records |
| `query_metrics` | Aggregated metrics | Stats and counts |

### Query Examples

```sql
-- Get recent commits for a repository
SELECT sha, message, author, timestamp
FROM commits
WHERE repository_id = $1
ORDER BY timestamp DESC
LIMIT 10;

-- Get translations with high confidence
SELECT title, business_value, confidence_score
FROM translations
WHERE confidence_score >= 80
ORDER BY created_at DESC;
```

## Security Model

| Aspect | Policy |
|--------|--------|
| **Access Level** | Read-only (`mcp_readonly` user) |
| **Allowed Operations** | SELECT only |
| **Blocked Operations** | INSERT, UPDATE, DELETE, DDL |
| **Network** | Localhost only (127.0.0.1) |

> [!CAUTION]
> Never attempt to modify data through this toolbox. All write operations are blocked at the database level.

## Schema Reference

### Main Tables

```
repositories
├── id (UUID, PK)
├── url (TEXT)
├── name (TEXT)
├── owner (TEXT)
├── description (TEXT)
├── default_branch (TEXT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

commits
├── sha (TEXT, PK)
├── repository_id (UUID, FK)
├── message (TEXT)
├── author (TEXT)
├── author_email (TEXT)
├── timestamp (TIMESTAMP)
├── files_changed (INT)
├── additions (INT)
└── deletions (INT)

translations
├── id (UUID, PK)
├── commit_sha (TEXT, FK)
├── title (TEXT)
├── technical_summary (TEXT)
├── business_value (TEXT)
├── risks_mitigated (TEXT[])
├── aligned_pillars (JSONB)
├── metrics (JSONB)
├── confidence_score (INT)
└── created_at (TIMESTAMP)
```

## Best Practices

### ✅ DO

- Use parameterized queries to prevent SQL injection
- Limit result sets with LIMIT clause
- Filter by specific repository when possible
- Use the provided query tools instead of raw SQL when available

### ❌ DON'T

- Attempt to execute DDL statements
- Run queries without LIMIT on large tables
- Access tables outside the `public` schema
- Share connection details or credentials

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure toolbox is running on port 5000 |
| Query timeout | Add LIMIT clause, use more specific filters |
| Permission denied | Check you're using read-only tools |
| Empty results | Verify repository_id and date ranges |

## Related Documentation

- [SECURITY.md](./SECURITY.md) - Security policies
- [tools-secure.yaml](./tools-secure.yaml) - Tool definitions
- [QUICKREF.md](./QUICKREF.md) - Quick reference
