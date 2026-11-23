# FEAT-001 — Threat model

## Assets

- production VPS services and ports;
- GHCR credentials and repository secrets/variables;
- application containers and internal databases;
- NGINX/Certbot configuration;
- deployment integrity from GitHub Actions to GHCR to VPS.

## Trust boundaries

- GitHub Actions → GHCR;
- VPS host → Docker daemon/Compose;
- host NGINX → loopback-bound application ports;
- operator input → live infrastructure mutations.

## Main threats and controls

- **Credential leakage:** examples use `$GHCR_PAT`/`read -s`; no real PAT values in repo text.
- **Accidental public exposure:** application binds are loopback-only; database ports are not host-published.
- **Port collision/outage:** stale inventory is never sufficient; fresh `ss`, `docker ps`, and NGINX evidence is required before assigning ports.
- **Supply-chain ambiguity:** publish immutable SHA tags in addition to `latest`; CI remains required.
- **Unauthorized production mutation:** NGINX/Certbot/live Docker changes require Production Gate authorization.
- **Frontend misconfiguration:** `NEXT_PUBLIC_*` is injected at build time through GitHub repository variables rather than treated as a VPS runtime secret.

## Residual risk

The policy cannot itself prove the live VPS matches the documented inventory. Human/operator-provided or tool-derived fresh evidence is still required before deployment planning and execution.
