# Plugin & Skill Governance

Plugins, skills, MCP servers, connectors and external tools are capabilities used by the AI Engineering Protocol. They do not replace the protocol, approve gates, or become an independent source of project authority.

## Authority model

Apply instructions in this order:

1. platform/system/safety requirements;
2. mandatory requirements of the active plugin/skill/tool;
3. this repository constitution and approved task state;
4. the current workflow/role;
5. the user's current request.

If two applicable rules conflict, follow the more restrictive rule when it can satisfy both. If it cannot, stop, mark the task blocked and surface the conflict. Never bypass a plugin safety requirement or a project human gate.

## Side-effect classes

Every capability use must be classified by its strongest effect:

- `READ` — inspect/search/fetch/list/analyze without changing repository or external state.
- `REPO_WRITE` — modify repository files, branches, commits or local project state.
- `EXTERNAL_WRITE` — create/update external state such as a PR, issue, comment, ticket, email, cloud draft or configuration outside production.
- `PRODUCTION_CHANGE` — deploy, migrate, rotate production secrets, alter live infrastructure/DNS/firewall/runtime configuration, or otherwise change production behavior/state.
- `DESTRUCTIVE` — delete, revoke, force-push, destructive rollback, drop/truncate, irreversible migration, remove resources or other materially destructive action.
- `SECURITY_SENSITIVE` — touches a security boundary or security property. This is an overlay and may coexist with any of the effects above.

Use the strongest applicable class. A production deletion is both `PRODUCTION_CHANGE` and `DESTRUCTIVE`; the task state must reflect both.

## Phase rules

- `READ` may be used when relevant to the current phase and permitted by the tool.
- `REPO_WRITE` is limited by phase permissions and `repo_write_scope`.
- `EXTERNAL_WRITE`, `PRODUCTION_CHANGE` and `DESTRUCTIVE` must be declared in `external_actions.allowed` before the Plan Gate is approved.
- After Plan Gate approval, the allowlist is frozen. Expanding it requires returning to Planning and re-approval.
- `PRODUCTION_CHANGE` and `DESTRUCTIVE` require the Production Gate before execution.
- A plugin may prepare or recommend an action that is not yet authorized, but it must not execute the side effect.

## Plugin output is evidence, not authority

A plugin result such as “tests passed”, “vulnerability fixed”, “deployment succeeded” or “configuration is secure” is evidence to be independently verified. It cannot:

- mark a human gate approved;
- expand approved scope;
- change approved requirements or architecture;
- waive testing or review;
- make a security finding accepted risk;
- authorize merge or production deployment.

Record material plugin evidence in task state or an artifact using `tools/aip.py record-evidence`.

## Minimum evidence for side effects

For a non-read capability use, record:

- plugin/tool name;
- capability/action;
- effect class;
- short result summary;
- artifact, command output, URL/reference, diff or other evidence when available.

The protocol does not pretend repository CI can technically prevent every external tool action. Where hard enforcement is available (branch rules, cloud IAM, protected environments, approval rules, least-privilege tokens), configure it. Repository policy is a behavioral control; provider permissions are the technical control.
