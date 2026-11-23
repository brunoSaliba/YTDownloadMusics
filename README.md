# YT Music Downloader

Site público (sem conta) para colar um link do YouTube, ver a música (título, artista, capa, duração) e baixar o áudio em MP3 192 kbps com tags e capa. Python/FastAPI + yt-dlp + ffmpeg, em Docker.

- Rodar local: `pip install --require-hashes -r requirements.txt -r requirements-dev.txt` e `uvicorn app.main:app --reload` (precisa de `ffmpeg` e `deno` no PATH para baixar de verdade).
- Testes: `pytest -q`.
- Dependências: `requirements.txt`/`requirements-dev.txt` têm hashes e são atualizados pelo Dependabot. Para regerar à mão: `echo "fastapi==X uvicorn==Y yt-dlp[default]==Z" | tr ' ' '
' | uv pip compile --generate-hashes --python-version 3.12 --python-platform x86_64-unknown-linux-gnu - -o requirements.txt` (dev: `pytest httpx ruff pip-audit bandit[toml]` com `-c requirements.txt`).
- Docker: `docker build -t ytdownloadmusics . && docker run --rm -p 127.0.0.1:8010:8080 ytdownloadmusics`.
- Deploy na VPS: `.memory-bank/ops/deploy.md`. Arquitetura: `.memory-bank/system/architecture.md`.
- Limites padrão: 15 min, sem playlists, 2 conversões simultâneas (ver `deploy/.env.example`).

Baixe apenas conteúdo que você tem direito de usar.

---

# AI Project Template

A vendor-neutral repository template for disciplined AI-assisted software engineering.

The protocol makes AI agents follow a controlled path instead of jumping from a request directly to code:

`Plan (acceptance + architecture + threat model) -> Fresh review -> Plan Gate -> Implementation -> Affected tests -> Code/Security Review -> PR -> CI -> Human Merge`

Security is not a final checklist. It is part of discovery, requirements, architecture, planning, implementation, verification, CI and review.

## Start a new project

1. Create a repository from this template.
2. Protect `main` using the GitHub setup in `docs/github-repository-setup.md`.
3. Open the repository with your AI coding tool.
4. Say:

```text
INIT PROJECT

<describe the product, users, integrations, constraints and preferred stack>
```

The agent must read `AGENTS.md` and `.ai/workflows/init-project.md`. Application code is prohibited until the required human gates are approved.

## Adopt an existing project

Say:

```text
INIT EXISTING PROJECT

Analyze this repository and adopt the AI Engineering Protocol.
```

The agent must inventory the existing system, security boundaries, tests, CI/CD, dependencies and technical debt before changing product behavior.

## Normal work

You can describe work naturally. The orchestrator classifies it as `HOTFIX`, `BUGFIX`, `TASK`, `FEATURE` or `EPIC` and selects the matching workflow.

Security-sensitive work cannot use the normal fast path. Any change involving authentication, authorization, tenancy, secrets, cryptography, sensitive data, file parsing/upload, external URL fetching, privileged operations, CI/CD, infrastructure, webhooks, payments, or other trust-boundary changes requires the security-sensitive workflow overlay.

## Repository model

- `AGENTS.md` — constitution for every AI agent.
- `CLAUDE.md` — Claude entry point importing the shared constitution.
- `.github/copilot-instructions.md` — Copilot entry point pointing to the same rules.
- `.ai/` — methodology, roles, workflows, plugin/tool governance, policies and security guidance.
- `.tasks/` — per-change execution state, handoffs, checkpoints and artifacts.
- `.memory-bank/` — durable project knowledge that survives individual tasks and chat sessions.
- `tools/aip.py` — dependency-free protocol helper for task state, human gate recording and CI validation.
- `.github/workflows/ai-governance.yml` — machine check for task state, write scope and high-confidence secret patterns.

## Protocol CLI

```bash
python tools/aip.py new-task --track FEATURE --title "Import employees"
python tools/aip.py status --task FEAT-001
python tools/aip.py approve --task FEAT-001 --gate definition --by "Bruno"
python tools/aip.py approve --task FEAT-001 --gate plan --by "Bruno"
python tools/aip.py allow-action --task FEAT-001 --plugin GitHub --action create_pr --effect EXTERNAL_WRITE --target repository --purpose "Open the approved PR"
python tools/aip.py validate --task FEAT-001 --base origin/main
python tools/aip.py checkpoint --task FEAT-001 --agent "Codex" --current-unit "Task 3" --next-action "Continue tests"
python tools/aip.py handoff --task FEAT-001 --agent "Codex" --next-action "Continue implementation"
python tools/aip.py resume --task FEAT-001
```

AI agents are forbidden from invoking `approve` on behalf of a human. The command exists to record a human decision, not to manufacture one.

## Security baseline

The template uses OWASP ASVS 5.0.0 as a verification reference for web application security, with project-specific requirements selected during initialization. It also requires threat modeling and explicit security invariants for sensitive changes. Automated tools are treated as evidence, not proof of security.

## What the template intentionally does not choose

The template does not force .NET, Node, Python, React, PostgreSQL, SQL Server, Docker, Kubernetes or any other application stack. During `INIT PROJECT`, architecture is selected and stack-specific CI, SAST, dependency scanning and test commands are generated after human approval.

## Plugins and external tools

Plugins/skills are specialists inside the protocol, not competing orchestrators. Read-only capabilities may support any relevant phase. External writes, production changes and destructive actions must be declared in the approved plan; the allowlist freezes at Plan Gate. Production/destructive execution additionally requires the Production Gate.

A plugin's claim is evidence, not authority. Record material evidence with `python tools/aip.py record-evidence ...` and independently verify it.

## Switching AI models

The project is deliberately model-independent. If one worker runs out of tokens, open the same repository/branch in another worker and use `RESUME`. Human gates, approved architecture, write scope and external-action permissions remain unchanged. The new worker reconstructs context from `state.json`, `session-handoff.md`, checkpoints, approved artifacts and live Git evidence rather than relying on the previous chat.
# ai-project-template
