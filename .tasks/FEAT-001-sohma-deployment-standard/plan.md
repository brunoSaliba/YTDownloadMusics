# FEAT-001 — Plan

## Scope

Allowed repository writes:

- `AGENTS.md`
- `.ai/deployment-standard.md`
- `.ai/platforms/bneli-vps.md`
- `.ai/workflows/init-project.md`
- `.ai/workflows/init-existing-project.md`
- `.ai/workflows/production-change.md`
- `.tasks/FEAT-001-sohma-deployment-standard/**`

No production host is changed by this feature.

## Implementation units

1. Add reusable SOHMA-style deployment standard.
2. Add mutable `bneli.tech` VPS inventory profile with explicit stale-data warning.
3. Integrate both into new-project and existing-project workflows.
4. Extend production-change workflow with live shared-VPS revalidation requirements.
5. Add constitution-level pointer in `AGENTS.md`.
6. Verify the candidate diff against scope and security invariants.
7. Perform independent code/policy review and security review.
8. Open PR only after human Definition, Plan, and Security gates required by state are satisfied.

## Recovery note

A candidate implementation diff was produced before this feature task was registered. Treat it as unapproved candidate work. No further implementation should occur until the human gates authorize this plan; after approval, re-verify every candidate file rather than assuming the prior diff is accepted.
