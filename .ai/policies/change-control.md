# Change Control

## Scope

Implementation changes must stay within `repo_write_scope` in the task state. Task artifacts for the current task and approved Memory Bank updates are allowed metadata changes.

## Scope expansion

If additional application paths are required, implementation stops. Planner updates the plan and scope. For FEATURE/EPIC/PROJECT or security-sensitive work, material scope expansion may require renewed human Plan Gate approval.

## Prohibited shortcuts

Agents must not:

- disable tests or scanners merely to pass CI;
- weaken authentication/authorization to simplify implementation;
- broaden a permission, CORS rule, network rule or secret scope without an approved requirement;
- commit local credentials/test production secrets;
- use `--no-verify`, force-push protected branches or bypass review policy as a routine fix;
- rewrite project security policy to classify a valid finding out of scope.
