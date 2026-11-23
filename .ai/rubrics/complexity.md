# Complexity Rubric

Run `python tools/aip.py classify [paths...] [--bugfix] [--current TRACK]` (default: `git diff` vs `origin/main`). It is deterministic and only escalates, never downgrades.

| Result | When |
|---|---|
| TASK | Only tests/docs/tools/.tasks/.ai, or ≤5 code files in a single module (`apps/api` or `apps/web`), no sensitive path |
| BUGFIX | Same as TASK with `--bugfix` (adds one regression test) |
| FEATURE | Sensitive path (auth, tenant, token, upload, webhook, migrations, CI, Docker, deploy, .env, dependencies), or >1 code module, or >15 code files |
| EPIC / PROJECT / HOTFIX | Declared manually |

Project-specific sensitive paths, module depth and limits: override in `.ai/classify.json` (keys `sensitive`, `non_code` regex lists, `module_depth`, `max_task_code_files`, `max_feature_code_files`; defaults in `tools/aip.py`).

6-15 code files in one module stays TASK/BUGFIX but the tool warns: split the work or justify in `plan.md`.

Goal-based work (e.g. "reduce tests") is ONE task and ONE PR, not one FEAT per step. Re-run `classify` if scope grows; if it returns a higher track, upgrade.
