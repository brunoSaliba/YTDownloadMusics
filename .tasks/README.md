# Tasks

Each active or historical engineering change gets a directory named with its task ID and slug, for example:

`FEAT-003-soc-integration/`

The machine-readable `state.json` controls gates, security classification, write scope, external actions, and cross-AI continuity pointers. Task artifacts explain the decision and evidence trail.

Each task also contains:

- `session-handoff.md` — current human-readable handoff; context, never authority;
- `checkpoints/` — immutable JSON snapshots of task + Git state at meaningful boundaries.

On a model/session change, follow `.ai/workflows/resume.md`. A worker switch never resets approval or scope.

Do not use task files as a substitute for durable system documentation; promote lasting facts to `.memory-bank/`.
