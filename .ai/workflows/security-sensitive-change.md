# Workflow Overlay — Security-Sensitive Change

Apply this on top of the selected track whenever `security_sensitive=true`.

## Before implementation

- Set security risk level and rationale in `state.json`.
- Read root/nested `SECURITY.md`.
- Complete the `Threat model` section of `plan.md`.
- State the security invariants this change must preserve.
- Classify affected data.
- Add explicit abuse cases/negative acceptance criteria.
- Review credential/secret blast radius and least privilege.
- Review supply-chain impact for new dependencies/actions/images.

## Plan

Plan must include concrete security verification evidence, not "run security scan" as a substitute for reasoning.

Examples:

- unauthorized and cross-tenant tests;
- signature/replay tests;
- malicious/boundary file parser tests;
- SSRF/network allowlist tests;
- secret/log redaction checks;
- privilege/CI permission review;
- fail-closed behavior under dependency failure.

## Implementation

Do not weaken a security control to unblock functionality. If requirements conflict with an invariant, stop and escalate.

## Review

A fresh Security Reviewer independently reviews the plan/threat model, implementation diff and tests, and fills `## Security review` in `review.md` (CI fails without it).

Critical/High findings block completion unless a human owner explicitly accepts residual risk with rationale.

## Security approval (at human merge)

There is no separate Security Gate. The human PR reviewer approves security by merging, after reading `## Security review`:

- security invariants;
- findings and fixes;
- residual risk;
- operational/credential/migration implications.
