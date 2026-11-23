# Ops — deploy on the shared bneli VPS

- Domain `musicas.bneli.tech`; app on `127.0.0.1:8010` → container `8080`. Port chosen from VPS evidence collected 2026-11-23 (occupied loopback: 3000-3003, 8000-8004, 8006, 8007, 8080, 8891, 65529).
- Image: `ghcr.io/brunosaliba/ytdownloadmusics/web:{latest,<sha>}`, published by `.github/workflows/publish.yml` on push to `main` after tests + Trivy.
- No GitHub repository variables or runtime secrets are needed.

## First install (Production Gate — operator runs, not the pipeline)

1. DNS: `musicas.bneli.tech` → VPS IP.
2. `mkdir -p /opt/ytdownloadmusics && cd /opt/ytdownloadmusics`; copy `deploy/docker-compose.yml` and `deploy/.env.example` as `.env`.
3. GHCR login if the package is private: `read -s GHCR_PAT; printf '%s' "$GHCR_PAT" | docker login ghcr.io -u <github-user> --password-stdin; unset GHCR_PAT`.
4. `docker compose up -d` → `curl -fsS http://127.0.0.1:8010/healthz`.
5. Copy `deploy/nginx/musicas.bneli.tech.conf` to `/etc/nginx/sites-available/musicas.bneli.tech`, symlink in `sites-enabled`, `nginx -t`, `systemctl reload nginx`.
6. `certbot --nginx -d musicas.bneli.tech`; verify `https://musicas.bneli.tech/healthz`.

## Update / rollback

- Update: `docker compose pull && docker compose up -d`.
- Rollback: set `IMAGE_TAG=<previous sha>` in `.env`, `docker compose up -d`.

## Maintenance

- yt-dlp breaks when YouTube changes: merge Dependabot `yt-dlp*` PRs quickly.
- Deno is pinned by digest in `Dockerfile` (`denoland/deno:bin-*`); Dependabot `docker` covers it — otherwise bump monthly.
- If YouTube starts answering "confirm you're not a bot" (HTTP 502 in the app), the VPS IP is blocked; cookies/PO token would be a new security-sensitive FEATURE.
