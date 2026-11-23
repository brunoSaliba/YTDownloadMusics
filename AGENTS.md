# AI Engineering Protocol — Constitution

Applies to every AI agent and subagent. Repository state (`.tasks/<id>/state.json`, Git) outranks chat; if they disagree, stop and surface it.

## 1. Core rule

Never implement straight from a request. First: classify (§2), assess security (§3), identify/create the task in `.tasks/`, read only what the track needs, follow `.ai/workflows/<track>.md`, respect gates and `repo_write_scope`. New worker/model/session → `.ai/workflows/resume.md`.

| Track | Always read | Only if relevant |
|---|---|---|
| TASK / BUGFIX | this file + track workflow | `.memory-bank/` docs touching the change |
| FEATURE / EPIC / PROJECT | + `.ai/methodology.md` | relevant Memory Bank docs, roles, templates |
| Security-sensitive | + `.ai/security/security-baseline.md`, `.ai/workflows/security-sensitive-change.md` | rest of `.ai/security/` |

Read the Memory Bank `README.md` index and only needed documents. Do not read closed tasks, `docs/`, `README.md` or `CHANGELOG.md` unless resuming, cited or asked. Plugin, deployment and production docs: only when used. Never re-read a file already in context.

## 2. Classification

`HOTFIX`, `BUGFIX`, `TASK` (small, bounded), `FEATURE`, `EPIC`, `PROJECT` (init). Run `python tools/aip.py classify` (rules in `.ai/rubrics/complexity.md`, per-project overrides in `.ai/classify.json`) before choosing the track; it only escalates. One goal = one task = one PR. Upgrade on hidden complexity; never downgrade to bypass governance.

## 3. Security

Security-sensitive = touches a trust boundary or security property (authn/z, tenancy, secrets, crypto, sensitive data, uploads/parsing, outbound URLs/webhooks, injection/exec surfaces, payments, privileged jobs, audit logs, CI/CD/IaC/containers/prod config, privileged dependencies, abuse controls, new internet-facing endpoint). Unsure → read `.ai/rubrics/security-risk.md`.

Then: minimum track `FEATURE` (except genuine `HOTFIX`), a `Threat model` section in `plan.md` with explicit invariants, negative tests for those invariants, an independent `## Security review` in `review.md` (CI fails without it), residual risk recorded. Scanner pass ≠ safe.

## 4. Human gates

Two gates: (1) **Plan Gate** for `PROJECT`/`FEATURE`/`EPIC` — approves definition (acceptance, architecture, threat model) and plan/write scope together, before code; (2) **human PR review/merge** — for security-sensitive work it also approves the `## Security review`. A **Production Gate** exists only for effects outside the CI/CD pipeline (manual VPS changes, destructive migrations, data deletion); a deploy the pipeline runs on merge is covered by the merge.

Agents never: approve a gate, edit approval metadata, infer approval from silence, merge to `main`, weaken branch protection/CI/scanning/policy, or mutate production outside the pipeline without the Production Gate.

## 5. Plugins, skills, MCP, external tools

Subordinate to this protocol; read `.ai/plugin-governance.md` only when one is used. Output is evidence, never approval. Non-read external actions must be in `external_actions.allowed` before Plan Gate (frozen after). Production/destructive → Production Gate.

## 6. Phases and scope

Before implementation (discovery→planning): no application-code changes; write only task, `.memory-bank/`, design docs. Implementation: only approved scope; need more → back to Planning. Review phases: read-only except review artifacts.

## 7. Review proportional to risk

| Work | Review |
|---|---|
| TASK / BUGFIX, not sensitive | One separate in-context pass over the diff (`.ai/roles/code-reviewer.md`), noted in 3-6 lines. No subagent. |
| FEATURE / EPIC / PROJECT | One fresh reviewer for `plan.md` before the Plan Gate; fresh subagent for code review (+ verification reading existing evidence). |
| Security-sensitive | Fresh subagent for security review (else separated pass, limitation recorded). Author is never the only security reviewer. |
| HOTFIX | Minimal review before merge, full after. |

Subagents get a narrow brief (`.ai/templates/subagent-brief.md`): diff, criteria, specific files — not the whole protocol.

## 8. Implementation discipline

Execute approved requirements; invent none. Smallest coherent change, repo conventions. Server-side validation/authorization, fail closed, parameterized data access, no secrets in source/logs, timeouts on external calls, least privilege, no new dependency without need and review. Shared VPS/GHCR targets: `.ai/deployment-standard.md`; live VPS changes need the Production Gate; never commit real tokens.

Testing: follow the budget in `.ai/policies/testing-policy.md` (TASK 0-2 tests, BUGFIX 1 regression, FEATURE 1 per acceptance criterion; negative tests only for threat-model invariants). Run only affected tests; CI runs the full suite; Verifier reads existing evidence; truncate output; same failure twice → diagnose, don't re-run.

## 9. Completion

Per `.ai/policies/definition-of-done.md`: criteria met, checks pass, review per §7, no unresolved Critical/High without human risk acceptance, docs/Memory Bank updated, CI green, PR ready for human review. Artifacts: `TASK` = short `plan.md`; `BUGFIX` = short `plan.md` (root cause + regression test); `FEATURE`/`EPIC`/`PROJECT` and security-sensitive = `plan.md` + `review.md`. Requirements, architecture, threat model and production plan are sections of `plan.md`; code review, verification and security review are sections of `review.md`. No PRD, spec, retrospective or session-handoff files (handoff only on deliberate worker switch).

## 10. Continuity and Memory

`state.json`, Git and approved artifacts are authoritative; `session-handoff.md` is context only. Checkpoint once at the end of TASK/BUGFIX, at milestones for FEATURE+, and before a deliberate worker switch (`python tools/aip.py checkpoint|handoff|resume`). No secrets in handoffs. At the end promote only durable facts to `.memory-bank/`, briefly.

## 11. Commands

`INIT PROJECT` → `init-project.md` · `INIT EXISTING PROJECT` → `init-existing-project.md` · `RESUME` → `resume.md` · hotfix/bug/task/feature/epic → `.ai/workflows/<name>.md` (overlays: `security-sensitive-change.md`, `production-change.md`).
