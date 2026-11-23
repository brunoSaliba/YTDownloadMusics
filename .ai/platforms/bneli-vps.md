# Platform Profile — Shared BNELI VPS

This file is a convenience profile for projects intentionally targeting the shared VPS used by `*.bneli.tech`.

It contains known inventory supplied by the platform owner. **Treat every inventory item as a snapshot, not as live truth. Revalidate the VPS before choosing ports or performing production work.**

## Target

- Host: `46.202.150.29`
- DNS family: `*.bneli.tech`
- Reverse proxy: NGINX on host
- TLS: Certbot/Nginx
- SSH: host port `22`

## Known reserved / occupied host ports

Never allocate these to a new project without explicit revalidation and owner approval:

- `22` — SSH
- `80` — host NGINX HTTP
- `443` — host NGINX HTTPS
- `3000` — known `portalcliente-web-1`
- `8003` — known `calculo-vigas-web-1`
- `32769` — known `hermes-agent-*` public binding (existing occupancy, not a pattern to copy; new services bind to loopback only)

Known SOHMA loopback bindings also include:

- `127.0.0.1:3001` — SOHMA web
- `127.0.0.1:8000` — SOHMA API

Treat `3001` and `8000` as occupied too unless live evidence proves otherwise.

`5432` is prohibited as a host-published application/database port under the standard even if it appears free.

## Known NGINX sites

Known site names include:

- `calculovigas.bneli.tech`
- `portalcliente.bneli.tech`
- `sohma.bneli.tech`

A new project must choose a distinct domain and distinct loopback host ports.

## Mandatory pre-allocation inventory

Before fixing any new ports, request fresh output from the operator:

```bash
echo '=== occupied sockets ==='
ss -tulpn
echo '=== docker ==='
docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo '=== nginx ==='
ls -la /etc/nginx/sites-enabled
```

Do not infer port availability from this document alone. Record when the returned evidence was collected.

## Exposure policy

For this platform:

- internet ingress belongs to host NGINX on 80/443;
- app containers published to the host bind to `127.0.0.1` only;
- internal Compose services should use Docker networking without host ports when possible;
- do not expose PostgreSQL on the host;
- do not repurpose SSH/HTTP/HTTPS ports;
- any exception is a security-sensitive architecture/production change requiring explicit approval.

## Secrets / GHCR

Private-image authentication is host state, not repository content. Documentation may say that `docker login ghcr.io` is required but must never contain the real PAT.

Use environment-variable references such as `$GHCR_PAT`, interactive `read -s`, or a separately approved credential mechanism.
