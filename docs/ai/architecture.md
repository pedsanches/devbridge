# AI System Architecture

This document describes how Artificial Intelligence (Anti-Gravity Agents) understands and interacts with the **DevBridge** system.

## 🧠 The "Brain" (Context Management)

The system uses a **Federated Context** model to avoid "Context Rot" (the degradation of attention when the context window is filled with irrelevant rules).

### The Router (`AGENTS.md`)
The entry point. It contains only the metadata required to route the agent to the correct domain.
- **Role**: Traffic Controller.
- **Knowledge**: Universal Laws (Security, Task Boundaries) + Routing Table.

### The Skills (`.agent/skills/`)
Specialized packages of knowledge loaded *on demand*.
- **Backend**: Strict Typing, Pydantic, FastAPI.
- **Frontend**: Next.js 16, React 19, Design Tokens.
- **ML**: Reproducibility, Data Integrity, Metric tracking.
- **QA**: Red-Green-Refactor, Edge Case hunting.

## ⚡ The "Nervous System" (Workflows)

We use **Standard Operating Procedures (SOPs)** located in `.agent/workflows/`.
These workflows automate the "Process" ensuring consistency regardless of the underlying LLM.

- **`feature-dev`**: The rigorous "Plan-Code-Verify" loop.
- **`ml-experiment`**: The scientific method applied to code (Hypothesis-Run-Log).

## 🔄 Integration Points

| System | Integration |
|--------|-------------|
| **Git** | Agents read `.gitignore`, use conventional commits, and link IDs |
| **Make** | Agents use `Makefile` for standardized entry points (`make diagnose`, `make test`) |
| **Docs** | Agents treat `docs/` as the "Source of Truth" for business rules |
| **Tools** | See [docs/ai/tooling_strategy.md](tooling_strategy.md) for approved MCP servers & extensions |

## 🛡️ Safety Systems

1.  **Presidio**: PII sanitization (enforced policy).
2.  **Linting**: Blockers on commit (via `run_command` verification).
3.  **Human-in-the-Loop**: `implementation_plan.md` MUST be approved before code changes.
