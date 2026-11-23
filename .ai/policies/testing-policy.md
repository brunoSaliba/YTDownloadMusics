# Testing Policy

Testing depth follows risk, not file count. CI is the gate for the full suite.

## Testing budget

| Track | Tests to add |
|---|---|
| TASK | Only for the changed behavior: 0-2. Change an existing test before adding a new one. |
| BUGFIX | 1 regression test that fails before the fix. |
| FEATURE | One test per acceptance criterion. No extras "just in case". |
| EPIC / PROJECT | Strategy in `plan.md`; each slice follows the FEATURE rule. |
| Refactor, style, docs, CI config | No new test unless behavior changes. |

## Security-sensitive

Add negative tests **only** for the invariants listed in the threat model, one per invariant, for example: unauthenticated access, wrong role, cross-tenant access, tampered identifiers, malicious input, invalid signatures, timeout behavior, sensitive data in logs. Do not add generic adversarial suites.

## Running tests (cost discipline)

- Run only the affected files/tests while iterating (name filter). Batch edits, then run once.
- The full suite, typecheck and build run in CI. Run them locally only when the change touches shared code, configuration or dependencies.
- The Verifier reads existing output or CI results as evidence and does not re-run what already has fresh evidence.
- Truncate output (failures only). A flaky test is a determinism bug: fix it once; do not loop reruns.
- Same failure twice for the same reason: diagnose from the error before running again.

Passing tests are necessary evidence, not proof of security.
