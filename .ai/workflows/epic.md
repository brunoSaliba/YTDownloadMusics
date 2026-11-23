# Workflow — EPIC

EPIC is for cross-cutting work and must be decomposed.

1. System-level success criteria, architecture, threat model and migration/compatibility strategy in `plan.md`.
2. One fresh reviewer checks `plan.md`.
3. Decompose into independently reviewable FEATURE/TASK slices with explicit dependency order; define rollout/rollback and observability.
4. **Plan Gate** (human): approves definition and staged plan together.
5. Execute each child task through its own workflow and PR where practical.
6. Epic-level integration/security verification in `review.md`.
7. Consolidate durable knowledge in `.memory-bank/`.

Avoid a single giant implementation branch whose scope cannot be meaningfully reviewed.
