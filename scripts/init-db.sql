-- ============================================================
-- DevBridge - Database Initialization
-- ============================================================
-- This script runs automatically on first container start
-- ============================================================

-- Create read-only user for MCP Toolbox (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcp_readonly') THEN
        CREATE ROLE mcp_readonly WITH LOGIN PASSWORD 'mcp_readonly_secure';
    END IF;
END
$$;

-- Grant connect privilege
GRANT CONNECT ON DATABASE devbridge TO mcp_readonly;

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO mcp_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_readonly;

-- ============================================================
-- Extensions
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
