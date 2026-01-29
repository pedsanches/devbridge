---
description: Rigorous workflow for running, tracking, and verifying ML experiments.
---

# Workflow: ML Experiment

Use this workflow when training models, evaluating datasets, or changing the ML pipeline.

## 1. Setup & Context

1.  **Load Skill**: `view_file .agent/skills/ml-engineer/SKILL.md`.
2.  **Check Resources**:
    - Run `nvidia-smi` to check GPU availability.
    - Check disk space if handling large datasets.

## 2. Design

1.  **Plan Experiment**:
    - Define hypothesis in `implementation_plan.md` (or a specific `experiments/EXP-00X.md`).
    - **User Check**: Confirm params with user if ambiguous.

## 3. Execution

1.  **Data Integrity**:
    - Run `python scripts/verify_data_integrity.py` (if exists) or manually check splits.
2.  **Launch**:
    - Run the training command.
    - **Capture ID**: Note the Experiment ID / Run Name.

## 4. Analysis & Report

1.  **Log Results**:
    - Update `REPORT.md` (or experiment log).
    - detailed metrics (Accuracy, Loss, F1).
2.  **Artifacts**:
    - Plot confusion matrix (if applicable) and save to artifacts.
    - Commit `walkthrough.md` with the results summary.

## 5. Cleanup

1.  **Heavy Files**:
    - Ensure checkpoints are saved in the correct folder (not committed to git).
    - `git status` to ensure no massive files are pending.
