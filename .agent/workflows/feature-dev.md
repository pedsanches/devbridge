---
description: Standard workflow for developing new features with high quality and verification.
---

# Workflow: Feature Development

Use this workflow for significant code changes.

## 1. Bootstrap & Plan

1.  **Analyze Request**: Understand what the user wants.
2.  **Identify Domain**:
    - If Backend: `view_file .agent/skills/backend-dev/SKILL.md`
    - If Frontend: `view_file .agent/skills/frontend-dev/SKILL.md`
    - If Both: Load both.
3.  **Create Plan**:
    - Create/Update `implementation_plan.md`.
    - **WAIT** for user approval (use `notify_user` if necessary).

## 2. Execution (Loop)

1.  **Task Management**:
    - Create/Update `task.md` with granular steps.
    - Call `task_boundary` to set the mood.
2.  **Implementation**:
    - Edit files (`replace_file_content` / `multi_replace_file_content`).
    - **Constraint**: Adhere to the rules in the loaded `SKILL.md`.

## 3. Verification (The Gate)

1.  **Automated Checks**:
    - Run the linters/tests defined in the Skill.
    - // turbo
    - `make diagnose` (or specific domain check).
2.  **Manual Verification**:
    - If Frontend: Use `browser_subagent` to verify UI.
    - If Backend: Use `curl` or a script to verify API.

## 4. Documentation

1.  **Artifacts**:
    - Create `walkthrough.md` with proof of work (screenshots/logs).
    - Update `CHANGELOG.md` if applicable.
2.  **Cleanup**:
    - Delete any temporary reproduction scripts.
    - Mark `task.md` as complete.
