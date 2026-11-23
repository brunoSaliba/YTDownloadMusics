# Plan — PROJ-000 init: YT Music Downloader

Charter: `.memory-bank/project/project-charter.md`.

## Discovery record

- Problem/outcome, actors, workflow, scope: ver charter.
- Integrations: YouTube (via yt-dlp, saída HTTPS). Nenhuma outra.
- Data: URLs/IDs de vídeo e metadados públicos (Public); IP do visitante em logs de acesso (Internal/pessoal mínimo). Arquivos de áudio são temporários (cópia de conteúdo de terceiros, nunca persistida).
- Deployment: VPS `*.bneli.tech`, Docker, GHCR, NGINX no host, porta loopback.
- NFR: prévia < 5 s; MP3 de 5 min entregue em < 60 s; 1 vCPU razoável; sem estado.
- Unknowns: porta livre na VPS (precisa evidência), domínio final, bloqueio de IP pelo YouTube na VPS.

## Goal and acceptance criteria

1. `GET /` serve página com campo de URL e botão "Buscar".
2. `POST /api/info {url}` com URL válida retorna `{id, title, artist, thumbnail, duration}`; artista = `artist` do YouTube se existir, senão `uploader`/canal; `thumbnail` montada pelo servidor como `https://i.ytimg.com/vi/<id>/hqdefault.jpg`.
3. Formas aceitas: `youtube.com/watch?v=ID`, `m.youtube.com`, `music.youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/shorts/ID`; parâmetros extras (`list`, `t`, `si`) ignorados.
4. URL inválida, host fora da allowlist ou ID mal formado → 400 com mensagem amigável, sem chamar o yt-dlp (vale para `/api/info` e `/api/download/{id}`).
5. Vídeo acima de `MAX_DURATION_SECONDS` (padrão 900), ao vivo ou indisponível → 422 com mensagem clara. **O download refaz essa validação** antes de baixar (chamada direta a `/api/download/{id}` não contorna o limite) e usa `max_filesize`.
6. `GET /api/download/{id}` entrega `audio/mpeg`, 192 kbps, com tags título/artista e capa embutida, `Content-Disposition` com nome sanitizado `Artista - Título.mp3`. (Bitrate/tags/capa verificados no smoke manual; testes automatizados cobrem cabeçalhos e nome.)
7. Diretório temporário do pedido é removido após a entrega, em erro ou timeout.
8. Mais de `MAX_CONCURRENT_JOBS` (padrão 2) conversões simultâneas → 503 "servidor ocupado"; `/api/info` tem semáforo próprio (`MAX_CONCURRENT_INFO`, padrão 2).
9. Job acima de `JOB_TIMEOUT_SECONDS` (padrão 240) é morto (processo filho e descendentes) → 504; bloqueio do YouTube ("not a bot") / erro do extrator → 502 amigável.
10. `GET /healthz` → 200; `GET /robots.txt` com `Disallow: /api/`.
11. Respostas com `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, CSP `default-src 'self'; img-src 'self' https://i.ytimg.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`; nenhum JS inline.
12. Imagem Docker roda como não-root; Compose publica só `127.0.0.1:<porta>`.

## Architecture

- **Um serviço** `web` (FastAPI + Uvicorn `--workers 1`, semáforos valem por processo), frontend estático (HTML/CSS/JS puro, sem build) servido pelo mesmo app.
- **Info**: biblioteca `yt_dlp` com `noplaylist`, `allowed_extractors=["youtube"]`, `cachedir=False`, sem config de usuário/plugins, `socket_timeout`.
- **Download**: executado em **processo filho** (`multiprocessing`/`subprocess` com argv fixo, sem shell, novo process group) que roda yt-dlp: revalida info → `bestaudio` → `FFmpegExtractAudio(mp3,192)`, `FFmpegMetadata`, `EmbedThumbnail` em `tempfile.mkdtemp()`. Pai aguarda com timeout e mata o grupo ao estourar. Resposta via `FileResponse` + `BackgroundTask` que apaga o diretório e libera o slot (também em `finally` nos caminhos de erro). Síncrono no request (NGINX `proxy_read_timeout 300s` > 240 s).
- **Runtime**: `python:3.12-slim` multi-stage, `ffmpeg` via apt, Deno (runtime JS exigido pelo yt-dlp atual para YouTube; confirmar no scaffold), usuário não-root, `HEALTHCHECK`, bind `0.0.0.0:8080` dentro do container. `HOME`, `DENO_DIR`, `XDG_CACHE_HOME`, `TMPDIR` apontando para o tmpfs.
- **Compose**: `image:` GHCR com `pull_policy: always`, `127.0.0.1:<PORTA>:8080`, `read_only: true`, `tmpfs /tmp` (~256m, conta no `mem_limit`), `mem_limit` (~768m), `cpus`, `pids_limit`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, log `json-file` com `max-size`/`max-file`.
- **NGINX**: `limit_req` + `limit_conn` por IP **obrigatórios** em `/api/` (ex.: info 20/min, download 6/min burst baixo, 2 conexões), `proxy_read_timeout 300s`, `client_max_body_size 1k`.
- **Sem DB, sem storage persistente, sem segredos** na v1. Config por env: `MAX_DURATION_SECONDS`, `MAX_CONCURRENT_JOBS`, `MAX_CONCURRENT_INFO`, `JOB_TIMEOUT_SECONDS`, `MAX_FILESIZE_MB`.
- **Observabilidade**: logs JSON simples (id do vídeo, resultado, duração do job); sem corpo de requisição, sem cookies.

## Threat model

- **Assets / data classification**: disponibilidade da VPS compartilhada (CPU/disco/RAM/rede — principal ativo); integridade da imagem/pipeline; reputação do IP da VPS perante o YouTube. Dados: Public (metadados), Internal (IPs em logs NGINX).
- **Entry points / inputs controlados pelo atacante**: `url` em `/api/info`; `id` em `/api/download/{id}`; metadados vindos do YouTube (título/uploader → nome de arquivo, HTML, tags); headers HTTP; mídia remota processada por ffmpeg/Deno.
- **Security invariants**:
  - I1 (SSRF): o yt-dlp só recebe `https://www.youtube.com/watch?v=<id>` reconstruída pelo servidor, `id` casando `^[A-Za-z0-9_-]{11}$`; a URL do usuário nunca é repassada; extratores limitados a `youtube` (sem `generic`).
  - I2 (exec/injection): nenhum `shell=True`; o processo filho recebe argv fixo com o `id` já validado; ffmpeg só via pós-processadores do yt-dlp; sem config/plugins do yt-dlp carregados.
  - I3 (path traversal / header injection): nome em disco gerado pelo servidor (`<id>.mp3`); `Content-Disposition` sanitizado (sem `/ \ " CR LF` e controles, ≤ 150 chars, RFC 5987 `filename*`).
  - I4 (recursos): duração, live, playlist e tamanho validados **no próprio endpoint de download** antes de baixar; semáforos (info e download) liberados sempre; timeout com kill do grupo de processos; tmpfs limitado; temp sempre apagado; rate limit por IP no NGINX.
  - I5 (XSS): metadados renderizados só via `textContent`; `img.src` só com URL montada pelo servidor em `i.ytimg.com`; CSP restritiva, sem inline.
  - I6 (container): não-root, FS read-only, `cap_drop ALL`, `no-new-privileges`, `pids_limit`, porta só em loopback; erros ao cliente sem stack trace.
  - I7 (CI/CD): `permissions: contents: read` no topo; `packages: write` só no job de publish em push para `main`, após testes e Trivy passarem; sem `pull_request_target`; `persist-credentials: false`; Actions pinadas por SHA.
- **Abuse cases → mitigation → evidence**:
  - URL `http://169.254.169.254/...` ou `youtube.com.evil.com` → allowlist + regex de ID → teste negativo (I1).
  - ID `../../etc/passwd` em `/api/download` → regex 400 → teste negativo (I1/I3).
  - Chamada direta a `/api/download/{id}` de vídeo de 10 h / live → 422 sem baixar → teste negativo com extrator mockado (I4).
  - Job travado → kill no timeout, 504, slot liberado → teste com filho fake que dorme (I4).
  - Título com `"\r\nSet-Cookie:` → sanitizador → teste (I3); `<script>` no título → `textContent` + CSP → revisão do JS e teste de cabeçalhos (I5).
  - Flood → semáforos 503 (teste, I4) + `limit_req` NGINX (revisão da config).
- **Secrets / blast radius**: v1 sem segredos de runtime. CI usa só `GITHUB_TOKEN`. PAT de pull do GHCR fica só no host.
- **Residual risk**: (a) legal/ToS — aceite do dono (D5); (b) bloqueio do IP da VPS pelo YouTube — pode exigir cookies/PO token futuramente (nova FEATURE security-sensitive); (c) rate limit por IP é contornável com muitos IPs — semáforo global limita o dano; (d) vulnerabilidades em ffmpeg/yt-dlp/Deno parseando conteúdo remoto — mitigado por hardening do container e atualização semanal; Deno atualizado manualmente.

## Decisions requiring human acceptance

- D1 Domínio: `musicas.bneli.tech` — aceito pelo humano (2026-11-23).
- D2 Porta loopback: `127.0.0.1:8010` → container `8080`. Evidência da VPS coletada em 2026-11-23: loopback ocupados 1721/udp, 3000-3003, 8000-8004, 8006, 8007, 8080, 8891, 65529; públicos 22, 25, 80, 443. `8010` livre; `musicas.bneli.tech` sem site NGINX existente. DNS do subdomínio a confirmar pelo operador.
- D3 Rate limit por IP no NGINX: **obrigatório** após revisão (site público sem login em VPS compartilhada).
- D4 Concorrência: 2 downloads / 2 infos simultâneos — aceito pelo humano (2026-11-23; infos reduzido de 4 para 2 após medição de memória no smoke).
- D5 Risco legal/ToS e risco de bloqueio de IP — aceitos pelo humano (2026-11-23).

Evidência da VPS a coletar (somente leitura):
```bash
echo '=== occupied sockets ==='; ss -tulpn
echo '=== docker ==='; docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo '=== nginx ==='; ls -la /etc/nginx/sites-enabled
```

## Repository write scope

`app/**`, `tests/**`, `Dockerfile`, `.dockerignore`, `pyproject.toml`, `requirements*.txt`, `deploy/**`, `.github/workflows/ci.yml`, `.github/workflows/publish.yml`, `.github/dependabot.yml`, `SECURITY.md`, `README.md`, `.memory-bank/**`, `.tasks/PROJ-000-init/**`.

## Ordered tasks and tests

1. Scaffold Python (`pyproject.toml`, `requirements.txt` com hashes via pip-tools, `app/main.py`, `app/youtube.py`, `app/jobs.py`, `app/static/`). Teste: `/healthz` + `robots.txt`.
2. Validação de URL + `/api/info` (2-5). Testes: parametrizado de formas válidas; negativos I1; duração/live com `yt_dlp` mockado.
3. `/api/download` (5-9). Testes: revalidação no download (I4), sanitizador (I3), limpeza de temp (7), semáforo 503, timeout 504 com kill. Sem rede nos testes.
4. Frontend + cabeçalhos (1, 11, I5): página única, estados carregando/erro/prévia/baixar; teste dos cabeçalhos.
5. Docker + deploy (12, I6): Dockerfile, `deploy/docker-compose.yml`, `deploy/nginx/<dominio>.conf`, `deploy/.env.example`, `.memory-bank/ops/deploy.md` (inclui cadência manual do Deno).
6. CI/CD (I7): `ci.yml` (ruff, pytest, pip-audit, bandit, `docker build` + Trivy), `publish.yml` (push em `main` → testes + Trivy → GHCR latest+sha).
7. Memory Bank (`system/`, `ops/`) + `SECURITY.md` do projeto.

Smoke manual (local, Docker) com vídeo real curto antes do PR: verifica bitrate, tags, capa (critério 6). Deploy real na VPS = passo do operador após merge (NGINX/certbot são Production Gate).

## Dependency / supply-chain changes

- Runtime: `fastapi`, `uvicorn[standard]`, `yt-dlp` (+ `yt-dlp-ejs` se exigido), ffmpeg (apt Debian), Deno (binário oficial, versão pinada + checksum).
- Dev: `pytest`, `httpx`, `ruff`, `pip-audit`, `bandit`.
- Dependabot: adicionar `pip` e `docker` (semanal, minor/patch agrupado, limite 2 PRs, major ignorado). Exceção: `yt-dlp` sem agrupamento, pois quebra quando o YouTube muda. Sem auto-merge.
