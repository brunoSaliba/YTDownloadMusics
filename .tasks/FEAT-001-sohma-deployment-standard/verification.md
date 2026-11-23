# Verification

## Result

`PASS` against the approved PRD, specification, architecture, threat model, and plan implementation units 1–5, after one in-scope defect fix (PostgreSQL host-publish exception) and two alignment fixes (Compose `image:` wording; production-overlay inventory commands).

This is not Security Gate approval. `gates.security` remains `pending`.

Verified at HEAD `dacb5b235a85cca3e8be10e7aae1ed56f58ef2db` plus the uncommitted reconciliation edits listed in the scope check.

Independent verifier pass: [Verify FEAT-001 vs spec](c4f72369-dd67-4aee-b7cb-c34d8bca7e1b) recorded **PASS WITH GAPS** on the pre-fix tree. The PostgreSQL exception gap is closed in this session. Remaining items below are residual, not unmet acceptance criteria.

## Acceptance criteria coverage

| Source | Criterion | Result | Evidence |
|---|---|---|---|
| PRD | Reusable across Python API and Node web | **MET** | Stack-agnostic Docker/GHCR/Compose/NGINX in `.ai/deployment-standard.md:9-24`; frontend `NEXT_PUBLIC_*` is additive (`.ai/deployment-standard.md:24,117-121`); “do not mechanically create inapplicable files” (`.ai/deployment-standard.md:47`). Compose wording now allows upstream datastore images (`.ai/deployment-standard.md:35-37`). |
| PRD | Host app ports bind only to `127.0.0.1` | **MET** | `.ai/deployment-standard.md:17`; `AGENTS.md:183`; `.ai/platforms/bneli-vps.md:65`; `.ai/workflows/production-change.md:33`; `.ai/workflows/init-project.md:148`. |
| PRD | Production Compose does not expose PostgreSQL to the host | **MET** (fixed) | `.ai/deployment-standard.md:19,40`; `.ai/platforms/bneli-vps.md:33,67`; `.ai/workflows/production-change.md:34`. Pre-fix exception on line 19 contradicted this AC and was removed. |
| PRD | GitHub Actions publishes `latest` and commit-SHA tags | **MET** | `.ai/deployment-standard.md:12-13,32-34`; `AGENTS.md:180`. |
| PRD | GHCR auth examples never contain a PAT value | **MET** | `.ai/deployment-standard.md:23,101-115` (`read -s` / `$GHCR_PAT` / stdin); `.ai/platforms/bneli-vps.md:73-75`; `.ai/workflows/production-change.md:37`. Workspace grep found no `ghp_` / `github_pat_` / `gho_` literals. |
| PRD | `NEXT_PUBLIC_*` are GitHub build-time repository variables | **MET** | `.ai/deployment-standard.md:24,117-121`; `AGENTS.md:186`; `.ai/workflows/init-project.md:83`; `.ai/workflows/production-change.md:38`. |
| PRD | Host NGINX; HTTPS via Certbot NGINX integration | **MET** | `.ai/deployment-standard.md:16,20-21,89-97`; `AGENTS.md:182`; `.ai/workflows/production-change.md:32,39`. |
| PRD | Shared VPS: fresh `ss`, `docker ps`, NGINX-site evidence before ports | **MET** | Same inventory block in `.ai/deployment-standard.md:74-81`; `.ai/platforms/bneli-vps.md:47-58`; `.ai/workflows/init-project.md:30-41`; `.ai/workflows/init-existing-project.md:27-36`; **and** `.ai/workflows/production-change.md:20-29` after this session (pre-fix overlay only said “revalidate”). |
| PRD | Live VPS/NGINX/Certbot mutations remain Production-Gate actions | **MET** | `.ai/deployment-standard.md:5,89`; `AGENTS.md:50,189`; `.ai/workflows/init-project.md:148`; `.ai/workflows/production-change.md:5-6,39`. |
| Spec | Generic standard covers Docker, GHA, GHCR, pull Compose, host NGINX, Certbot, loopback, secret-safe GHCR login, build-time `NEXT_PUBLIC_*` | **MET** | `.ai/deployment-standard.md` sections Non-negotiable / Repository deliverables / GHCR authentication / GitHub Actions build-time variables. |
| Spec | `bneli.tech` profile is a snapshot, not permanent truth | **MET** | `.ai/platforms/bneli-vps.md:5`. |
| Spec | INIT PROJECT and INIT EXISTING PROJECT consult the standard | **MET** | `.ai/workflows/init-project.md:28`; `.ai/workflows/init-existing-project.md:23`. |
| Spec | Wait for `ss -tulpn`, `docker ps`, `/etc/nginx/sites-enabled` before fixing ports | **MET** | Commands plus “do not choose/reserve/select until reviewed” in init (`init-project.md:41`), standard (`deployment-standard.md:69-85`), profile (`bneli-vps.md:58`), production overlay (`production-change.md:20`). |
| Spec invariant | Never publish host 80/443/22/5432 from application Compose | **MET** | `.ai/deployment-standard.md:18`; `AGENTS.md:184`; `.ai/platforms/bneli-vps.md:19-21,33`. |
| Spec invariant | Never expose app services on `0.0.0.0` behind host NGINX | **MET** | Positive control: required bind `127.0.0.1:<port>:<container-port>` (`.ai/deployment-standard.md:17`). Grep of implementation files found no `0.0.0.0`. |
| Spec invariant | Never place a real PAT/token in repository text or examples | **MET** | See PRD PAT row. |
| Spec invariant | Never treat stale VPS inventory as proof a port is free | **MET** | `.ai/deployment-standard.md:69`; `.ai/platforms/bneli-vps.md:5,58`; `AGENTS.md:187`. |
| Spec invariant | Never infer merge authorizes live deployment | **MET** | `.ai/deployment-standard.md:5`; `.ai/workflows/production-change.md:44`; `AGENTS.md:50`. |
| Architecture | Four-layer policy split | **MET** | Standard / `bneli-vps.md` / init+production workflows / `AGENTS.md:174-189`. |
| Architecture | Internet → host NGINX :80/:443 → loopback app port → container; GHCR pull; DBs without host ports | **MET** | `.ai/deployment-standard.md:9-19,88`; `.ai/workflows/production-change.md:32-35`. |
| Threat model | Credential leakage control | **MET** | `$GHCR_PAT` / `read -s`; no literals. |
| Threat model | Accidental public exposure | **MET** | Loopback + no host PostgreSQL after exception removal. |
| Threat model | Port collision / stale inventory | **MET** | Fresh `ss` / `docker ps` / NGINX evidence required (`.ai/deployment-standard.md:69-85`). |
| Threat model | SHA tags plus `latest`; CI required | **MET** as publish policy. Deploy pin of SHA/digest remains residual (see security-review.md). |
| Threat model | Production mutation requires Production Gate | **MET** | Overlay + constitution. |
| Threat model | `NEXT_PUBLIC_*` not VPS runtime | **MET** | See PRD row. |
| Plan unit 1 | Add reusable standard | **MET** | `.ai/deployment-standard.md` |
| Plan unit 2 | Add stale `bneli.tech` inventory | **MET** | `.ai/platforms/bneli-vps.md` |
| Plan unit 3 | Integrate into init workflows | **MET** | `init-project.md`, `init-existing-project.md` |
| Plan unit 4 | Extend production-change revalidation | **MET** | Overlay now includes the mandated inventory commands. |
| Plan unit 5 | Constitution pointer | **MET** | `AGENTS.md:174-189` |
| Plan units 6–7 | Verify and independent review | **MET** | This file; `code-review.md`; `security-review.md`. |
| Plan unit 8 | PR after Definition, Plan, and Security gates | **NOT DONE** | Security Gate is pending by instruction. Implementation already exists on `main` (process finding; see retrospective). |

## Scope / write-scope check

Approved `repo_write_scope`:

- `AGENTS.md`
- `.ai/deployment-standard.md`
- `.ai/platforms/bneli-vps.md`
- `.ai/workflows/init-project.md`
- `.ai/workflows/init-existing-project.md`
- `.ai/workflows/production-change.md`
- `.tasks/FEAT-001-sohma-deployment-standard/**`

Candidate implementation `d03d8b5..5b7e2f2` touched only the six policy files. Task artifacts are under the task glob.

This session’s product edits stayed inside that scope:

- `.ai/deployment-standard.md` — remove PostgreSQL host-port exception; clarify Compose `image:` vs datastore images
- `.ai/workflows/production-change.md` — require `ss` / `docker ps` / NGINX listing before port changes
- `.ai/platforms/bneli-vps.md` — label `32769` as non-pattern occupancy

Memory Bank promotion was removed from this FEAT because `.memory-bank/**` is outside the frozen `repo_write_scope`. Durable facts remain in the task retrospective.

No live VPS mutation. `effects.production_change=false`. `external_actions.allowed=[]`.

## Required tests/checks actually ran

| Check | Command / method | Result |
|---|---|---|
| Protocol unit tests | `python -m unittest tools.tests.test_aip -v` | 23 tests, `OK`, 0.106s |
| PAT literals | workspace grep `ghp_` / `github_pat_` / `gho_` | no matches |
| `0.0.0.0` in implementation files | grep on `.ai/deployment-standard.md`, `.ai/platforms/bneli-vps.md`, `.ai/workflows/` | no matches |
| Invariant greps | loopback, `pull_policy: always`, `ss -tulpn`, `docker ps`, `sites-enabled`, `certbot --nginx`, `NEXT_PUBLIC_`, Production Gate | present in the files cited above |

No application runtime exists in this template. Adding durable policy-lint tests under `tools/` would be outside frozen `repo_write_scope`; that gap is residual (security-review.md).

## Remaining uncertainty

- Live VPS occupancy cannot be proved from repository text. Threat-model residual risk stands.
- Production Compose pinning of SHA/digest, and least-privilege rules for generated `publish.yml`, are not in the approved specification. They are non-blocking residual Medium items requiring explicit human risk acceptance at Security Gate, not silent new requirements.
- `aip.py validate --stage pr` is expected to fail until a human records Security Gate approval.
