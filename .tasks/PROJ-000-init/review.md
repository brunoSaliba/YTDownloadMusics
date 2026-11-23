# Review

## Result

Ready for human PR review. All code/security findings addressed. Open operational risk: YouTube media download not verified end-to-end (local network blocked, see smoke); must be checked on the VPS.

## Code review

Fresh subagent reviewer, 2026-11-23 (read-only, yt-dlp 2026.10.26 / Starlette 1.10 source checked).

| Severity | Finding | Evidence | Required action |
|---|---|---|---|
| Medium | Slot leak if `sweep`/`mkdtemp` raised (ENOSPC) outside `try` | app/main.py download | Fixed: both inside `try/finally` |
| Medium | Age-restricted video classified as `blocked` (502) | app/worker.py `classify_error` | Fixed: only "not a bot" → blocked; regression case in `test_classify_error` |
| Low | 500 handler bypasses security-header middleware | app/main.py `unhandled_error` | Fixed: headers set explicitly |
| Low | `info` mode without `format` could fail on format selection | app/worker.py `run_info` | Fixed: `bestaudio/best` |
| Low | Slot released before streaming (plan said BackgroundTask) | app/main.py | Accepted deviation: slot bounds conversion only |
| Low | `max_filesize` approximate with chunked HTTP | yt-dlp HttpFD | Accepted: duration cap is the real bound |
| Low | Timeout test covers direct child only, not grandchildren | tests/test_api.py | Accepted: killpg verified by reading |
| Low | "15 minutos" hard-coded in index.html | app/static/index.html | Accepted (matches default) |

## Verification against acceptance criteria

`pytest -q` → 47 passed (2026-11-23, local); `ruff check app tests` clean.
1/10/11 `test_index_health_robots_and_security_headers` · 2 `test_info_returns_metadata`, `test_info_maps_metadata_and_builds_thumbnail_server_side` · 3 `test_accepts_supported_youtube_urls` · 4 `test_info_rejects_bad_url_without_spawning_worker`, `test_download_rejects_malformed_id` · 5 `test_download_revalidates_limits_before_downloading`, `test_download_maps_worker_errors_and_cleans_temp` · 6 headers/name in `test_download_serves_mp3_and_removes_temp`; bitrate/tags/cover verified in smoke below · 7 `test_download_serves_mp3_and_removes_temp`, `test_download_range_request_does_not_leak_temp` · 8 `test_download_busy_returns_503` · 9 `test_run_worker_kills_hung_child_on_timeout`, `test_classify_error` · 12 smoke: image builds; container ran as uid 10001 with read-only FS, tmpfs, cap_drop ALL, no-new-privileges, 768m, loopback port.

### Manual smoke (2026-11-23, local Docker Desktop, image `ytdownloadmusics:smoke`)

- `/healthz` 200; deno 2.9.8 and ffmpeg 7.1.5 present.
- Real `/api/info` from the container → 502 "bloqueou": YouTube answers "Sign in to confirm you're not a bot". Host diagnosis: same yt-dlp **IPv4 blocked, IPv6 works** on this residential connection; inside Docker Desktop (IPv6 network) metadata works but media URLs return HTTP 403 (also with plain `yt-dlp` CLI, so not app code). Classification `blocked` → 502 behaved as designed.
- Metadata over IPv6 in the container: `{"title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)", "artist": "Rick Astley", "duration": 213, "thumbnail": "https://i.ytimg.com/..."}`.
- Conversion pipeline in the hardened container (audio fetched on host, same postprocessors as `run_download`): 4.7 s; `ffprobe` → `codec=mp3`, `bit_rate=193810`, `tag:title`, `tag:artist=Rick Astley`, embedded `mjpeg` cover. Criterion 6 OK.
- Memory: worker 103 MB + largest child (Deno/ffmpeg) 319 MB peak RSS. 4 info + 2 download workers could OOM at 768m (L2); human chose `MAX_CONCURRENT_INFO=2` (4 workers × ~420 MB ≈ 1.7 GB worst case only if all peak at once; typical info peak is Deno-only and brief).

## Scope check

Yes: all changed files inside `repo_write_scope` (`requirements*.in` removed by human decision 2026-11-23); `aip.py validate` passed.

## Security review

Fresh subagent reviewer (not the author), 2026-11-23, read-only.

- I1 OK: ASCII `fullmatch` ID, canonical URL rebuilt (validation.py), `allowed_extractors` uses `re.fullmatch` → only `youtube`; userinfo/backslash/IDN tricks rejected. Negative tests: `test_rejects_non_youtube_or_malformed_urls`, `test_info_rejects_bad_url_without_spawning_worker`.
- I2 OK: list argv, no shell, ID re-validated in worker; no yt-dlp config; plugins off (Dockerfile env + worker.py now forces `YTDLP_NO_PLUGINS`); Deno runs with no `--allow-*`, `--no-remote`. Test: `test_main_rejects_invalid_id_without_running_ytdlp`.
- I3 OK: disk name `%(id)s.%(ext)s`; sanitizer strips C*, separators, quotes; `filename*` percent-encoded. Test: `test_download_name_is_header_and_path_safe`.
- I4 was PARTIAL → fixed. M1 (Medium): Range 416/400 or send failure skipped the FileResponse BackgroundTask, leaking ~20-30 MB per request until sweep → tmpfs DoS. Fix: MP3 read into memory (bounded by duration cap) and work dir deleted in `finally` before responding; sweep threshold 10 min. Regression: `test_download_range_request_does_not_leak_temp`. Other I4 controls OK (match_filter before download, slots in `finally`, killpg).
- I5 OK: `textContent` only, server-built thumbnail, CSP without inline.
- I6 OK: non-root, read-only, tmpfs noexec, cap_drop ALL, no-new-privileges, pids_limit, loopback-only.
- I7 OK: `contents: read` default, `packages: write` only in publish job after CI + Trivy on the exact image, `persist-credentials: false`, SHA-pinned actions, no `pull_request_target`, hash-pinned requirements.
- Low: L1 IPv6 /128 rate-limit key (accepted; global slots bound damage) · L2 concurrent workers vs 768m (mitigated: info slots 4→2 by human decision; residual OOM risk only if all 4 peak at once — container restarts, verify on VPS) · L3 plugins only via env (fixed in worker.py) · L4 HTTPS redirect/HSTS/`server_tokens` (server_tokens added; HSTS note for post-certbot) · L5 mutable `latest` (deploy doc: prefer `IMAGE_TAG=<sha>`).
- CI scanner exception (human-approved 2026-11-23): Trivy `skip-files` for `**/yt_dlp/extractor/shahid.py` only — upstream yt-dlp embeds a public AWS key ID for the Shahid extractor, unreachable here (`allowed_extractors=["youtube"]`). Not a project secret; scope limited to that one file. Debian zlib CVE-2026-85091 fixed via `apt-get upgrade` in the runtime stage.
- Residual risk: ffmpeg/yt-dlp parse remote media (contained by container sandbox); distributed DoS against global slots; Action SHAs resolved via GitHub API but not independently re-verified by reviewer; Deno inherits env (keep `.env` secret-free); YouTube ToS/copyright and IP blocking (accepted by owner).

## Plan review (fresh reviewer, 2026-11-23)

Verdict inicial: AJUSTES NECESSÁRIOS. High: (1) download contornava limites → revalidação no download + `max_filesize`; (2) timeout inaplicável em thread → job em processo filho com kill do grupo; (3) DoS sem rate limit → `limit_req`/`limit_conn` obrigatórios + semáforo no info. Medium/Low: hardening de container, read-only vs caches do yt-dlp/Deno, `allowed_extractors`, thumbnail montada no servidor, ordem/permissões do CI, códigos 502/504, cabeçalhos/CSP, robots.txt, cadência do Deno. Todos incorporados ao `plan.md`. Sem contradição com `bneli-vps.md`.
