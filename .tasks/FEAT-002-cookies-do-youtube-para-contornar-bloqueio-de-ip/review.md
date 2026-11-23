# Review — FEAT-002 Cookies do YouTube

## Result

`APPROVED` (after fixes below; human merge approves code + security review)

## Code review

Independent fresh subagent, 2026-11-23. Verdict: "Request changes" → all fixed.

| Severity | Finding | Evidence | Action |
|---|---|---|---|
| Medium | `.youtube.com` + flag `FALSE` passed the filter but MozillaCookieJar rejects the whole file (job `failed`, line to stderr) | `app/worker.py` `_valid_cookie_line` | Fixed: flag must match leading dot; test `flag_mismatch` |
| Medium | AC1 download path not tested with cookies | `tests/test_worker.py` | Fixed: `test_download_also_uses_cookies` |
| Low | Test patched `run_info.__defaults__` | tests | Fixed: `ydl_cls=None` → `YoutubeDL` at call time; tests patch `worker.YoutubeDL` |
| Low | `_SECRETS` global leaked between tests; `SETTINGS` inherited real secret path | tests | Fixed: autouse fixture; `cookies_file=""` |
| Low | `OSError` after `mkdtemp` failed the job | `cookie_copy` | Fixed: run without cookies (C4) |
| Nit | `isdigit` accepted Unicode digits; missing annotation; no assertion that copy exists at yt-dlp exit | worker/tests | Fixed (`isascii`, annotation, `exists_on_exit`) |
| Nit | "unreadable" case not parametrized | tests | Accepted: same `OSError → None` branch as `missing`/`directory` |

## Verification against acceptance criteria

1. Cookies used in info + download: `test_ytdlp_gets_private_filtered_cookie_copy_removed_after_job`, `test_download_also_uses_cookies`; Docker smoke with a fake cookie file returned metadata.
2. Filtered 0600 copy, removed after job, original intact, copy present when yt-dlp saves: first test above (mode checked on POSIX/CI); smoke left no `ytdl-*` in `/tmp`.
3. Missing/empty/directory/too big/malformed/flag mismatch/symlink → no cookies: `test_unusable_cookie_file_runs_without_cookies[*]` (symlink runs on Linux CI).
4. No cookie content in API/logs/stdout: `test_cookie_values_never_reach_stdout_or_stderr`; smoke `docker logs` had 0 matches.
5. Expired/refused → `blocked`: same test asserts `{"ok": false, "error": "blocked"}`.
6. VPS `_k2ty4A5x1w` → 200: pending Production plan (operator).

Local: 57 passed, 1 skipped (symlink on Windows); ruff, bandit clean.

## Scope check

Changed files all inside `repo_write_scope`: yes (`aip validate`).

## Security review

Independent fresh subagent, 2026-11-23, working tree reviewed (not the author). Verdict: "No blocking findings".

- Invariants:
  - C1 domain filter rejects `youtube.com.evil.com`, `notyoutube.com`, Unicode and space tricks; `#HttpOnly_` and leading dots handled like yt-dlp. OK.
  - C3 `O_NOFOLLOW` + `fstat` on the same fd, bounded read, 0600 copy in 0700 `mkdtemp` on noexec tmpfs; yt-dlp saves only the copy, before `rmtree`. OK.
  - C4/C5 OK. C2: JSON is an allowlist (`public_info`).
- Findings:
  - Medium — a CR inside a field passed the filter; yt-dlp re-split it and `write_string` echoed fragments (or the full value) raw to stderr, bypassing logger and redaction, and `jobs.py` logs the stderr tail.
    - Fixed: lines with any control char except TAB are rejected; worker `sys.stderr` is wrapped by `_RedactingStream`.
    - Negative test: CR line plus a direct `write_string` call; neither secret appears in stdout or stderr.
  - Medium — docs suggested `--cookies-from-browser` (main profile would export personal accounts).
    - Fixed: private-window extension or burner-only profile; `shred -u` of the export; no copy kept outside the VPS.
  - Low — Compose secret file must exist on updates too. Fixed: the update step creates it if missing.
  - Low — values < 8 chars are not redacted; transformed forms (percent-encoding, repr escapes) are not redacted. Accepted: auth cookies (SID/HSID/SSID/APISID/SAPISID/`__Secure-*PSID`/LOGIN_INFO) are ≥ 17 chars.
- Residual risk (for human acceptance at merge):
  - On SIGKILL timeout the copy stays in tmpfs (same uid) until `sweep_stale_workdirs` (>10 min).
  - yt-dlp does not persist rotated cookies, so they expire sooner.
  - Burner account ban/expiry.
  - Root on the VPS can read the file.
  - YouTube ToS (D5).
