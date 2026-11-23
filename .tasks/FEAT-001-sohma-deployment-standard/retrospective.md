# Retrospective

## What changed from the original understanding?

The six policy files were written and merged to `main` **before** FEAT-001 existed. The task was then registered, Definition and Plan gates were recorded, and the candidate diff was merged unchanged (`163fd34`, then task artifacts in `dacb5b2`). `state.json` still said the work was blocked pending those gates.

This session treated Git and the approved artifacts as source of truth: re-verified the landed files, removed the one spec-contradicting clause, aligned the production overlay with the mandated inventory commands, and produced the missing verification/review/retrospective evidence. The deployment standard was not rewritten.

## What caused rework or uncertainty?

- Candidate-before-task implementation left governance state (`blocked`, `implementation: pending`, stale `next_action`) disagreeing with Git and with recorded gate approvals.
- Plan unit 8 (PR after Security Gate) cannot describe current delivery: the policy is already on `main`.
- A PostgreSQL host-publish exception in the standard contradicted the approved absolute PRD/spec/threat-model control.
- The production overlay required “revalidate” but omitted the three evidence commands the specification names.
- `tools/` is outside frozen write-scope, so FEATURE-level durable negative tests for these markdown invariants could not be added here.

## What defects/security issues were found and when?

- **During independent verification/code/security review (this session):** PostgreSQL host-port exception (Medium, spec contradiction) — fixed.
- **Same pass:** Compose `image:` wording ambiguous for datastores — fixed.
- **Same pass:** production overlay missing `ss` / `docker ps` / NGINX inventory — fixed.
- **Same pass:** `hermes-agent` public bind unlabeled — labeled as non-pattern.
- **Residual Medium, non-blocking, not fixed:** production image pin to SHA/digest; generated `publish.yml` least privilege. These are outside the approved spec/plan and require explicit human residual-risk acceptance; they were not implemented.
- No Critical/High findings. No PAT literals. No `0.0.0.0` examples.

## What did we learn about the system?

- The intended production topology is: GitHub Actions → GHCR (`:latest` and `:<commit-sha>`) → VPS Compose pull (`pull_policy: always`) → loopback-bound app ports → host NGINX/Certbot on 80/443.
- `.ai/platforms/bneli-vps.md` is a stale inventory snapshot. Port allocation always needs fresh `ss -tulpn`, `docker ps`, and `/etc/nginx/sites-enabled`.
- Merge never authorizes live VPS/NGINX/Certbot/Docker mutation.
- `NEXT_PUBLIC_*` for prebuilt frontend images comes from GitHub repository variables at build time, not the VPS `.env`.
- This template still has no application runtime; the “implementation” is protocol policy.

## What durable knowledge was promoted to `.memory-bank/`?

None in this FEAT. A Memory Bank ops note was drafted and then removed because `.memory-bank/**` is outside the frozen `repo_write_scope`. Durable facts stay in this retrospective until a later in-scope promotion.

## What process improvement should apply next time?

- Do not land candidate implementation on `main` before the FEATURE task, artifact review, and required gates exist. Recover the diff after Plan Gate instead of merging first and reconciling later.
- After Definition and Plan approval, immediately clear `blocked` / `block_reason` that referred to those gates, or the next worker will refuse to proceed.
- If a policy file must be both the reusable standard and the deploy-time checklist, copy the mandatory evidence commands into the overlay used at production time (or the overlay will be followed alone).
- Keep `tools/` in `repo_write_scope` when a security-sensitive FEATURE will need durable invariant tests; otherwise testers are limited to one-off greps.
- Do not promote to `.memory-bank/` on a FEATURE whose frozen `repo_write_scope` omits it; leave durable facts in the retrospective until an in-scope promotion.
