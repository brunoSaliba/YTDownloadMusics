# Review

## Result

`APPROVED`

Independent review of the implementation already on `main` was performed by a fresh agent ([Code review FEAT-001](620582f1-b43a-4c7d-8fcf-6272f4b121d5)) against the approved PRD/specification/plan. That pass found no Critical issues and three Important issues. The Important items that contradicted approved requirements or would cause incorrect Compose planning were fixed in this session. Remaining items are Minor or out-of-spec recommendations.

This is not merge authority and not Security Gate approval.

## Findings

| Severity | Finding | Evidence | Required action |
|---|---|---|---|
| Important (fixed) | “use `image:` only for application services” was ambiguous and could exclude datastore images | Pre-fix `.ai/deployment-standard.md` Compose deliverables | Clarified: app services use prebuilt GHCR `image:` (no VPS `build:`); datastores may use upstream `image:` on the internal network only (`.ai/deployment-standard.md:35-37`). |
| Important (fixed) | PostgreSQL host-publish exception contradicted PRD/spec | Pre-fix `.ai/deployment-standard.md:19` | Exception removed (`.ai/deployment-standard.md:19,40`). |
| Important (fixed) | Production overlay said “revalidate” without the mandated `ss` / `docker ps` / NGINX commands | Pre-fix `.ai/workflows/production-change.md:20` | Inventory block and wait-for-review added (`.ai/workflows/production-change.md:20-29`). |
| Minor (accepted residual) | Spec’s `0.0.0.0` ban is only implied by the `127.0.0.1` rule | `.ai/deployment-standard.md:17` | No standard change; positive bind rule is the control. |
| Minor (accepted residual) | Python/Node reusability is implicit | `.ai/deployment-standard.md:3,47` | No standard change; stack-agnostic Docker plus “do not create inapplicable files” meets the AC. |
| Minor (fixed) | `32769` public binding could be copied as a pattern | `.ai/platforms/bneli-vps.md:24` | Labeled as existing occupancy, not a pattern. |
| Minor (accepted residual) | Constitution bullets omit Certbot by name | `AGENTS.md:178-187` | Certbot remains in the standard and production overlay; PRD AC is met there. |
| Minor (accepted residual) | Inventory bash duplicated in four files | standard, profile, init, production overlay | Left duplicated so each workflow remains self-contained. |
| Process | `state.json` was still `blocked` after Definition and Plan approval while files were on `main` | `.tasks/FEAT-001-sohma-deployment-standard/state.json` | Unblocked in this reconciliation; Security Gate stays pending. |

## Acceptance criteria coverage

Covered in `verification.md`. Policy layering, loopback binds, GHCR `latest`+SHA publish, PAT-safe login, `NEXT_PUBLIC_*` build-time vars, host NGINX/Certbot, and Production Gate separation matched the plan. Write-scope of `d03d8b5..5b7e2f2` matched `repo_write_scope`.

## Scope / write-scope check

Product implementation files are exactly the six paths in the approved plan. No application code, CI workflows, or host mutation. Post-review edits stayed inside approved scope.

## Remaining uncertainty

Generated `ci.yml` / `publish.yml` / `deploy/docker-compose.yml` are not in this repository; quality of future instantiations depends on agents following the standard. SHA-tag deploy pinning was not in the approved spec and was not added.
