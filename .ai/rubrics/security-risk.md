# Security Risk Rubric

Assess inherent risk before implementation.

## High-risk triggers

Treat as High unless strong evidence justifies Medium:

- authentication/session/account recovery;
- authorization or multi-tenant isolation;
- admin/privileged operations;
- cryptographic key/signature logic;
- secrets/credentials lifecycle;
- remote code/process execution;
- untrusted file/archive/document parsing;
- user-influenced outbound requests;
- payment/entitlement state;
- internet-facing infrastructure or CI/CD credential changes;
- regulated or highly sensitive data exposure paths.

## Medium-risk examples

- new authenticated endpoint with ordinary business data;
- new external API integration without sensitive credentials crossing client boundaries;
- database query changes affecting access patterns;
- new background job or webhook with bounded privilege.

## Low-risk examples

- presentation-only text/style change;
- internal refactor with unchanged boundaries and behavior;
- documentation-only change without security policy impact.

## Consequences

- Low: normal workflow.
- Medium: explicit security acceptance criteria and reviewer attention.
- High: threat model (plan.md section) + independent Security Reviewer + filled `## Security review` in review.md, checked by CI and the human merge.
