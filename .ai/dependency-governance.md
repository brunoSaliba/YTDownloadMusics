# Dependency Automation Governance

Dependency automation is subordinate to the AI Engineering Protocol. It exists to surface maintainable updates, not to bypass planning, testing, review, or human merge control.

## 1. Ecosystems follow approved architecture

Do not enable application-package ecosystems in Dependabot before the stack is part of the approved project architecture.

Examples:

- Next.js + FastAPI -> `npm`, `pip`, `github-actions`
- React + .NET -> `npm`, `nuget`, `github-actions`
- .NET only -> `nuget`, `github-actions`

The generic template should configure only `github-actions`. Application ecosystems are added during `INIT PROJECT` after the Plan Gate and as part of the approved bootstrap plan.

## 2. Routine version updates

For normal version updates:

- schedule weekly by default;
- group minor and patch updates by ecosystem;
- keep the number of simultaneous routine PRs low;
- never auto-merge dependency PRs;
- require the repository's normal CI and human review rules.

## 3. Major upgrades

Major dependency upgrades are not routine maintenance.

Do not configure Dependabot version updates to open automatic semver-major PRs by default.

A major upgrade must become an explicit `TASK` or `FEATURE` and include, as applicable:

- impact analysis;
- upstream migration/breaking-change review;
- dependency and runtime compatibility review;
- implementation plan;
- tests/build/lint/type checks;
- security review when the dependency affects a trust boundary, build/runtime privilege, CI/CD, authentication, authorization, data handling, or supply chain;
- human-reviewed PR.

## 4. Security updates

Security updates remain high priority and must not be silently ignored merely because routine major version updates are disabled.

When a security advisory requires a major upgrade or otherwise material migration, create an explicit security-sensitive task and prioritize it according to realistic exposure and impact.

Passing dependency scanners is evidence, not proof of safety.

## 5. INIT PROJECT behavior

After architecture is approved, the Planner must include dependency-management setup in the bootstrap plan:

1. identify the approved package ecosystems;
2. add only those ecosystems to `.github/dependabot.yml`;
3. group routine minor/patch updates;
4. keep major version updates manual by default;
5. preserve security-update handling;
6. require CI and human review;
7. do not enable auto-merge.

Any later change to dependency automation is repository governance work and must follow its own task/scope when it changes files outside the active task's approved `repo_write_scope`.
