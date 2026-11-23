# Example Plugin Capability Map

This file is an example, not a declaration of installed tools. Copy relevant entries into project-specific documentation only after verifying the actual capabilities and permissions available.

| Capability | Typical phases | Normal effects | Notes |
|---|---|---|---|
| GitHub | discovery, review, delivery | READ, EXTERNAL_WRITE | Reading issues/PR/CI is READ. Creating PR/issues/comments is EXTERNAL_WRITE. Merge remains human/protected. |
| Security scanner / Codex Security | architecture, threat modeling, verification, security review | READ, REPO_WRITE only when explicitly fixing | Findings are evidence; acceptance of residual risk is human. |
| Cloud provider | architecture, ops planning, deployment | READ, EXTERNAL_WRITE, PRODUCTION_CHANGE, DESTRUCTIVE | Production mutation requires Production Gate and provider-side least privilege. |
| Planning/TDD skills | discovery, planning, implementation, verification | READ, REPO_WRITE | Skill workflow requirements compose with this protocol; stricter gates win. |
| Database admin tooling | architecture, migration planning, operations | READ, PRODUCTION_CHANGE, DESTRUCTIVE | Production migrations and destructive DB changes require explicit authorization and rollback/roll-forward planning. |

## Project rule

Do not assume a plugin is installed, connected, or authorized because it appears in this example. Inspect the actual tool/permission state when the task needs it.
