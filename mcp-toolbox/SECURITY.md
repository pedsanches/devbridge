# 🔒 MCP Toolbox Security Guide

## Security Principles Applied

This configuration follows the **principle of least privilege** and industry best practices for database access via AI tools.

### 1. Read-Only User

```sql
-- User: mcp_readonly
-- Permissions: SELECT only
-- No: INSERT, UPDATE, DELETE, CREATE, DROP, ALTER
```

The `mcp_readonly` user can **only read data** and cannot modify anything.

### 2. Predefined Queries Only

All tools use **static, parameterized SQL statements**:
- No dynamic SQL generation
- No arbitrary query execution
- SQL injection is impossible

### 3. Safe Data Exposure

Tools are designed to:
- ✅ Show schema metadata (table structure)
- ✅ Show row counts and statistics
- ✅ Show database health metrics
- ❌ NOT expose raw user data
- ❌ NOT show sensitive columns
- ❌ NOT allow data export

### 4. System Table Protection

Queries explicitly exclude system schemas:
- `pg_catalog` - PostgreSQL internals
- `information_schema` - System tables
- `pg_toast` - Toast storage

---

## Available Tools (All Read-Only)

| Tool | Purpose | Exposes Data? |
|------|---------|---------------|
| `list-databases` | List database names | No |
| `list-tables` | List table names | No |
| `describe-table` | Show column schema | No (metadata only) |
| `list-indexes` | Show index definitions | No |
| `list-foreign-keys` | Show FK relationships | No |
| `count-rows` | Count table rows | No (count only) |
| `table-stats` | Performance metrics | No |
| `database-health` | Health overview | No |
| `list-connections` | Active connections | No (sanitized) |

---

## What This Configuration Prevents

### ❌ Data Modification
```sql
-- These are IMPOSSIBLE with mcp_readonly:
INSERT INTO users VALUES (...);
UPDATE users SET password = '...';
DELETE FROM users;
DROP TABLE users;
TRUNCATE users;
```

### ❌ Schema Changes
```sql
-- These are IMPOSSIBLE:
ALTER TABLE users ADD COLUMN ...;
CREATE TABLE malicious ...;
DROP INDEX ...;
```

### ❌ Privilege Escalation
```sql
-- These are IMPOSSIBLE:
GRANT ALL TO mcp_readonly;
ALTER USER mcp_readonly SUPERUSER;
CREATE EXTENSION ...;
```

### ❌ Data Exfiltration
```sql
-- No tool allows:
SELECT * FROM users;  -- Cannot query raw data
COPY users TO '/tmp/data.csv';  -- No file access
SELECT password FROM users;  -- No column access
```

---

## PostgreSQL User Permissions

```sql
-- Verify permissions (run as admin)
SELECT 
  grantee, 
  privilege_type, 
  table_schema, 
  table_name
FROM information_schema.role_table_grants
WHERE grantee = 'mcp_readonly';

-- Should only show SELECT privileges
```

### Granted Permissions
- `CONNECT` on database
- `USAGE` on public schema
- `SELECT` on tables in public schema

### Revoked Permissions
- All write operations
- All DDL operations
- All admin operations

---

## Network Security Recommendations

### For Development (Current)
```yaml
# Server binds to localhost only
--address 127.0.0.1
```

### For Production

1. **Never expose directly to internet**
2. **Use TLS/SSL** for connections
3. **Add authentication** layer
4. **Use VPN or private network**
5. **Enable audit logging**

```bash
# Production example with restricted origins
./toolbox \
  --tools-file tools-secure.yaml \
  --address 127.0.0.1 \
  --allowed-origins "https://your-app.com" \
  --log-level INFO
```

---

## Audit Trail

The MCP Toolbox logs all tool invocations. Monitor with:

```bash
# Run with logging
./toolbox --tools-file tools-secure.yaml --log-level INFO

# Logs show:
# - Which tools are called
# - When they are called
# - Parameters passed
```

---

## To Revoke Access

If you need to remove MCP access:

```sql
-- Connect as admin
psql -U pedrosanches -d postgres

-- Revoke all permissions
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM mcp_readonly;
REVOKE USAGE ON SCHEMA public FROM mcp_readonly;
REVOKE CONNECT ON DATABASE postgres FROM mcp_readonly;

-- Drop the user
DROP USER mcp_readonly;
```

---

## Security Checklist

- [x] Read-only database user
- [x] No dynamic SQL queries
- [x] System schemas excluded
- [x] No raw data exposure
- [x] Parameterized queries
- [x] Localhost binding only
- [x] Logging enabled
- [ ] TLS encryption (add for production)
- [ ] API authentication (add for production)
- [ ] Rate limiting (add for production)

---

## Files

| File | Purpose |
|------|---------|
| `tools-secure.yaml` | Production-ready secure config |
| `tools-starter.yaml` | Development testing only |
| `tools.yaml.example` | Full example with all options |

**For production, always use `tools-secure.yaml`**
