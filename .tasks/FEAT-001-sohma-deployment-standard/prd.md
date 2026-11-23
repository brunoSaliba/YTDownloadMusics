# FEAT-001 — Product definition

## Problem

Projects created from this template need a repeatable production deployment model compatible with the existing SOHMA Data Platform topology, while avoiding unsafe assumptions about a shared VPS whose live ports and services can change.

## Outcome

Provide a reusable repository-level deployment standard for Docker + GitHub Actions + GHCR + pull-based Docker Compose + host NGINX/Certbot, plus a separately maintained `bneli.tech` VPS profile that is explicitly a stale snapshot until revalidated.

## Acceptance criteria

- deployment rules are reusable across Python API and Node web repositories;
- host application ports bind only to `127.0.0.1`;
- production Compose does not expose PostgreSQL to the host;
- GitHub Actions publishes `latest` and immutable commit-SHA image tags to GHCR;
- private GHCR authentication examples never contain a PAT value;
- `NEXT_PUBLIC_*` values are treated as image-build inputs from GitHub repository variables;
- NGINX remains on the host and HTTPS uses Certbot NGINX integration;
- projects targeting the shared `bneli.tech` VPS must request fresh `ss`, `docker ps`, and NGINX-site evidence before assigning host ports;
- live VPS/NGINX/Certbot mutations remain Production-Gate actions.
