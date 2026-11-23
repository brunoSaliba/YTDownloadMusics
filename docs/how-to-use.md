# Day-to-Day Usage

## New project

```text
INIT PROJECT

Build a customer portal for occupational exam orders integrated with SOC.
Backend .NET, frontend React, SQL Server, Docker/VPS are preferred, but validate the architecture before implementation.
```

Expected behavior: the agent creates `PROJ-000`, writes `plan.md` (charter, acceptance, architecture, threat model, bootstrap plan), then stops at the Plan Gate. No application code exists yet.

After you approve the Plan Gate, the scaffold may be created and the project decomposed into feature tasks.

## New feature

```text
Allow users to manually replace the automatically suggested provider. Require a justification and audit trail.
```

Expected behavior: Orchestrator classifies the work, assesses security risk, creates the task, produces/reviews spec and plan, waits at human gates, then implements/tests/reviews.

## Small bug

```text
Searching CPF with punctuation returns no employee.
```

Expected behavior: BUGFIX diagnose -> regression test -> minimal fix -> review. If the root cause touches authorization/tenancy or another security-sensitive property, it upgrades rather than staying on the fast path.

## Human approvals

A human can record an approval:

```bash
python tools/aip.py approve --task FEAT-001 --gate definition --by "Bruno"
python tools/aip.py approve --task FEAT-001 --gate plan --by "Bruno"
```

For security-sensitive work, after independent security review:

```bash
python tools/aip.py approve --task FEAT-001 --gate security --by "Bruno"
```

Agents are prohibited by `AGENTS.md` from executing these approvals on your behalf.

## Using plugins and skills

You do not disable useful plugins just because the repository has a methodology. The Orchestrator uses them in the appropriate phase.

Read-only example:

```text
Architecture phase -> Cloudflare plugin reads current platform docs/capabilities -> architecture artifact
```

External-write example before Plan Gate:

```bash
python tools/aip.py allow-action --task FEAT-001 \
  --plugin GitHub --action create_pr --effect EXTERNAL_WRITE \
  --target repository --purpose "Open PR after protocol checks"
```

After Plan Gate approval, this list is frozen. A newly desired side effect requires returning to Planning and re-approval.

For a production deployment, create the task with `--production-change`, complete the production plan and pre-production reviews, then a human records:

```bash
python tools/aip.py approve --task FEAT-001 --gate production --by "Bruno"
```

Only then may an approved production action execute. Afterward record fresh production verification.

## Switching AI workers / token limits

If Codex, Claude, Copilot, or another worker needs to stop, the preferred deliberate handoff is:

```bash
python tools/aip.py handoff --task FEAT-007 --agent "Codex" \
  --current-unit "Task 3 - Import preview" \
  --completed "Parser" \
  --completed "Validation" \
  --in-progress "Preview endpoint" \
  --verification "18 focused tests passed" \
  --next-action "Finish preview tests"
```

Open the same branch/repository in the next AI and say:

```text
RESUME
```

The next worker must read `.ai/workflows/resume.md` and produce a Resume Report before changing files. If exactly one task cannot be determined safely, give the task ID:

```bash
python tools/aip.py resume --task FEAT-007
```

If the previous worker ran out of tokens abruptly, do not reconstruct from chat. `RESUME` compares the current working tree to the last checkpoint and flags work that occurred afterward. Same-file changes after a checkpoint are detected with a working-tree fingerprint when Git evidence is available.

If plugin inventories differ, you may explicitly inventory the current environment:

```bash
python tools/aip.py resume --task FEAT-007 \
  --available-capability GitHub \
  --available-capability "Codex Security"
```

An unavailable Cloudflare/GitHub/etc. capability blocks only its approved external action. It does not authorize another mechanism and does not reset the task.

### Lightweight checkpoints during long work

Do not wait until the end of a session. After a meaningful unit and verification:

```bash
python tools/aip.py checkpoint --task FEAT-007 --agent "Claude" \
  --current-unit "Task 4 - Background processing" \
  --verification "Worker tests: 12 passed" \
  --next-action "Implement retry policy"
```


### Same folder vs another machine

`session-handoff.md` and checkpoint JSON do not contain a backup of source-code edits. If you open Claude/Codex against the same working directory, `RESUME` can inspect uncommitted changes. If you switch to a different clone/container/cloud workspace, persist the approved branch state first (for example, commit/push through the repository's approved Git workflow). A dirty handoff explicitly warns that it is not portable yet.
