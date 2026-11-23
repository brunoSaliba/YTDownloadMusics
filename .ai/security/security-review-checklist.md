# Security Review Checklist

The Security Reviewer adapts this checklist to the actual change.

## Scope and model

- [ ] Security-sensitive classification is correct.
- [ ] Threat model/security invariants match the final implementation.
- [ ] New trust boundaries and assets are documented.

## Authentication / authorization

- [ ] Protected operations require server-side authorization.
- [ ] Object and tenant boundaries have negative tests.
- [ ] Client-controlled identifiers/claims cannot expand access.
- [ ] Admin/privileged paths use least privilege and are auditable.

## Inputs and execution

- [ ] Untrusted inputs are validated at boundaries.
- [ ] Query/command/template/deserialization contexts use safe APIs.
- [ ] File parsing/upload is bounded and type-validated where relevant.
- [ ] User-influenced outbound requests are constrained.

## Data / secrets

- [ ] Secrets are externalized and redacted from logs/errors.
- [ ] Sensitive data collection/logging/retention is minimized.
- [ ] Encryption/security-sensitive primitives use established libraries.

## Integrations / availability

- [ ] External calls have timeouts and bounded retries.
- [ ] Webhook/signature/replay controls are correct when relevant.
- [ ] Idempotency/resource/rate limits exist where abuse or retries matter.

## Supply chain / operations

- [ ] New dependencies/actions/images are justified and reviewed.
- [ ] CI/CD permissions and secret exposure are least privilege.
- [ ] Deployment/config changes do not broaden exposure unexpectedly.

## Findings

- [ ] Critical/High issues are fixed or explicitly human-accepted with rationale.
- [ ] Residual risk is documented.
- [ ] `## Security review` in review.md is filled and ready for the human PR reviewer.
