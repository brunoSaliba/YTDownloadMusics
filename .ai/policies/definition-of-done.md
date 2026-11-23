# Definition of Done

A change is done only when every applicable item is true.

## Product and scope

- Acceptance criteria are satisfied.
- No unapproved scope expansion remains.
- Public/API/data-contract changes are documented.

## Engineering

- Build/typecheck/lint/format checks required by the stack pass.
- Unit/integration/end-to-end tests required by risk pass.
- Bug fixes include a regression test unless technically impossible and documented.
- External calls have appropriate timeout/error behavior.
- Migrations are forward/rollback-safe according to project policy.

## Security

- Security-sensitive classification is accurate.
- Threat model section of `plan.md` is updated when required.
- Negative authorization/security tests exist for material controls.
- No plaintext secret or credential is introduced.
- Sensitive data logging is reviewed.
- Dependency/supply-chain impact is reviewed.
- `## Security review` in review.md is filled (independent reviewer) when required.
- No unresolved Critical/High finding remains without explicit human risk acceptance.

## Knowledge

- `plan.md` and `review.md` reflect the final implementation.
- Durable architecture/security/ops knowledge is promoted to `.memory-bank/`.

## Delivery

- CI passes.
- PR clearly states what changed, why, tests, security impact, migrations/ops impact and known risks.
- Merge remains a human-controlled action.
