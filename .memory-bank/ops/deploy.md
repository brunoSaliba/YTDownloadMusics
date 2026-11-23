# Ops — deploy on the shared bneli VPS

- Domain `musicas.bneli.tech`; app on `127.0.0.1:8010` → container `8080`. Port chosen from VPS evidence collected 2026-11-23 (occupied loopback: 3000-3003, 8000-8004, 8006, 8007, 8080, 8891, 65529).
- Image: `ghcr.io/brunosaliba/ytdownloadmusics/web:{latest,<sha>}`, published by `.github/workflows/publish.yml` on push to `main` after tests + Trivy.
- No GitHub repository variables or runtime secrets are needed.

## First install (Production Gate — operator runs, not the pipeline)

1. DNS: `musicas.bneli.tech` → VPS IP.
2. `mkdir -p /opt/ytdownloadmusics && cd /opt/ytdownloadmusics`; copy `deploy/docker-compose.yml` and `deploy/.env.example` as `.env`.
3. GHCR login if the package is private: `read -s GHCR_PAT; printf '%s' "$GHCR_PAT" | docker login ghcr.io -u <github-user> --password-stdin; unset GHCR_PAT`.
4. `install -o 10001 -g 10001 -m 400 /dev/null youtube-cookies.txt` (required by the Compose secret; empty = no cookies), then `docker compose up -d` → `curl -fsS http://127.0.0.1:8010/healthz`.
5. Copy `deploy/nginx/musicas.bneli.tech.conf` to `/etc/nginx/sites-available/musicas.bneli.tech`, symlink in `sites-enabled`, `nginx -t`, `systemctl reload nginx`.
6. `certbot --nginx -d musicas.bneli.tech`; verify `https://musicas.bneli.tech/healthz`.

## Update / rollback

- Update: `docker compose pull && docker compose up -d`. Since FEAT-002 the Compose secret file must exist: `[ -e youtube-cookies.txt ] || install -o 10001 -g 10001 -m 400 /dev/null youtube-cookies.txt` before `up`.
- Rollback: set `IMAGE_TAG=<previous sha>` in `.env`, `docker compose up -d`.

## Maintenance

- yt-dlp breaks when YouTube changes: merge Dependabot `yt-dlp*` PRs quickly.
- Deno is pinned by digest in `Dockerfile` (`denoland/deno:bin-*`); Dependabot `docker` covers it — otherwise bump monthly.
- If YouTube starts answering "confirm you're not a bot" (HTTP 502 in the app), the VPS IPv4 is likely blocked: set `FORCE_IPV6=1` in `.env` and `docker compose up -d` (needs host IPv6 + the compose network's `enable_ipv6`). If IPv6 is blocked too, install YouTube cookies (FEAT-002) below.

## YouTube cookies (FEAT-002)

- Use a **burner** Google account, never a personal one. Export in a private window: log in, open `https://www.youtube.com/robots.txt`, export `youtube.com` cookies in Netscape format with a cookies.txt extension allowed in private windows (or `yt-dlp --cookies-from-browser chrome:"<burner-only profile>"`; never the main profile, which would export personal accounts), close the window without logging out.
- Install/rotate keeping the inode: `cat new.txt > /opt/ytdownloadmusics/youtube-cookies.txt && chown 10001:10001 youtube-cookies.txt && chmod 400 youtube-cookies.txt` (read on the next job; after `mv` run `docker compose restart`). Then `shred -u new.txt`; keep no copy outside the VPS.
- Disable: `: > youtube-cookies.txt`. Revoke: log out the burner account elsewhere.
- Symptom of expiry/ban: 502 "blocked" again → export fresh cookies.
