# Workflow — TASK

Small, well-bounded, low-uncertainty change. Lightweight by design; security and human merge are unchanged.

0. `python tools/aip.py classify` on the planned paths; TASK/BUGFIX only if it says so. No checkpoints/state detail beyond the final one.
1. Short plan (≤15 lines in `plan.md`): goal, files, test approach. No PRD, spec, architecture or threat model.
2. Quick security check (`.ai/rubrics/security-risk.md` only if unsure). Medium/High or security-sensitive → upgrade to FEATURE.
3. Define `repo_write_scope`.
4. Implement.
5. Test the changed behavior (targeted tests; full suite/typecheck/build once at the end).
6. One separate in-context review pass over the diff (no subagent); note the result in 3-6 lines.
7. Update docs / Memory Bank only if durable reality changed. No retrospective.
8. One checkpoint at the end, then PR for human review/merge.
