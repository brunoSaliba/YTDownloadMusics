# Session Handoff

No handoff has been recorded yet.

When an AI worker changes or a session is ending, use:

```bash
python tools/aip.py handoff --task TASK-ID --agent "Agent name" --next-action "Exact next action"
```

If a session ends unexpectedly, the next worker must use `RESUME` / `aip resume` and reconstruct state from `state.json`, the latest checkpoint, Git status/diff, and approved task artifacts.
