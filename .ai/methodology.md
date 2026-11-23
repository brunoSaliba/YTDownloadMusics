# AI Engineering Protocol — Methodology

Turns AI coding into a reproducible process: persistent state, separation of duties, human gates, security throughout. Fast tracks remove ceremony, never security responsibilities.

## Tracks

| Track | Flow |
|---|---|
| HOTFIX | Triage → Containment → Minimal Fix → Tests → Review (+Security if relevant) → PR |
| BUGFIX | Diagnose → Reproduce → short plan → Fix → 1 regression test → Review → PR |
| TASK | Short plan → Implement → Tests → Review → PR |
| FEATURE | `plan.md` (acceptance, architecture if needed, threat model if sensitive) → fresh review → **Plan Gate** → Implement → Test → Verify/Review → PR → **human merge** |
| EPIC | FEATURE flow + decomposition into slices, each with its own PR |
| PROJECT | Discovery → `plan.md` (charter, acceptance, architecture, threat model, bootstrap plan) → review → **Plan Gate** → scaffold |

Security-sensitive work overlays extra controls and cannot use a quick path. Deploy through the pipeline is covered by the human merge. Effects outside the pipeline (manual production changes, destructive actions) need a Production Gate with target, blast radius, rollback and fresh verification.

## State

One directory per change: `.tasks/<ID>-<slug>/` with `state.json` (authoritative: gates, phase, security, `repo_write_scope`, `external_actions`), plus `plan.md` (and `review.md` for FEATURE+/security-sensitive) and `checkpoints/`. `session-handoff.md` only on deliberate worker switch. Never treat an unapproved gate as approved from chat.

## Human authority

Two human decisions: the Plan Gate (scope, architecture, security posture, write scope) and the merge. Agents prepare evidence and recommendations; they cannot approve.

## Escalation

If implementation reveals a fact that changes requirements, architecture, security invariants, data model, public contract or write scope: stop, mark blocked, describe the fact, return to the earlier phase, re-review/re-approve if materially affected.

## Evidence hierarchy

1. code/config/tests at current commit; 2. task state and approved artifacts; 3. Memory Bank; 4. authoritative external docs; 5. chat history. Surface conflicts; don't choose silently.

## Capabilities, dependencies, continuity

- Plugins/skills/tools: `.ai/plugin-governance.md`, `.ai/policies/external-actions.md`. Capabilities never govern the methodology.
- Dependency bots: `.ai/dependency-governance.md` (grouped minor/patch, major upgrades manual, never auto-merge, derived from the approved stack).
- Continuity: the repository owns it; new workers follow `.ai/workflows/resume.md`, and a worker change grants no new authority.
