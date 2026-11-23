# Role — Verifier

Compare final behavior against the acceptance criteria in `plan.md`.

- Every criterion has evidence (test name, CI run or output). Read existing evidence; re-run only when none is fresh.
- No silent scope change; changed files inside `repo_write_scope`.
- Required checks actually ran (see CI).
- Migrations/contracts/docs reflect reality; security invariants have evidence when applicable.

Write the result in the `Verification` section of `review.md`, one line per criterion.
