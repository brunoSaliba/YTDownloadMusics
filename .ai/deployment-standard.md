# Deployment Standard — SOHMA-style VPS/GHCR

Use this standard when a project is approved for the shared VPS deployment model used by SOHMA Data Platform and related `*.bneli.tech` services.

This is a platform standard, not permission to deploy. Production actions remain governed by `.ai/workflows/production-change.md` and require the applicable human gates.

## Non-negotiable platform model

- Application services run in Docker.
- CI/CD uses GitHub Actions.
- Runtime images are published to GHCR using lowercase owner paths:
  - `ghcr.io/<owner-lowercase>/<project>/<service>:latest`
  - `ghcr.io/<owner-lowercase>/<project>/<service>:<commit-sha>`
- Production deployment is pull-based on the VPS.
- Production Compose consumes prebuilt images and uses `pull_policy: always`.
- The reverse proxy is NGINX on the HOST. Do not add Caddy or a reverse-proxy container to Compose.
- Application ports exposed to the host bind only to loopback: `127.0.0.1:<port>:<container-port>`.
- Never publish host ports `80`, `443`, `22` or `5432` from application Compose files.
- A PostgreSQL service owned by the Compose stack has no host-published port.
- NGINX sites use `/etc/nginx/sites-available/<domain>` plus a symlink in `/etc/nginx/sites-enabled/`.
- HTTPS is provisioned using `certbot --nginx` after HTTP routing is valid.
- Private GHCR pulls require authenticated `docker login` on the VPS.
- Never place a PAT/token in source code, README, Compose, examples, task artifacts, handoffs or logs. Interactive examples may refer to `$GHCR_PAT` or use `read -s` without embedding a value.
- `NEXT_PUBLIC_*` values are build-time inputs. For GitHub Actions builds they come from GitHub repository variables, not the VPS `.env`.

## Repository deliverables

When this deployment model is approved, plan the minimum applicable artifacts:

- `.github/workflows/ci.yml`
  - run appropriate tests/checks on pull requests and pushes to `main`;
- `.github/workflows/publish.yml`
  - on push to `main`, build and push the approved service images to GHCR;
  - publish both `latest` and the immutable commit SHA tag;
- `deploy/docker-compose.yml`
  - application services use prebuilt GHCR `image:` references (no VPS-side `build:` for those services);
  - datastores may use upstream `image:` names on the internal Docker network only;
  - `pull_policy: always`;
  - loopback-only published app ports;
  - no host-published PostgreSQL port;
- `deploy/nginx/<domain>.conf`
  - reverse proxy to the selected loopback ports;
- `deploy/.env.example`
  - placeholders/names only, no real secrets;
- operational documentation for required GitHub repository variables and VPS secrets/configuration.

Do not mechanically create files that do not apply to the approved stack. Inspect existing Dockerfiles, Compose, workflows and deployment docs first and preserve valid project-specific behavior.

## Production Docker review

Before approving the deployment plan, review Docker/runtime concerns supported by the actual repository, including as applicable:

- non-root runtime user;
- minimal runtime image/stages;
- deterministic dependency installation;
- healthcheck behavior;
- application bind address;
- loopback-only host exposure;
- CORS/origin configuration;
- secret/config handling;
- persistent storage ownership/permissions;
- graceful shutdown;
- database readiness/migrations;
- frontend build-time variables.

Do not introduce unrelated refactors under the label of deployment standardization.

## Port allocation is evidence-driven

Never reserve or hard-code a new host port from stale documentation alone.

Before selecting ports for a project targeting the shared VPS, ask the human/operator to run this read-only inventory on the VPS and return the output:

```bash
echo '=== occupied sockets ==='
ss -tulpn
echo '=== docker ==='
docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo '=== nginx ==='
ls -la /etc/nginx/sites-enabled
```

If needed after reviewing that output, request narrowly scoped read-only follow-up commands such as NGINX site contents or `docker compose ps`. Do not ask for secrets.

Port selection must account for both current socket listeners and Docker-published ports. Record the evidence date and selected ports in the project deployment documentation/Memory Bank.

## NGINX pattern

The repository may generate a site file, but installation on the VPS is a production change. The normal host-side sequence is conceptually:

1. place reviewed config in `/etc/nginx/sites-available/<domain>`;
2. create/review symlink in `/etc/nginx/sites-enabled/`;
3. `nginx -t`;
4. reload NGINX;
5. verify HTTP routing;
6. run `certbot --nginx -d <domain>`;
7. verify HTTPS and application health.

Exact commands and paths must come from the approved production plan and the real server state.

## GHCR authentication

The repository may document that authentication is required, but must not contain a real credential.

Safe conceptual patterns include:

```bash
read -s GHCR_PAT
printf '%s' "$GHCR_PAT" | docker login ghcr.io -u <github-user> --password-stdin
unset GHCR_PAT
```

or using an already-provisioned credential mechanism approved for the host.

Never paste a PAT into a shell command committed to the repository.

## GitHub Actions build-time variables

For frontend values such as `NEXT_PUBLIC_API_BASE_URL`, use a GitHub Actions repository variable, e.g. `${{ vars.NEXT_PUBLIC_API_BASE_URL }}`, as an explicit Docker build argument/env only when required by the frontend build.

Do not place `NEXT_PUBLIC_*` in the VPS `.env` expecting a prebuilt Next.js image to pick them up at runtime.

## Verification

A deployment change is not complete merely because containers are running. Fresh production verification should include, as applicable:

- `docker compose ps`/container health;
- loopback health/API checks on the VPS;
- public HTTPS health/application checks through NGINX;
- expected image tag/digest;
- NGINX configuration test;
- no unintended public database/app ports;
- application logs for startup errors without exposing secrets.
