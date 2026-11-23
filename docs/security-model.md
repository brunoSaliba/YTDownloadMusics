# Security Model of the Template

The template uses defense in depth rather than relying on a prompt.

## Layer 1 — Behavior

`AGENTS.md`, workflows and role documents tell every agent how security must shape discovery, architecture, implementation and review.

## Layer 2 — Persistent evidence

Task state, threat models, security reviews, acceptance criteria and Memory Bank documents make decisions inspectable across tools and sessions.

## Layer 3 — Local/CI guardrails

`tools/aip.py` checks required gates, declared write scope, external-action allowlists, completion state, plugin/tool evidence and a small set of high-confidence secret patterns. The GitHub workflow runs this at PR time and can also validate production/post-production stages.

## Layer 4 — Plugin/provider boundaries

Plugins and external tools are capabilities, not authorities. Non-read side effects must be declared before Plan Gate; production/destructive operations require Production Gate. When possible, provider IAM, protected environments and approval controls enforce the same boundary technically.

## Layer 5 — Repository authority

GitHub rulesets/branch protection provide the real human merge boundary: required PR, human review and required CI/security checks.

## Layer 6 — Stack-specific security

`INIT PROJECT` must create actual language/framework/runtime security automation after the stack is approved. The generic template intentionally refuses to fake universal SAST coverage.

## Important limitation

No prompt, state file or CI script can guarantee that an AI obeys policy or that software is secure. Human review and technical enforcement at repository/runtime boundaries remain necessary.
