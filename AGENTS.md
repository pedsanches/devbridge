# DevBridge - AI Agent Instructions ("The Router")

> This file follows the [AGENTS.md](https://agents.md) open standard for tool-agnostic AI agent instructions.

## 🧠 Core Philosophy: "Agent-First & Skill-Based"

You are an advanced AI engineer working on **DevBridge**.
To prevent context rot and ensure high expertise, you must **LOAD SKILLS** before starting deep work.

### 🚦 The Flow

1.  **Understand Task**: Read the user request.
2.  **Identify Domain**: Is this Backend? Frontend? ML Modeling? Full Stack?
3.  **Load Skill**: Use `view_file` on the relevant `SKILL.md` (see below).
4.  **Execute**: Follow the specific rules in that Skill.

## 📂 Skill Capabilities (Route Map)

| Domain | Skill File (Absolute Path) | Trigger Keywords |
|--------|----------------------------|------------------|
| **Backend** | `.agent/skills/backend-dev/SKILL.md` | FastAPI, Python, Pydantic, API, Celery, Database |
| **Frontend** | `.agent/skills/frontend-dev/SKILL.md` | React, Next.js, UI, Styles, Components, Tailwind |
| **ML Engineering** | `.agent/skills/ml-engineer/SKILL.md` | Training, Lumina, PyTorch, Datasets, Evaluation, Experiments |
| **QA & Testing** | `.agent/skills/qa-engineer/SKILL.md` | Tests, Vitest, Pytest, E2E, Bugs |

## 🛡️ Universal Laws (Apply Always)

### 1. The Prime Directive: `task_boundary`
- **ALWAYS** start complex interactions with `task_boundary`.
- **UPDATE** the status frequently.
- **NEVER** leave a task "hanging" without a `notify_user` or clear conclusion.

### 2. Security First
- **NEVER** output secrets, keys, or passwords in chat.
- **NEVER** commit PII.
- **ALWAYS** assume the user is watching.

### 3. File Operations
- **ALWAYS** use absolute paths.
- **NEVER** edit a file without reading it first (`view_file`).
- **PREFER** `replace_file_content` for contiguous blocks.

### 4. Commits & Verification
- **ALWAYS** run verification commands (lint/test) *before* asking for review.
- **NEVER** commit broken code knowingly.

## ⚡ Quick Reference (Global)

```bash
make diagnose       # Run full system health check
make help           # See available commands
```

---
*If you are unsure which skill to load, start with `backend-dev` as it contains the core business logic.*
