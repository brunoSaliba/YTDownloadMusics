# GitHub Repository Security Setup

Repository files cannot fully enforce human merge authority by themselves. Configure repository/organization rules after creating a project from the template.

## Protect `main`

Create a branch ruleset targeting the default branch and enable at minimum:

- require a pull request before merging;
- require at least one human approval;
- dismiss stale approvals when new commits are pushed or require approval of the latest reviewable push;
- require status checks before merging;
- require the `Protocol gate` check from `AI Governance`;
- require stack-specific CI checks generated during `INIT PROJECT`;
- block force pushes;
- block branch deletion where appropriate.

For higher-risk repositories also consider required code scanning results, signed commits, merge queue and stricter reviewer requirements.

## GitHub Actions hardening

- Keep workflow `permissions` explicit and least privilege.
- Prefer immutable full-length commit SHAs for third-party and GitHub actions.
- Do not use privileged `pull_request_target` patterns to execute untrusted PR code with secrets.
- Review any workflow permission/secret change as security-sensitive.
- Limit which actions/reusable workflows are allowed when organization policy supports it.

## Secret protection

When available for the repository/account:

- enable secret scanning;
- enable push protection;
- review bypasses rather than normalizing them;
- rotate exposed credentials even after removing them from Git history when exposure is plausible.

The local `tools/aip.py` secret pattern check is intentionally small and high-confidence. It is not a substitute for a dedicated secret scanning service.

## Code/security scanning

During `INIT PROJECT`, generate scanning appropriate to the actual stack rather than pretending a language-agnostic template covers everything. Examples may include:

- GitHub CodeQL/code scanning for supported languages;
- package-manager dependency audit;
- container/IaC scanning when those artifacts exist;
- SAST/framework analyzers;
- migration/schema validation.

Make security checks required merge conditions where they provide reliable signal.


## Production environment / deployment protection

If GitHub Actions can deploy to production, create a protected `production` environment and require human reviewers/approval before deployment. Give the deployment job only the minimum environment secrets/permissions it needs.

The repository protocol treats merge and production deployment as separate decisions. Do not configure an unreviewed merge to bypass the Production Gate. If you intentionally use approved continuous deployment, document that policy explicitly and enforce equivalent provider/environment controls.


### Wire the gate into deployment workflows

A provider-specific deployment workflow should validate immediately before mutating production:

```bash
python3 tools/aip.py validate --task "$TASK_ID" --stage production --base origin/main
```

After the deployment, record and independently verify provider evidence, complete `production_verification`, then run:

```bash
python3 tools/aip.py validate --task "$TASK_ID" --stage post-production --base origin/main
```

The generic template cannot enforce a cloud provider action that happens outside GitHub; provider-side IAM/approval controls must mirror the repository policy.
