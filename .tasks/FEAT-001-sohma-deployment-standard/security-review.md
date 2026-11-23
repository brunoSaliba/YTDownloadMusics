# Security Review

## Result

`APPROVED`

Independent review was performed by a fresh agent ([Security review FEAT-001](c94ca29b-82c9-4f08-a1c7-3c9b4795994a)). No Critical or High findings. The one Medium that contradicted approved PRD/spec/threat-model (PostgreSQL host-publish exception) was fixed in-scope.

The current implementation is considered safe for Security Gate approval **with explicit human acceptance** of two non-blocking residual Medium items that are outside the approved specification and plan (production SHA/digest pin; generated `publish.yml` least privilege). Those items were not implemented in this task.

This artifact is not human Security Gate approval. `gates.security` must remain `pending`. An agent must not copy this review into gate approval fields.

## Security boundary reviewed

- Governance/policy for shared VPS + GHCR: image publish/pull, host exposure, credentials, production mutations.
- Trust boundaries: GitHub Actions → GHCR; VPS host → Docker/Compose; host NGINX → loopback app ports; operator → live infrastructure.
- This task does not mutate a host (`effects.production_change=false`, `external_actions.allowed=[]`).
- Classification `security_sensitive=true`, risk `high` is correct. CI/CD and deployment-policy changes are security-sensitive per the constitution.

## Invariants verified

| Spec invariant | Verdict | Evidence |
|---|---|---|
| Never publish host 80/443/22/5432 from application Compose | **MET** | `.ai/deployment-standard.md:18`; `AGENTS.md:184`; `.ai/platforms/bneli-vps.md:33` |
| Never expose app services on `0.0.0.0` when behind host NGINX | **MET** | Required bind `127.0.0.1:<port>:<container-port>` (`.ai/deployment-standard.md:17`). Grep of implementation files: no `0.0.0.0`. |
| Never place a real PAT/token in repository text or example commands | **MET** | Login example is `read -s` + stdin + `unset` (`.ai/deployment-standard.md:107-110`). Workspace grep: no `ghp_` / `github_pat_` / `gho_`. |
| Never treat stale VPS inventory as evidence a port is free | **MET** | Snapshot warning (`.ai/platforms/bneli-vps.md:5`); fresh `ss` / `docker ps` / NGINX listing required in standard, profile, init, and production overlay. |
| Never infer merge authorization permits a live deployment | **MET** | `.ai/deployment-standard.md:5`; `.ai/workflows/production-change.md:44`; `AGENTS.md:50` |

## Findings

| Severity | Finding | Reachability / impact | Evidence | Required action |
|---|---|---|---|---|
| Medium (fixed) | PostgreSQL host-publish exception in the “non-negotiable” list | Agent could publish Postgres on a non-5432 host port, contradicting PRD/architecture/threat model | Pre-fix `.ai/deployment-standard.md:19` | Exception removed. Host PostgreSQL publish is forbidden (`.ai/deployment-standard.md:19,40`; overlay `:34`). |
| Medium (residual, non-blocking) | Production Compose is specified as `image:` + `pull_policy: always` without requiring `:commit-sha` or digest pin; `:latest` is documented as a publish tag | Downstream compose-up can pull a mutable tag. Overlay already requires verifying digest rather than assuming `latest` (`.ai/workflows/production-change.md:36`) | `.ai/deployment-standard.md:12-15,35-38`; threat model requires *publishing* SHA tags, not *deploying* them | Out of approved specification/plan. Not fixed in this task. Documented as residual risk; human residual-risk acceptance required at Security Gate. |
| Medium (residual, non-blocking) | Mandated `publish.yml` / `ci.yml` do not yet require least-privilege `permissions:`, SHA-pinned actions, or “no GHCR write on `pull_request`” | Future scaffolded workflows are the GHCR write boundary. This template’s `ai-governance.yml` already uses `permissions: contents: read` and SHA-pinned checkout; the new standard does not copy that pattern | `.ai/deployment-standard.md:30-34` vs `.github/workflows/ai-governance.yml`; `.ai/security/security-baseline.md` §10 | Out of approved specification/plan. Not fixed in this task. Documented as residual risk; human residual-risk acceptance required at Security Gate. |
| Low | GHCR host-pull example does not require `packages:read` / pull-only credential | Stolen write-capable PAT on the VPS expands blast radius | `.ai/deployment-standard.md:101-115` | Residual; least privilege is already a constitution rule. |
| Low | `NEXT_PUBLIC_*` guidance does not say the values are public in the client bundle | Operator might put a server secret in `vars.NEXT_PUBLIC_*` | `.ai/deployment-standard.md:117-121` | Residual documentation. |
| Low | No durable negative tests for these policy files; `aip` secret scan skips `.md` | A future PAT or `0.0.0.0` example in markdown would not fail existing tests | `tools/aip.py` `SECRET_SCAN_SUFFIXES`; `tools/tests/test_aip.py` | Residual. Adding tests under `tools/` is outside frozen write-scope. Manual grep in this session is the current evidence. |
| Info | Profile contains host IP `46.202.150.29` and service names | Recon if the template repo is public. Not a credential. Internal inventory. | `.ai/platforms/bneli-vps.md:9` | Keep as snapshot inventory. |
| Info | `32769` public binding documented | Copy-paste risk | `.ai/platforms/bneli-vps.md:24` | Labeled as non-pattern occupancy in this session. |

## Negative/security test evidence

- Protocol tests: `python -m unittest tools.tests.test_aip -v` → 23 passed.
- Adversarial grep: no GitHub PAT literals; no `0.0.0.0` in implementation files; GHCR login example uses stdin, not an embedded token.
- No new automated invariant tests were added (`tools/` is outside frozen scope).
- Passing tests are not proof of security.

## Secrets / data / logging review

- No real PAT/token in the diff or current policy files.
- `deploy/.env.example` is specified as names/placeholders only; file is not created by this template task.
- Production verification tells operators to inspect logs without exposing secrets.
- Inventory (IP, ports, site names) is Internal operational data, not Restricted.
- Operator inventory commands are read-only and “do not ask for secrets.”

## Supply-chain / CI/CD review

- This change is documentation/policy. No new GitHub Actions, images, or dependencies.
- Existing `.github/workflows/ai-governance.yml` remains SHA-pinned with `contents: read`.
- Policy requires publishing `:latest` and `:<commit-sha>` and `pull_policy: always`. Deploy integrity still depends on post-deploy digest verification (overlay) unless the human later requires pin-on-compose.
- Merge is not production authorization.

## Residual risk

1. **Medium (non-blocking, human acceptance required):** Production Compose is specified as `image:` + `pull_policy: always` without requiring a `:commit-sha` or digest pin. `:latest` remains a documented publish tag. Unpinned auto-pull is possible until a later approved change requires SHA/digest pins. Compensating control already in the overlay: verify deployed image/tag/digest rather than assuming `latest`.
2. **Medium (non-blocking, human acceptance required):** Mandated `publish.yml` / `ci.yml` do not require least-privilege `permissions:`, SHA-pinned Actions, or “no GHCR write on `pull_request`”. Future scaffolded workflows may be overly privileged until a later approved change copies this template’s Action pattern.
3. Policy cannot prove the live VPS matches `.ai/platforms/bneli-vps.md`. Fresh operator evidence remains mandatory (already in the threat model).
4. No durable markdown secret/bind lint in CI.
5. Shared-host blast radius is unchanged; loopback + host NGINX only helps if generated Compose actually binds `127.0.0.1`.

## Human risk acceptance required?

**Yes.** The two residual Medium items above (production SHA/digest pin; generated `publish.yml` least privilege) are outside the approved specification/plan, were not implemented in this task, and are classified as non-blocking residual risk. No Critical/High findings are open.

This review does not record Security Gate approval. `gates.security` remains `pending` for a human.
