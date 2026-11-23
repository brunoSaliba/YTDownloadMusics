# FEAT-001 — Specification

The protocol must add a reusable deployment standard and a separate shared-VPS profile.

## Required behavior

- The generic deployment standard must specify Dockerized application services, GitHub Actions CI/publish, GHCR images, pull-based Compose, host NGINX, Certbot, loopback-only host binds, secret-safe GHCR login examples, and build-time handling of `NEXT_PUBLIC_*`.
- The `bneli.tech` platform profile must record known host/services/ports as an inventory snapshot, not permanent truth.
- `INIT PROJECT` and `INIT EXISTING PROJECT` must consult the deployment standard when this topology applies.
- Before fixing host ports on the shared VPS, the agent must request fresh evidence using `ss -tulpn`, `docker ps`, and `/etc/nginx/sites-enabled` listing and wait for the result.
- Production mutations to NGINX, Certbot, Docker runtime, firewall, or live services remain subject to the Production Gate.

## Security invariants

- Never publish host 80/443/22/5432 from application Compose.
- Never expose app services on `0.0.0.0` when they are intended to sit behind host NGINX.
- Never place a real PAT/token in repository text or example commands.
- Never treat stale VPS inventory as evidence that a port is currently free.
- Never infer that merge authorization permits a live deployment.
