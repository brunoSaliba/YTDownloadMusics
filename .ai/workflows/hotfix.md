# Workflow — HOTFIX

Use only for urgent production restoration or active security containment.

1. Triage impact and reproduce/confirm evidence.
2. Define the minimal safe change and rollback path.
3. If security-related, overlay `security-sensitive-change.md` and preserve evidence.
4. Implement only the minimal fix.
5. Add focused regression/security tests.
6. Run targeted build/tests plus mandatory governance checks.
7. Independent code review; Security Reviewer when applicable.
8. Human-controlled PR/merge/deploy.
9. Follow with a short root-cause note (Memory Bank) and any non-urgent hardening as separate work.

Urgency reduces ceremony, not accountability.
