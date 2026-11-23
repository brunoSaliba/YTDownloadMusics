# Workflow — FEATURE

One `plan.md` (goal + acceptance, architecture if changed, threat model if security-sensitive, scope, tests) and one `review.md`.

1. Write `plan.md`: acceptance criteria, architecture only if boundaries change, threat model if security-sensitive, exact `repo_write_scope`, test plan within the testing budget.
2. One fresh reviewer checks `plan.md` (brief: `.ai/templates/subagent-brief.md`).
3. **Plan Gate** (human): approves definition and plan together.
4. Implement in small testable increments; run only affected tests.
5. Tester adds tests per acceptance criterion (negative tests only for security invariants).
6. Verifier maps existing evidence (CI/test output) to acceptance criteria; does not re-run what already has fresh evidence.
7. Code Reviewer reviews the diff; Security Reviewer when required. Both write into `review.md`.
8. Promote durable facts to `.memory-bank/`; no separate retrospective.
9. One checkpoint, CI, PR.
10. **Human merge** approves code and, if security-sensitive, the `## Security review` section.
