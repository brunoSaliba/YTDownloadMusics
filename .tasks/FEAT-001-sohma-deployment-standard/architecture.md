# FEAT-001 — Architecture

## Policy layering

1. `.ai/deployment-standard.md` — reusable deployment model independent of a specific host.
2. `.ai/platforms/bneli-vps.md` — environment-specific inventory snapshot and reserved-port knowledge for the shared `*.bneli.tech` VPS.
3. Workflow integration — `INIT PROJECT`, `INIT EXISTING PROJECT`, and `production-change.md` consume those policies at the appropriate phase.
4. `AGENTS.md` — constitution-level pointer requiring agents to follow the deployment policy when applicable.

## Runtime topology standardized

Internet → host NGINX :80/:443 → `127.0.0.1:<app-port>` → Docker application container.

Images are built in GitHub Actions, pushed to GHCR, and pulled by production Compose. Databases internal to Compose stay on Docker networks without host-published database ports.

## Design decision

The shared VPS inventory is intentionally separated from the reusable standard because live occupancy is mutable. Port selection requires fresh runtime evidence before plan approval/finalization.
