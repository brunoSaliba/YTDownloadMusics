# Subagent brief (keep under ~15 lines)

- **Role:** code reviewer | verifier | security reviewer | artifact reviewer (`.ai/roles/<role>.md`)
- **Task:** `<ID>`; track `<TRACK>`; security-sensitive: yes/no
- **Scope:** diff `git diff <base>...HEAD` (and only files: ...)
- **Criteria:** acceptance criteria / invariants to check (list, no prose)
- **Read:** only the files above and the role file. Do not read the whole protocol, Memory Bank or closed tasks.
- **Output:** findings by severity with file:line evidence, max ~30 lines. Read-only except the review artifact.
