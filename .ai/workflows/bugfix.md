# Workflow — BUGFIX

1. Diagnose and reproduce; record expected vs actual and root-cause evidence (brief).
2. Assess security sensitivity; upgrade/overlay when relevant.
3. Short plan and write scope.
4. Add a failing regression test when feasible.
5. Smallest correct fix.
6. Run the affected tests; full suite/typecheck/build once at the end.
7. One separate in-context review pass over the diff (no subagent unless security-sensitive, then security review per AGENTS.md §7).
8. Retrospective only if the learning is non-trivial and durable.
9. One checkpoint at the end, then PR for human review/merge.

If the fix needs new product behavior, architecture change or a new trust boundary, upgrade to FEATURE.
