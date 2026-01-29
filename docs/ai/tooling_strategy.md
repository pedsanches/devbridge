# Anti-Gravity Tooling & MCP Strategy

This document outlines the recommended extensions and Model Context Protocol (MCP) servers to enable the "Agent-First" architecture for `devbridge`.

## 1. Principles of Adoption

1.  **Low Noise**: Tools must be "Pull-Only" (Agent requests data) or "Verified Push" (Critical alerts). No chatting firehoses.
2.  **Auditability**: Actions taken by tools must leave a trace (commits, logs, or DB records).
3.  **Scoped Power**: Tools should have specific, limited scopes (e.g., Read-Only DB access for debugging).

## 2. Essential Recommendations (Must Have)

These solve critical bottlenecks in the current `feature-dev` and `backend-dev` workflows.

### A. GitHub MCP
- **Use Case**: Task Management & Code Review.
- **Problem Solved**: "Context Switching". The agent can check existing Issues/PRs before creating new ones, avoiding duplication.
- **Workflow**:
    - `feature-dev`: Agent reads the Issue description directly from GitHub.
    - `bug-fix`: Agent finds the PR that introduced the bug.
- **Risk**: Agents creating infinite comment loops (Mitigation: Use strict system prompts in `AGENTS.md` to limit comment frequency).

### B. PostgreSQL MCP (Read-Only)
- **Use Case**: Backend Debugging & Verification.
- **Problem Solved**: "Blind Coding". Agents can verify if migrations actually worked or if seed data exists without writing ad-hoc python scripts.
- **Workflow**:
    - `backend-dev`: "Verify the user 'test@example.com' was created."
    - `qa-engineer`: "Check if the audit log table has entries."
- **Configuration**: Create a dedicated `read_only_agent` DB user. **NEVER** give write access to the tool directly (Agents should use the API for writes to test logic).

## 3. High-Value Recommendations (Should Have)

These amplify the `ml-engineer` and `frontend-dev` capabilities.

### C. Qdrant / Vector DB MCP
- **Use Case**: RAG & ML Debugging.
- **Problem Solved**: "Black Box Embeddings". Agents can search the vector store to see *what* the system is actually retrieving.
- **Workflow**:
    - `ml-experiment`: "Why did query 'DNA helix' return unrelated results?" -> Agent queries Qdrant directly.
- **Cost**: Requires setting up an MCP server for Qdrant (or using a generic HTTP MCP with Qdrant API spec).

### D. Sub-Agent Browser (Built-in)
- **Use Case**: E2E Verification.
- **Problem Solved**: "It works on my machine". Visual verification of the deployed frontend.
- **Workflow**:
    - `frontend-dev`: "Take a screenshot of the login page on mobile viewport."
    - `qa-engineer`: "Click the signup button and report any js console errors."
- **Note**: Already standard in Anti-Gravity, but must be explicitly called out in `workflows/feature-dev.md` as a verification step.

## 4. Custom/Advanced Integrations (Nice to Have)

### E. "Log-Scraper" MCP (Local)
- **Use Case**: Observability.
- **Problem Solved**: Tailing logs is hard via chat.
- **Implementation**: A simple local MCP that enables `read_recent_logs(service: "backend", lines: 50)`.
- **Workflow**: `bug-fix`.
- **Alternative**: Use `run_command` with `docker logs`. (Low priority if `run_command` works well).

## 5. What to AVOID (Anti-Patterns)

- **❌ Slack/Discord MCPs (Write Access)**: High risk of spamming public channels. Use `notify_user` instead, let the Human bridge the gap.
- **❌ "Memory" / "User Preferences" MCPs (Early Stage)**: Avoid complex long-term memory systems until the basic workflows are solid. Prefer `AGENTS.md` and `docs/` for explicit knowledge.

## 6. Implementation Plan

1.  **Phase 1**: Enable GitHub & PostgreSQL (Read-Only).
2.  **Phase 2**: Add "Browser Verification" step to `frontend-dev` workflow.
3.  **Phase 3**: Develop custom/generic Qdrant tool if ML debugging becomes a bottleneck.
