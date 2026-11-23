# Workflow — INIT PROJECT

Use when starting a new product from this template.

## Phase 0 — Initialize governance

- Create `.tasks/PROJ-000-init/` with `state.json` based on the task template.
- Set track `PROJECT`, phase `discovery`, implementation blocked.
- Inventory all information the human supplied.
- Do not scaffold application code.

## Phase 1 — Discovery

Produce a concise discovery record covering:

- product problem and success outcome;
- users/actors and roles;
- core workflows;
- integrations;
- data types/classification;
- deployment/operational expectations;
- non-functional needs;
- legal/contract/privacy/security constraints explicitly known;
- unknowns that materially affect design.

Avoid interrogating the human for low-value details. Make reasonable, clearly labeled assumptions where they are reversible; escalate decisions that affect scope, security, architecture or cost.

If the intended deployment target is the shared SOHMA-style VPS/GHCR model, read `.ai/deployment-standard.md`. If the target is the shared `*.bneli.tech` VPS, also read `.ai/platforms/bneli-vps.md`.

Known VPS inventory is context only. **Before fixing host ports, request fresh operator evidence** with:

```bash
echo '=== occupied sockets ==='
ss -tulpn
echo '=== docker ==='
docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo '=== nginx ==='
ls -la /etc/nginx/sites-enabled
```

Do not choose or reserve ports until the returned evidence has been reviewed.

## Phase 2 — Product definition

Product Manager creates:

- `.memory-bank/project/project-charter.md`;
- the `Goal and acceptance criteria` section of the task `plan.md`.

Include functional and non-functional security requirements from the beginning.

## Phase 3 — Technical specification

Specification Engineer adds to `plan.md` testable behavior, contracts, validation/errors and security acceptance criteria.

## Phase 4 — Architecture + threat model

Architect adds the `Architecture` section to `plan.md`, relevant ADRs and initial durable system docs.

Security Reviewer writes/validates the `Threat model` section of `plan.md` and data classification.

Architecture must cover, as applicable:

- modules/components;
- data storage;
- auth/authz/tenancy;
- integrations;
- background work;
- observability/audit;
- deployment/runtime;
- secrets/configuration;
- CI/CD security strategy;
- backup/restore and failure handling.

If the shared VPS/GHCR standard applies, architecture/deployment decisions must explicitly cover:

- Dockerized services;
- GHCR image naming and service boundaries;
- host NGINX reverse proxy;
- loopback-only app host bindings;
- selected host ports backed by fresh VPS evidence;
- no host-published PostgreSQL port;
- GitHub build-time repository variables for `NEXT_PUBLIC_*` where applicable;
- GHCR private-pull authentication without repository-stored credentials.

## Phase 5 — Independent artifact review

One fresh reviewer checks the `plan.md` sections (scope, architecture, threat model). Resolve findings before the Plan Gate.

## Human Plan Gate (definition + plan)

Present:

- product scope;
- architecture;
- important security invariants;
- major trade-offs;
- data classification;
- risks/unknowns;
- decisions requiring human acceptance.

Stop until explicit human approval is recorded. Application code remains prohibited.

## Phase 6 — Bootstrap implementation plan

Planner completes `plan.md` for repository scaffold and first delivery slices. Define exact `repo_write_scope`. The Plan Gate is requested once, after this phase, covering the definition above and the plan.

Plan stack-specific quality/security automation, such as:

- build/test/lint/typecheck;
- dependency vulnerability audit;
- SAST/code scanning appropriate to languages;
- container/IaC scanning if applicable;
- migration checks;
- secret scanning/push protection integration;
- deployment safety checks.

### Dependency management setup

Read `.ai/dependency-governance.md`.

Dependency automation must be derived from the architecture that was approved at the Plan Gate. The generic template configures only GitHub Actions; do not assume `npm`, `pip`, `nuget`, Maven or any other application ecosystem before the architecture establishes it.

The bootstrap plan must state:

- which package ecosystems are actually used by the approved stack;
- which ecosystems will be added to `.github/dependabot.yml`;
- weekly grouped minor/patch version updates by default;
- low simultaneous routine PR limits;
- semver-major version upgrades excluded from routine automated version-update PRs by default;
- security updates remain prioritized and are not silently ignored;
- no dependency auto-merge;
- CI and human review remain mandatory.

Major upgrades discovered later must be handled as explicit `TASK`/`FEATURE` work with impact and migration analysis rather than routine bot maintenance.

### Deployment setup

When the SOHMA-style deployment standard is approved, read `.ai/deployment-standard.md` and include only the applicable deployment artifacts, normally:

- `.github/workflows/ci.yml`;
- `.github/workflows/publish.yml`;
- `deploy/docker-compose.yml`;
- `deploy/nginx/<domain>.conf`;
- `deploy/.env.example`;
- documentation of required GitHub repository variables and host-side configuration.

The production Compose uses prebuilt `image:` references plus `pull_policy: always`; application ports published to the host bind only to `127.0.0.1`. Host NGINX/Certbot installation commands are production actions and are not executed during repository scaffold.

## Human Plan Gate

Show planned repository structure, dependencies, workflows, write scope, delivery slices and test/security gates. Stop until explicit approval.

## Phase 7 — Scaffold

Only now create application/source code and stack-specific CI according to the plan.

Configure `.github/dependabot.yml` for the approved stack exactly as authorized in the bootstrap plan. Do not enable application ecosystems that were not approved.

If the SOHMA-style deployment standard is approved, create/review the planned repository deployment artifacts without performing live VPS mutations. Validate Compose configuration and workflow syntax where tooling permits.

Validate a clean build/test baseline before beginning product features.

## Phase 8 — Feature delivery

Create separate tasks for approved delivery slices and use FEATURE/EPIC workflows. `PROJ-000` closes only after the initial scaffold and project Memory Bank accurately describe the real system.
