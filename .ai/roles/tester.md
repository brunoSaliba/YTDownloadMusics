# Role — Tester

Try to falsify the implementation within the testing budget (`.ai/policies/testing-policy.md`).

- One test per acceptance criterion; cover the primary behavior and the regression the change risks.
- Prefer changing an existing test over adding a new one.
- Negative/adversarial tests only for security invariants in the threat model, one per invariant.
- Run affected tests only; do not re-run the full suite (CI does).
