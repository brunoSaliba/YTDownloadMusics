# Security Baseline

This baseline applies during design, implementation and review. Project-specific `SECURITY.md` and threat models may impose stricter requirements.

## 1. Security requirements begin in Discovery

Identify confidentiality, integrity, availability, authenticity and privacy expectations for important assets. Security acceptance criteria belong in the PRD/specification, not only in a final review.

Use OWASP ASVS 5.0.0 as a verification reference for applicable web application controls. Select requirements based on actual architecture and risk.

## 2. Identity and access

- Separate authentication from authorization.
- Enforce authorization server-side for every protected operation and object.
- Prefer deny-by-default / least privilege.
- Derive tenant/customer scope from trusted server-side identity/context.
- Never trust a client-provided company/tenant/user identifier as proof of access.
- Test horizontal and vertical privilege boundaries.
- Sensitive account recovery/session changes require explicit abuse-case analysis.

## 3. Secrets and cryptography

- Never commit production secrets or put server secrets in frontend bundles.
- Use environment/secret stores appropriate to deployment.
- Scope credentials to the minimum service, environment and permission set.
- Do not log secrets, authorization headers, tokens or private keys.
- Prefer established cryptographic libraries and protocols; do not invent cryptography.
- Rotation/revocation must be possible for material credentials.

## 4. Data protection

- Classify data using `.ai/security/data-classification.md`.
- Minimize collection and retention.
- Restrict access by business need.
- Define encryption-in-transit and at-rest expectations based on risk.
- Avoid sensitive fields in logs, analytics, exception payloads and URLs.
- Define deletion/export/audit requirements when regulation or contracts require them.

## 5. Input, output and injection

- Validate untrusted input at trust boundaries using allowlists/typed parsing where practical.
- Parameterize database queries.
- Use contextual output encoding and safe framework APIs.
- Avoid shell commands; when unavoidable, never concatenate untrusted input.
- Treat deserialization, template engines and dynamic evaluation as security-sensitive.

## 6. File and document handling

For uploads/imports/parsers:

- authenticate/authorize before upload;
- allowlist required file types and validate actual content, not only extension/header;
- enforce size/count/row/page/decompression/resource limits;
- generate server-side storage names/paths;
- store outside executable/public paths unless explicitly designed otherwise;
- scan or sandbox where risk warrants it;
- never process a file before security validation appropriate to its type;
- safely generate downloads and content types.

## 7. Outbound network and integrations

- Define allowed destinations and protocols.
- Constrain user-controlled URLs and redirects.
- Use timeouts and bounded retries.
- Validate TLS and signatures/tokens as designed.
- Treat webhook authenticity/replay protection explicitly.
- Isolate client-specific credentials from global/master credentials wherever blast radius matters.

## 8. Availability and abuse

- Bound expensive inputs and pagination.
- Apply rate limits where abuse matters.
- Avoid unbounded retries, queues, recursion, decompression or memory growth.
- Define idempotency for retried state-changing operations.

## 9. Logging and audit

- Log security-relevant actions with actor, action, target, result and timestamp where appropriate.
- Never make logs a secret store.
- Protect audit integrity and access.
- Make failures observable without leaking sensitive internals to clients.

## 10. Supply chain and CI/CD

- Treat dependencies, build actions and base images as trust decisions.
- Prefer minimal dependencies.
- Pin GitHub Actions to immutable full commit SHAs where possible.
- Set workflow `permissions` explicitly and minimally.
- Do not expose privileged secrets to untrusted PR code.
- Review workflow/IaC/container changes as security-sensitive.
- Generate stack-specific dependency/SAST/container scanning during project initialization.

## 11. Security verification

Use multiple evidence types: tests, static analysis, dependency analysis, manual review and threat-model reasoning. No scanner can prove business-logic authorization or secure design.
