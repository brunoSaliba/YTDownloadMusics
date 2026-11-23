# External Action Policy

## Default

External side effects are denied unless they are explicitly included in the current task's approved plan. Read-only inspection is allowed when relevant and otherwise permitted.

## Allowlist

The task state contains `external_actions.allowed`. Each entry identifies:

- provider/plugin;
- action/capability;
- effect (`EXTERNAL_WRITE`, `PRODUCTION_CHANGE`, or `DESTRUCTIVE`);
- target/environment when known;
- purpose.

The Planner may populate the allowlist before Plan Gate approval. Once the Plan Gate is approved, agents must not expand it. New side effects require a return to Planning and a new Plan Gate approval.

## Production and destructive actions

A `PRODUCTION_CHANGE` or `DESTRUCTIVE` action additionally requires the Production Gate. Approval is specific to the task's approved action list and does not create standing permission for future tasks.

Examples:

- creating a pull request: `EXTERNAL_WRITE`;
- creating a staging Cloudflare Worker: usually `EXTERNAL_WRITE`;
- deploying to production: `PRODUCTION_CHANGE`;
- production database migration: `PRODUCTION_CHANGE`;
- dropping a production table: `PRODUCTION_CHANGE` + `DESTRUCTIVE`;
- force pushing a protected branch: `DESTRUCTIVE` and prohibited unless an explicit incident procedure permits it.

## Human-only decisions

Agents cannot record Definition, Plan, Security or Production Gate approval. They also cannot reinterpret a prior approval as covering a new external action.
