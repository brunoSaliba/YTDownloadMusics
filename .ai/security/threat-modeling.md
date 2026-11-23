# Threat Modeling Guide

Threat modeling is required for PROJECT/EPIC initialization and High-risk security-sensitive FEATURE work.

## Method

1. Define system boundary and deployment.
2. Identify assets and data classifications.
3. List human and machine actors with trust levels.
4. Map entry points and data flows.
5. Mark trust boundaries.
6. Identify realistic abuse cases and attacker goals.
7. State security invariants that must always hold.
8. Map mitigations to each important threat.
9. Define negative tests/verification evidence.
10. Record residual risks, owners and unresolved assumptions.

STRIDE can be used as a prompt for completeness, but do not mechanically generate irrelevant threats.

Focus particularly on authorization/business logic, tenant boundaries, secret blast radius, file/network parsing boundaries, privileged automation and failure modes.
