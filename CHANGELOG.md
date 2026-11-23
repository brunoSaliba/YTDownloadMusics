# Changelog

## v3 — Cross-AI Handoff and Recovery

- Added vendor-neutral `RESUME` workflow for changing AI model, coding agent, IDE agent, or session mid-task.
- Added per-task `session-handoff.md` and immutable `checkpoints/` snapshots.
- Added `aip checkpoint`, `aip handoff`, and `aip resume` CLI commands.
- Added Git branch/HEAD/working-tree capture and fingerprints to detect work after the last checkpoint, including same-file changes.
- Added explicit preservation rules: worker changes cannot reset gates, expand write scope, change approved external actions, or silently rewrite approved design.
- Added missing-capability reporting for plugin/tool differences between AI environments; only affected external actions are blocked.
- Added abrupt-session recovery that treats Git as evidence when no final handoff exists.
- Upgraded task state schema to v3 with continuity metadata.

## v2 — Plugin and Production Governance

- Added explicit plugin/skill/tool authority model.
- Added side-effect classification: READ, REPO_WRITE, EXTERNAL_WRITE, PRODUCTION_CHANGE, DESTRUCTIVE and SECURITY_SENSITIVE overlay.
- Added external action allowlist frozen by Plan Gate.
- Added Production Gate for live/destructive operations.
- Added production plan and post-production verification.
- Added plugin/tool evidence recording and independent evidence verification.
- Added CLI enforcement preventing write-scope/action expansion after Plan Gate.
- Added re-review behavior when a newly discovered production/security boundary invalidates an earlier definition.
- Added GitHub workflow support for PR, production and post-production protocol validation.
- Added provider-side enforcement guidance for protected environments and least-privilege credentials.
