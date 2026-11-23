# Production Change Workflow Overlay

Use this overlay only for effects that happen **outside** the CI/CD pipeline. A deploy that the pipeline performs on merge is covered by the human merge and needs no Production Gate. Use it whenever the planned work includes a production deployment, live migration, production secret rotation, DNS/firewall/IAM change, live infrastructure mutation or a destructive action.

1. Identify the exact production target and blast radius.
2. Confirm the change exists in `external_actions.allowed`.
3. Write the `Production plan` section of `plan.md`: including prerequisites, ordering, rollback/roll-forward path and verification.
4. Identify secrets/permissions needed and use least privilege.
5. Complete implementation, tests, verification, code review and required security review before production authorization.
6. Stop at the **Production Gate**. The agent may prepare commands/actions but must not execute the production/destructive side effect.
7. After explicit human approval is recorded, execute only the approved action(s).
8. Verify production health and intended behavior with fresh evidence.
9. Record `production_verification=completed` and promote durable operational knowledge to `.memory-bank/ops/`.
10. If rollback requires a destructive or materially different action not already approved, stop and request a new authorization unless the approved plan explicitly pre-authorized that rollback.

## Shared SOHMA-style VPS/GHCR deployments

When `.ai/deployment-standard.md` applies:

- revalidate the live VPS before final port selection or first deployment; request this read-only inventory from the operator and do not select or change ports until the output has been reviewed:

```bash
echo '=== occupied sockets ==='
ss -tulpn
echo '=== docker ==='
docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo '=== nginx ==='
ls -la /etc/nginx/sites-enabled
```

- for the shared `*.bneli.tech` host, also read `.ai/platforms/bneli-vps.md`;
- internet ingress remains on host NGINX 80/443;
- application containers bind published host ports only to `127.0.0.1`;
- do not publish PostgreSQL to the host;
- production Compose pulls approved GHCR images and uses `pull_policy: always`;
- verify the deployed image/tag/digest rather than assuming `latest` is the intended build;
- never echo, log, commit or place a GHCR PAT in an example command; use an approved credential mechanism, `$GHCR_PAT` reference, or interactive `read -s`;
- `NEXT_PUBLIC_*` values for prebuilt frontend images come from GitHub Actions repository variables at build time, not the VPS runtime `.env`;
- NGINX site installation, symlink creation, reload and `certbot --nginx` are production actions and must be explicitly covered by the Production Gate;
- run `nginx -t` before reload and verify both loopback upstream health and public HTTPS afterward.

If the live inventory conflicts with the approved plan (for example the selected port became occupied), stop and return to planning/change control rather than improvising a new port in production.

Merge is not production authorization. Production authorization is not permission to merge.
