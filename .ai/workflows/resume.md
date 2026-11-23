# RESUME / Cross-AI Handoff Workflow

Use this workflow whenever a new model, agent, IDE agent, session, or tool environment continues work that another worker started.

## Non-negotiable rule

A worker change is **not** a new task and grants **no new authority**. Existing human approvals, security decisions, write scope, external-action allowlists, architecture, and requirements remain in force.

## Before modifying any file

1. Read `AGENTS.md`; open other policies only if the next action needs them.
2. Identify the current task. Prefer an explicit task ID; otherwise use the current branch/task artifacts and do not guess when multiple candidates exist.
3. Run `python tools/aip.py resume --task TASK-ID` when the CLI is available.
4. Read the current task's `state.json`.
5. Read `session-handoff.md` if present.
6. Read the latest checkpoint under `checkpoints/` if present.
7. Read the approved spec/architecture/plan/threat model relevant to the current phase.
8. Inspect live `git status`, `git diff`, branch, and HEAD.
9. Compare live Git evidence to the last checkpoint. Treat later or same-file changes as unverified work until inspected.
10. Inventory capabilities/plugins only when an approved external action depends on them.
11. Produce a short Resume Report before editing.

## Resume Report

Report:

- task ID, track, phase;
- last agent and checkpoint;
- current implementation unit and next action;
- human gate statuses;
- approved `repo_write_scope`;
- branch / HEAD / working-tree state;
- changes made after the last checkpoint or uncertainty about same-file changes;
- missing capabilities required for approved external actions;
- blockers or deviations from the approved plan.

## Recovery after abrupt session termination

A final handoff may not exist. That is expected.

When `session-handoff.md` is stale or absent:

- trust `state.json` for workflow authority;
- trust Git for actual repository changes;
- use the latest checkpoint only as the last known verified boundary;
- inspect all changes after that boundary;
- do not assume partially written code is correct or complete;
- rerun the smallest relevant verification before proceeding.

## Workspace boundary

A checkpoint stores state, paths, hashes and verification notes; it does **not** duplicate source code.

- Same working tree / same mounted repository: uncommitted work can be inspected directly.
- Different clone, VM, container, cloud agent or machine: the prior environment must persist/synchronize the branch through an approved mechanism before the new worker can see those code changes.
- If the prior environment disappeared before unsynchronized edits were persisted, record that loss explicitly; do not pretend the checkpoint can recreate them.
- Git push or another remote write remains subject to repository/plugin governance when it is an external side effect.

## Capability mismatch

If the new worker does not have a plugin/tool needed for an approved external action:

- mark only that action as currently unavailable;
- continue unrelated approved repository work when safe;
- never substitute a different side-effecting mechanism unless it is already approved or the task returns to Planning;
- never claim an external action occurred without evidence.

## Checkpoint cadence

`TASK`/`BUGFIX`: one checkpoint at the end of the task. `FEATURE`+: checkpoint at meaningful milestones after fresh verification (not every small unit). Always checkpoint before a deliberate model/session switch.

Use:

```bash
python tools/aip.py checkpoint --task TASK-ID --agent "Codex" \
  --current-unit "Task 3 - Preview endpoint" \
  --next-action "Finish preview integration tests" \
  --verification "18 focused tests passed"
```

## Deliberate handoff

When you know another worker will continue, create a richer handoff:

```bash
python tools/aip.py handoff --task TASK-ID --agent "Codex" \
  --current-unit "Task 3 - Preview endpoint" \
  --summary "Parser and validation are complete; preview service is partially implemented." \
  --completed "Parser" --completed "Validation" \
  --in-progress "Preview endpoint" \
  --verification "18 focused tests passed" \
  --decision "Preview does not persist records" \
  --known-issue "Pagination for validation errors is pending" \
  --next-action "Complete preview tests before background processing"
```

## Forbidden behavior

The new worker must not:

- restart the task merely because it prefers another design;
- silently rewrite approved architecture/specification;
- reset or self-approve gates;
- expand `repo_write_scope` or external actions;
- erase uncommitted work without first inspecting it;
- trust the prior agent's completion claim without fresh evidence;
- treat a plugin difference as authorization to bypass the approved mechanism.
