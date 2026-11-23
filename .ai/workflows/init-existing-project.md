# Workflow — INIT EXISTING PROJECT

Use when adopting the protocol in an existing codebase.

## Read-only discovery first

Do not change product behavior during adoption.

Inventory:

- repository structure and languages;
- runtime/deployment topology;
- data stores/migrations;
- authentication/authorization/tenancy;
- external integrations;
- sensitive data and secrets/config strategy;
- CI/CD and branch protections that are visible;
- tests and quality tooling;
- dependency/supply-chain approach;
- logging/monitoring/backup/rollback documentation;
- known technical/security debt supported by evidence.

If the repository deploys to the SOHMA-style VPS/GHCR model, read `.ai/deployment-standard.md`. If it targets the shared `*.bneli.tech` VPS, also read `.ai/platforms/bneli-vps.md`.

During adoption, distinguish repository-observed deployment configuration from live-host state. Do not claim that ports, NGINX sites, certificates, firewall rules, running containers or GHCR credentials are current unless verified on the VPS.

If port allocation or deployment normalization is part of a later approved task, first request fresh operator evidence:

```bash
echo '=== occupied sockets ==='
ss -tulpn
echo '=== docker ==='
docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo '=== nginx ==='
ls -la /etc/nginx/sites-enabled
```

Do not modify product/runtime deployment behavior merely as part of protocol adoption. Any normalization becomes separate governed work unless explicitly included and approved.

## Build Memory Bank

Create/update:

- `.memory-bank/project/project-charter.md`;
- `.memory-bank/system/architecture.md`;
- `.memory-bank/system/data-and-security.md`;
- `.memory-bank/system/integrations.md`;
- `.memory-bank/ops/deployment.md`;
- root `SECURITY.md` with real boundaries/invariants.

For SOHMA-style deployment, `.memory-bank/ops/deployment.md` should record observed repository facts separately from unverified live-host assumptions, including image registry, Compose model, NGINX topology, loopback bindings, build-time frontend variables and known operational unknowns.

## Threat model

Identify assets, actors, trust boundaries, important entry points and security invariants. Do not claim controls exist merely because documentation says so; distinguish observed implementation from intent.

## Review and checkpoint

Present current architecture, security posture, deployment posture, confidence/unknowns and recommended protocol adoption changes. Governance-file adoption may proceed as approved; unrelated refactoring, deploy normalization or platform hardening becomes separate tasks.
