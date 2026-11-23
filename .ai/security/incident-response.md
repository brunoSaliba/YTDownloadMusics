# Security Incident Development Flow

Use for urgent remediation of an active or suspected security issue.

1. Preserve evidence and avoid destructive cleanup until impact is understood.
2. Contain exposure using the smallest safe operational action.
3. Rotate/revoke exposed credentials when applicable.
4. Create a `HOTFIX` task marked `security_sensitive=true`.
5. Record known affected assets, versions and assumptions without placing secrets/exploit-sensitive material unnecessarily in the repo.
6. Implement the smallest safe fix with regression/security tests.
7. Security Reviewer validates the violated invariant and remediation.
8. Human controls production rollout and merge.
9. Perform post-incident root cause, blast-radius review and durable control improvements.

Do not use incident urgency as permission to silently weaken security controls or skip later retrospective/root-cause work.
