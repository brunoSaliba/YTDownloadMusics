#!/usr/bin/env python3
"""AI Engineering Protocol helper.

Dependency-free on purpose. It records task state and validates human gates,
write scope, completion evidence and a small set of high-confidence secret
patterns. It is a guardrail, not a security scanner or authorization system.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / ".tasks"

TRACK_PREFIX = {
    "PROJECT": "PROJ",
    "HOTFIX": "HOTFIX",
    "BUGFIX": "BUG",
    "TASK": "TASK",
    "FEATURE": "FEAT",
    "EPIC": "EPIC",
}

FULL_GATE_TRACKS = {"PROJECT", "FEATURE", "EPIC"}
LEAN_SCHEMA = 4  # v4: Definition folded into Plan Gate, Security folded into PR merge, plan.md + review.md only
VALID_STATUS = {"pending", "in_progress", "completed", "blocked", "not_required"}
PR_REQUIRED_STATUS = ("implementation", "testing", "verification", "code_review", "retrospective")
EXTERNAL_EFFECTS = {"EXTERNAL_WRITE", "PRODUCTION_CHANGE", "DESTRUCTIVE"}

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,255}\b")),
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
]

SECRET_SCAN_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".cs", ".fs", ".vb", ".java",
    ".kt", ".go", ".rb", ".php", ".sh", ".ps1", ".yml", ".yaml", ".json",
    ".xml", ".toml", ".ini", ".conf", ".properties", ".env", ".tf", ".tfvars",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "task"


def task_dirs() -> list[Path]:
    if not TASKS_DIR.exists():
        return []
    return [p for p in TASKS_DIR.iterdir() if p.is_dir() and (p / "state.json").exists()]


def find_task(task_id: str) -> Path:
    task_id = task_id.upper()
    matches = []
    for directory in task_dirs():
        state = load_json(directory / "state.json")
        if str(state.get("id", "")).upper() == task_id:
            matches.append(directory)
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one task {task_id}; found {len(matches)}")
    return matches[0]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def next_id(track: str) -> str:
    prefix = TRACK_PREFIX[track]
    numbers: list[int] = []
    for directory in task_dirs():
        state = load_json(directory / "state.json")
        task_id = str(state.get("id", ""))
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", task_id, flags=re.IGNORECASE)
        if match:
            numbers.append(int(match.group(1)))
    number = max(numbers, default=0) + 1
    return f"{prefix}-{number:03d}"


def blank_state(task_id: str, title: str, track: str, complexity: int,
                security_sensitive: bool, risk: str, production_change: bool = False,
                external_write: bool = False, destructive: bool = False) -> dict:
    # Production/destructive effects always cross a security boundary.
    security_sensitive = security_sensitive or production_change or destructive
    if security_sensitive and track in {"TASK", "BUGFIX"}:
        raise SystemExit("Security-sensitive TASK/BUGFIX must use FEATURE or EPIC. Use HOTFIX only for genuine urgent remediation.")

    full_gates = track in FULL_GATE_TRACKS
    production_gate = production_change or destructive
    return {
        "schema_version": LEAN_SCHEMA,
        "id": task_id,
        "title": title,
        "track": track,
        "complexity": complexity,
        "phase": "discovery" if track == "PROJECT" else "planning",
        "blocked": False,
        "block_reason": None,
        "security": {
            "risk": risk,
            "security_sensitive": security_sensitive,
            "threat_model_required": security_sensitive or track in {"PROJECT", "EPIC"},
            "security_review_required": security_sensitive,
        },
        "effects": {
            "repo_write": True,
            "external_write": external_write or production_gate,
            "production_change": production_change,
            "destructive": destructive,
            "security_sensitive": security_sensitive,
        },
        "gates": {
            "definition": gate("not_required"),
            "plan": gate("pending" if full_gates else "not_required"),
            "security": gate("not_required"),
            "production": gate("pending" if production_gate else "not_required"),
        },
        "repo_write_scope": [],
        "external_actions": {
            "allowed": [],
            "evidence": [],
        },
        "continuity": {
            "last_agent": None,
            "current_unit": None,
            "next_action": None,
            "last_checkpoint": None,
            "last_checkpoint_at": None,
            "last_handoff_at": None,
        },
        "status": {
            "product": "not_required",
            "specification": "not_required",
            "architecture": "not_required",
            "artifact_review": "not_required",
            "threat_model": "pending" if (security_sensitive or track in {"PROJECT", "EPIC"}) else "not_required",
            "planning": "pending",
            "implementation": "blocked" if full_gates else "pending",
            "testing": "pending",
            "verification": "not_required",
            "code_review": "pending",
            "security_review": "pending" if security_sensitive else "not_required",
            "retrospective": "not_required",
            "production_plan": "pending" if production_gate else "not_required",
            "production_verification": "pending" if production_gate else "not_required",
        },
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def gate(status: str) -> dict:
    return {"status": status, "approved_by": None, "approved_at": None}


def create_task_files(directory: Path, state: dict) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    save_json(directory / "state.json", state)
    for output, template in (("plan.md", "plan.md"), ("review.md", "review.md")):
        if artifact_required(output, state):
            source = ROOT / ".ai" / "templates" / template
            (directory / output).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (directory / "checkpoints").mkdir(exist_ok=True)


def ensure_continuity(state: dict) -> dict:
    """Return state with v3 continuity defaults without changing gates/scope."""
    continuity = state.setdefault("continuity", {})
    for key in ("last_agent", "current_unit", "next_action", "last_checkpoint",
                "last_checkpoint_at", "last_handoff_at"):
        continuity.setdefault(key, None)
    return state


def _continuity_ignore_patterns(directory: Path) -> list[str]:
    if not directory.is_relative_to(ROOT):
        return []
    prefix = str(directory.relative_to(ROOT)).replace("\\", "/")
    return [
        f"{prefix}/state.json",
        f"{prefix}/session-handoff.md",
        f"{prefix}/checkpoints/**",
    ]


def git_working_snapshot(root: Path = ROOT, ignore_patterns: list[str] | None = None) -> dict:
    """Capture lightweight Git evidence for handoff/recovery.

    Continuity files can be ignored so recording a checkpoint does not make
    that same checkpoint appear as uncheckpointed product work.
    """
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)

    inside = run("rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0:
        return {
            "git_available": False, "branch": None, "head": None,
            "working_tree": "unknown", "changed_files": [], "untracked_files": [],
            "working_tree_fingerprint": None,
        }

    branch_r = run("rev-parse", "--abbrev-ref", "HEAD")
    head_r = run("rev-parse", "HEAD")
    diff_r = run("diff", "--name-only", "HEAD")
    untracked_r = run("ls-files", "--others", "--exclude-standard")

    tracked = [x.strip().replace("\\", "/") for x in diff_r.stdout.splitlines() if x.strip()] if diff_r.returncode == 0 else []
    untracked = [x.strip().replace("\\", "/") for x in untracked_r.stdout.splitlines() if x.strip()] if untracked_r.returncode == 0 else []
    patterns = ignore_patterns or []
    tracked = [x for x in tracked if not matches_scope(x, patterns)]
    untracked = [x for x in untracked if not matches_scope(x, patterns)]
    changed = sorted(set(tracked + untracked))

    # Hash current file states, not agent narrative. This detects additional
    # edits to a file that was already dirty at the previous checkpoint.
    hasher = hashlib.sha256()
    for relative in changed:
        hasher.update(relative.encode("utf-8", errors="replace"))
        path = root / relative
        try:
            if not path.exists():
                hasher.update(b"<deleted>")
            elif path.is_file():
                size = path.stat().st_size
                hasher.update(str(size).encode("ascii"))
                if size <= 10_000_000:
                    hasher.update(path.read_bytes())
                else:
                    # Avoid pulling very large artifacts into memory; Git diff
                    # review remains mandatory for resumed work.
                    hasher.update(b"<large-file-content-not-hashed>")
            else:
                hasher.update(b"<non-file>")
        except OSError:
            hasher.update(b"<unreadable>")

    return {
        "git_available": True,
        "branch": branch_r.stdout.strip() if branch_r.returncode == 0 else None,
        "head": head_r.stdout.strip() if head_r.returncode == 0 else None,
        "working_tree": "dirty" if changed else "clean",
        "changed_files": changed,
        "untracked_files": sorted(set(untracked)),
        "working_tree_fingerprint": hasher.hexdigest(),
    }


def _next_checkpoint_path(directory: Path) -> Path:
    checkpoints = directory / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    numbers = []
    for path in checkpoints.glob("*.json"):
        match = re.fullmatch(r"(\d+)-checkpoint\.json", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return checkpoints / f"{max(numbers, default=0) + 1:03d}-checkpoint.json"


def create_checkpoint(directory: Path, state: dict, *, agent: str, current_unit: str | None,
                      next_action: str | None, verification: list[str] | None = None,
                      git_snapshot: dict | None = None, summary: str | None = None,
                      completed: list[str] | None = None, in_progress: list[str] | None = None,
                      decisions: list[str] | None = None, known_issues: list[str] | None = None) -> Path:
    """Persist an immutable continuity checkpoint and update only continuity metadata."""
    ensure_continuity(state)
    snapshot = git_snapshot or git_working_snapshot(ignore_patterns=_continuity_ignore_patterns(directory))
    path = _next_checkpoint_path(directory)
    checkpoint = {
        "schema_version": 1,
        "checkpoint": path.stem,
        "task_id": state["id"],
        "created_at": utc_now(),
        "agent": agent,
        "phase": state.get("phase"),
        "current_unit": current_unit,
        "next_action": next_action,
        "summary": summary,
        "completed": completed or [],
        "in_progress": in_progress or [],
        "decisions": decisions or [],
        "known_issues": known_issues or [],
        "verification": verification or [],
        "workflow_snapshot": {
            "gates": json.loads(json.dumps(state.get("gates", {}))),
            "status": json.loads(json.dumps(state.get("status", {}))),
            "repo_write_scope": list(state.get("repo_write_scope", [])),
            "external_actions_allowed": json.loads(json.dumps(state.get("external_actions", {}).get("allowed", []))),
            "blocked": state.get("blocked", False),
            "block_reason": state.get("block_reason"),
        },
        "git": snapshot,
    }
    save_json(path, checkpoint)
    continuity = state["continuity"]
    continuity["last_agent"] = agent
    continuity["current_unit"] = current_unit
    continuity["next_action"] = next_action
    continuity["last_checkpoint"] = path.name
    continuity["last_checkpoint_at"] = checkpoint["created_at"]
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    return path


def _load_last_checkpoint(directory: Path, state: dict) -> dict | None:
    ensure_continuity(state)
    name = state["continuity"].get("last_checkpoint")
    if not name:
        return None
    path = directory / "checkpoints" / name
    if not path.exists():
        return None
    return load_json(path)


def build_resume_report(directory: Path, state: dict, current_git: dict,
                        available_capabilities: list[str] | None = None) -> dict:
    """Build a read-only resume report. Never changes approvals or scope."""
    ensure_continuity(state)
    checkpoint = _load_last_checkpoint(directory, state)
    checkpoint_git = checkpoint.get("git", {}) if checkpoint else {}
    checkpoint_files = set(checkpoint_git.get("changed_files", []) or [])
    current_files = set(current_git.get("changed_files", []) or [])
    uncheckpointed = sorted(current_files - checkpoint_files)

    fingerprint_changed = False
    old_fp = checkpoint_git.get("working_tree_fingerprint")
    new_fp = current_git.get("working_tree_fingerprint")
    if checkpoint and old_fp and new_fp:
        fingerprint_changed = old_fp != new_fp

    missing: list[str] = []
    if available_capabilities is not None:
        available_lower = {x.lower() for x in available_capabilities}
        required = {
            str(action.get("plugin")) for action in state.get("external_actions", {}).get("allowed", [])
            if action.get("plugin")
        }
        missing = sorted(x for x in required if x.lower() not in available_lower)

    return {
        "task_id": state.get("id"),
        "title": state.get("title"),
        "track": state.get("track"),
        "phase": state.get("phase"),
        "blocked": state.get("blocked", False),
        "block_reason": state.get("block_reason"),
        "last_agent": state["continuity"].get("last_agent"),
        "last_checkpoint": state["continuity"].get("last_checkpoint"),
        "last_checkpoint_at": state["continuity"].get("last_checkpoint_at"),
        "current_unit": state["continuity"].get("current_unit"),
        "next_action": state["continuity"].get("next_action"),
        "gates": json.loads(json.dumps(state.get("gates", {}))),
        "repo_write_scope": list(state.get("repo_write_scope", [])),
        "external_actions_allowed": json.loads(json.dumps(state.get("external_actions", {}).get("allowed", []))),
        "git": current_git,
        "checkpoint_git": checkpoint_git or None,
        "uncheckpointed_changes": uncheckpointed,
        "working_tree_changed_since_checkpoint": fingerprint_changed or bool(uncheckpointed),
        "head_changed_since_checkpoint": bool(checkpoint and checkpoint_git.get("head") and current_git.get("head") and checkpoint_git.get("head") != current_git.get("head")),
        "missing_capabilities": missing,
        "handoff_file": (
            str((directory / "session-handoff.md").relative_to(ROOT))
            if (directory / "session-handoff.md").exists() and (directory / "session-handoff.md").is_relative_to(ROOT)
            else str(directory / "session-handoff.md") if (directory / "session-handoff.md").exists() else None
        ),
    }


def _active_task_candidates() -> list[Path]:
    terminal = {"completed", "closed", "archived", "production_verified"}
    candidates = []
    for directory in task_dirs():
        state = load_json(directory / "state.json")
        if str(state.get("phase", "")).lower() not in terminal:
            candidates.append(directory)
    return candidates


def select_resume_task(task_id: str | None) -> Path:
    if task_id:
        return find_task(task_id)
    candidates = _active_task_candidates()
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise SystemExit("No active task found. Use --task TASK-ID if resuming a historical task.")
    ids = [load_json(p / "state.json").get("id", p.name) for p in candidates]
    raise SystemExit("Multiple active tasks found; specify --task. Candidates: " + ", ".join(map(str, ids)))


def artifact_required(name: str, state: dict) -> bool:
    """Lean (v4) tasks keep only plan.md (+review.md for FEATURE+/security-sensitive).

    Requirements, architecture, threat model and production plan are sections of plan.md;
    code review, verification and security review are sections of review.md.
    session-handoff.md is created on demand by the handoff command.
    """
    track = state["track"]
    sensitive = state["security"]["security_sensitive"]
    if name == "plan.md":
        return True
    if name == "review.md":
        return track in FULL_GATE_TRACKS or sensitive
    return False


def ensure_dynamic_artifacts(directory: Path, state: dict) -> None:
    target = directory / "review.md"
    if artifact_required("review.md", state) and not target.exists():
        source = ROOT / ".ai" / "templates" / "review.md"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def cmd_init_project(args: argparse.Namespace) -> None:
    task_id = "PROJ-000"
    for directory in task_dirs():
        if load_json(directory / "state.json").get("id") == task_id:
            raise SystemExit("PROJ-000 already exists. This repository has already been initialized or adoption started.")
    state = blank_state(task_id, args.title, "PROJECT", args.complexity, True, args.risk)
    directory = TASKS_DIR / f"{task_id}-init"
    create_task_files(directory, state)
    print(f"Created {directory.relative_to(ROOT)}")
    print("Application implementation is blocked until Definition and Plan gates are human-approved.")


def cmd_new_task(args: argparse.Namespace) -> None:
    track = args.track.upper()
    task_id = next_id(track)
    state = blank_state(task_id, args.title, track, args.complexity, args.security_sensitive, args.risk, args.production_change, args.external_write, args.destructive)
    directory = TASKS_DIR / f"{task_id}-{slugify(args.title)}"
    create_task_files(directory, state)
    print(f"Created {directory.relative_to(ROOT)}")


def cmd_status(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    print((directory / "state.json").read_text(encoding="utf-8"))


def cmd_approve(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    name = args.gate
    if name not in state["gates"]:
        raise SystemExit(f"Unknown gate: {name}")
    current = state["gates"][name]["status"]
    if current == "not_required":
        raise SystemExit(f"Gate {name} is not required for {state['track']}")

    if name == "definition":
        required = ["product", "specification", "architecture", "artifact_review", "threat_model"]
        incomplete = [item for item in required if state["status"].get(item) not in {"completed", "not_required"}]
        if incomplete:
            raise SystemExit("Definition Gate cannot be approved; incomplete: " + ", ".join(incomplete))
    elif name == "plan":
        if state["status"].get("planning") != "completed":
            raise SystemExit("Plan Gate cannot be approved until planning=completed")
        if not state.get("repo_write_scope"):
            raise SystemExit("Plan Gate cannot be approved until repo_write_scope is non-empty")
        if state["status"].get("threat_model") not in {"completed", "not_required"}:
            raise SystemExit("Plan Gate cannot be approved until threat_model (section of plan.md) is completed")
        action_errors = external_action_errors(state)
        if action_errors:
            raise SystemExit("Plan Gate cannot be approved; external action policy errors: " + "; ".join(action_errors))
        if state.get("gates", {}).get("production", {}).get("status") != "not_required":
            if state["status"].get("production_plan") != "completed":
                raise SystemExit("Plan Gate cannot be approved until production_plan=completed")
    elif name == "security":
        required = ["testing", "verification", "code_review", "security_review", "threat_model"]
        incomplete = [item for item in required if state["status"].get(item) not in {"completed", "not_required"}]
        if incomplete:
            raise SystemExit("Security Gate cannot be approved; incomplete: " + ", ".join(incomplete))
    elif name == "production":
        required = ["implementation", "testing", "verification", "code_review", "security_review", "production_plan"]
        incomplete = [item for item in required if state["status"].get(item) not in {"completed", "not_required"}]
        if incomplete:
            raise SystemExit("Production Gate cannot be approved; incomplete: " + ", ".join(incomplete))
        if state["gates"].get("security", {}).get("status") not in {"approved", "not_required"}:
            raise SystemExit("Production Gate cannot be approved before the Security Gate")
        prod_actions = [a for a in state.get("external_actions", {}).get("allowed", [])
                        if a.get("effect") in {"PRODUCTION_CHANGE", "DESTRUCTIVE"}]
        if not prod_actions:
            raise SystemExit("Production Gate cannot be approved without an allowed PRODUCTION_CHANGE/DESTRUCTIVE action")

    state["gates"][name] = {"status": "approved", "approved_by": args.by, "approved_at": utc_now()}
    if name == "definition":
        state["phase"] = "planning"
    if name == "plan":
        state["phase"] = "implementation"
        state["status"]["implementation"] = "pending"
    if name == "security":
        state["phase"] = "ready_for_pr"
    if name == "production":
        state["phase"] = "production_authorized"
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Recorded HUMAN approval: {state['id']} gate={name} by={args.by}")


def cmd_mark(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    if args.item not in state["status"]:
        raise SystemExit(f"Unknown status item: {args.item}")
    if args.status not in VALID_STATUS:
        raise SystemExit(f"Invalid status: {args.status}")
    if args.item == "production_verification" and args.status == "completed":
        if state.get("gates", {}).get("production", {}).get("status") != "approved":
            raise SystemExit("production_verification cannot be completed before Production Gate approval")
    state["status"][args.item] = args.status
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Updated {state['id']}: {args.item}={args.status}")


def cmd_phase(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    state["phase"] = args.phase
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Updated {state['id']}: phase={args.phase}")


def cmd_scope(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    if state["gates"].get("plan", {}).get("status") == "approved":
        raise SystemExit("repo_write_scope is frozen after Plan Gate approval. Return to Planning and re-approve the plan.")
    scope = list(state.get("repo_write_scope", []))
    for item in args.add:
        if item not in scope:
            scope.append(item)
    state["repo_write_scope"] = scope
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Updated {state['id']} write scope:")
    for item in scope:
        print(f"  - {item}")


def cmd_allow_action(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    if state["gates"].get("plan", {}).get("status") == "approved":
        raise SystemExit("External action allowlist is frozen after Plan Gate approval. Return to Planning and re-approve the plan.")
    effect = args.effect.upper()
    if effect not in EXTERNAL_EFFECTS:
        raise SystemExit(f"Unsupported external effect: {effect}")

    if effect in {"PRODUCTION_CHANGE", "DESTRUCTIVE"}:
        if state["track"] in {"TASK", "BUGFIX"}:
            raise SystemExit("Production/destructive work is security-sensitive and must be upgraded to FEATURE/EPIC (or genuine HOTFIX).")
        was_security_sensitive = state["security"].get("security_sensitive", False)
        state["security"]["security_sensitive"] = True
        state["security"]["threat_model_required"] = True
        state["security"]["security_review_required"] = True
        state["effects"]["security_sensitive"] = True
        if state.get("schema_version", 3) < LEAN_SCHEMA:
            state["gates"]["security"] = gate("pending")
        if state["status"].get("threat_model") == "not_required":
            state["status"]["threat_model"] = "pending"
        if state["status"].get("security_review") == "not_required":
            state["status"]["security_review"] = "pending"
        state["gates"]["production"] = gate("pending")
        state["status"]["production_plan"] = "pending"
        state["status"]["production_verification"] = "pending"
        # Adding a new security/production boundary after Definition approval invalidates that approval.
        if not was_security_sensitive and state.get("gates", {}).get("definition", {}).get("status") == "approved":
            state["gates"]["definition"] = gate("pending")
            if state["status"].get("artifact_review") != "not_required":
                state["status"]["artifact_review"] = "pending"
            state["phase"] = "definition"
    if effect == "PRODUCTION_CHANGE":
        state["effects"]["production_change"] = True
    if effect == "DESTRUCTIVE":
        state["effects"]["destructive"] = True
    state["effects"]["external_write"] = True

    action = {
        "plugin": args.plugin,
        "action": args.action,
        "effect": effect,
        "target": args.target,
        "purpose": args.purpose,
    }
    allowed = state.setdefault("external_actions", {}).setdefault("allowed", [])
    if action not in allowed:
        allowed.append(action)
    ensure_dynamic_artifacts(directory, state)
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Allowed external action for {state['id']}: {args.plugin}.{args.action} [{effect}]")


def cmd_checkpoint(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    path = create_checkpoint(
        directory,
        state,
        agent=args.agent,
        current_unit=args.current_unit,
        next_action=args.next_action,
        verification=args.verification or [],
        summary=args.summary,
        completed=args.completed or [],
        in_progress=args.in_progress or [],
        decisions=args.decision or [],
        known_issues=args.known_issue or [],
    )
    print(f"Created checkpoint {path.relative_to(ROOT)}")


def _bullet_lines(items: list[str] | None, empty: str = "- None recorded") -> str:
    return "\n".join(f"- {item}" for item in items) if items else empty


def cmd_handoff(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    snapshot = git_working_snapshot(ignore_patterns=_continuity_ignore_patterns(directory))
    path = create_checkpoint(
        directory,
        state,
        agent=args.agent,
        current_unit=args.current_unit,
        next_action=args.next_action,
        verification=args.verification or [],
        git_snapshot=snapshot,
        summary=args.summary,
        completed=args.completed or [],
        in_progress=args.in_progress or [],
        decisions=args.decision or [],
        known_issues=args.known_issue or [],
    )
    state = load_json(directory / "state.json")
    state["continuity"]["last_handoff_at"] = utc_now()
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)

    gates = "\n".join(
        f"- {name}: {data.get('status')}" for name, data in state.get("gates", {}).items()
    )
    scope = _bullet_lines(state.get("repo_write_scope"), "- No repository write scope recorded")
    changed = _bullet_lines(snapshot.get("changed_files"), "- No changed files")
    handoff = f"""# Session Handoff

## Identity
- Task: {state['id']} — {state['title']}
- From agent: {args.agent}
- Timestamp: {state['continuity']['last_handoff_at']}
- Phase: {state.get('phase')}
- Checkpoint: {path.name}
- Branch: {snapshot.get('branch')}
- HEAD: {snapshot.get('head')}

## Current unit
{args.current_unit or 'Not recorded'}

## Summary
{args.summary or 'No summary recorded.'}

## Completed
{_bullet_lines(args.completed)}

## In progress
{_bullet_lines(args.in_progress)}

## Last verified state
{_bullet_lines(args.verification)}

## Important decisions
{_bullet_lines(args.decision)}

## Known issues / blockers
{_bullet_lines(args.known_issue)}

## Next action
{args.next_action}

## Human gates (authoritative state remains state.json)
{gates}

## Approved repository write scope
{scope}

## Working tree at handoff
- Status: {snapshot.get('working_tree')}
- Changed files: {len(snapshot.get('changed_files', []))}

{changed}

> This handoff is context, not authorization. `state.json`, approved artifacts, Git evidence, and repository policy remain authoritative.
"""
    portability = "portable-after-repository-sync" if snapshot.get("working_tree") == "clean" else "same-working-tree-only-until-changes-are-persisted"
    handoff = handoff.replace(
        "## Working tree at handoff\n",
        f"## Workspace portability\n- Mode: {portability}\n- Note: checkpoints store metadata/hashes, not copies of source changes.\n\n## Working tree at handoff\n",
    )
    (directory / "session-handoff.md").write_text(handoff, encoding="utf-8")
    print(f"Handoff recorded for {state['id']} at {directory.relative_to(ROOT) / 'session-handoff.md'}")
    if snapshot.get("working_tree") == "dirty":
        print("WARNING: working tree is dirty. This handoff is portable only within the same workspace until code changes are persisted/synchronized by an approved Git workflow.")


def cmd_resume(args: argparse.Namespace) -> None:
    directory = select_resume_task(args.task)
    state = load_json(directory / "state.json")
    current = git_working_snapshot(ignore_patterns=_continuity_ignore_patterns(directory))
    report = build_resume_report(directory, state, current, args.available_capability)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print("RESUME REPORT")
    print(f"Task: {report['task_id']} — {report['title']}")
    print(f"Track / phase: {report['track']} / {report['phase']}")
    print(f"Last agent: {report['last_agent'] or 'unknown'}")
    print(f"Last checkpoint: {report['last_checkpoint'] or 'none'}")
    print(f"Current unit: {report['current_unit'] or 'not recorded'}")
    print(f"Next action: {report['next_action'] or 'not recorded'}")
    print(f"Branch / HEAD: {current.get('branch')} / {current.get('head')}")
    print(f"Working tree: {current.get('working_tree')}")
    print("Gates: " + ", ".join(f"{k}={v.get('status')}" for k, v in report['gates'].items()))
    if report["uncheckpointed_changes"]:
        print("Uncheckpointed changed files detected:")
        for item in report["uncheckpointed_changes"]:
            print(f"  - {item}")
    elif report["working_tree_changed_since_checkpoint"]:
        print("Working tree content changed since the last checkpoint (same-file changes may be involved).")
    if report["head_changed_since_checkpoint"]:
        print("HEAD changed since the last checkpoint; inspect commits before continuing.")
    if report["missing_capabilities"]:
        print("Capabilities unavailable in this environment for approved external actions:")
        for item in report["missing_capabilities"]:
            print(f"  - {item}")
        print("Only the affected external actions are blocked; unrelated approved work may continue.")
    if report["blocked"]:
        print(f"TASK BLOCKED: {report['block_reason'] or 'no reason recorded'}")
    print("Before modifying files: read the task artifacts, inspect Git diff/status, and verify the current unit against the approved plan.")


def cmd_record_evidence(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    effect = args.effect.upper()
    if effect != "READ" and effect not in EXTERNAL_EFFECTS and effect != "REPO_WRITE":
        raise SystemExit(f"Unsupported evidence effect: {effect}")

    if effect in EXTERNAL_EFFECTS:
        matches = [a for a in state.get("external_actions", {}).get("allowed", [])
                   if a.get("plugin") == args.plugin and a.get("action") == args.action and a.get("effect") == effect]
        if not matches:
            raise SystemExit("Cannot record non-read external evidence for an action outside external_actions.allowed")

    evidence = {
        "plugin": args.plugin,
        "action": args.action,
        "effect": effect,
        "summary": args.summary,
        "artifact": args.artifact,
        "recorded_at": utc_now(),
        "verification": {
            "status": "pending",
            "verified_by": None,
            "verified_at": None,
            "summary": None,
        },
    }
    state.setdefault("external_actions", {}).setdefault("evidence", []).append(evidence)
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Recorded plugin/tool evidence for {state['id']}: {args.plugin}.{args.action} [{effect}]")


def cmd_verify_evidence(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    evidence = state.get("external_actions", {}).get("evidence", [])
    if args.index < 0 or args.index >= len(evidence):
        raise SystemExit(f"Evidence index out of range: {args.index}; count={len(evidence)}")
    item = evidence[args.index]
    item["verification"] = {
        "status": "verified",
        "verified_by": args.by,
        "verified_at": utc_now(),
        "summary": args.summary,
    }
    state["updated_at"] = utc_now()
    save_json(directory / "state.json", state)
    print(f"Verified evidence #{args.index} for {state['id']} by={args.by}")


def verified_production_evidence_errors(state: dict) -> list[str]:
    if state.get("gates", {}).get("production", {}).get("status") == "not_required":
        return []
    evidence = state.get("external_actions", {}).get("evidence", [])
    verified = [e for e in evidence
                if e.get("effect") in {"PRODUCTION_CHANGE", "DESTRUCTIVE"}
                and e.get("verification", {}).get("status") == "verified"]
    if not verified:
        return ["No independently verified PRODUCTION_CHANGE/DESTRUCTIVE execution evidence recorded"]
    return []


def external_action_errors(state: dict) -> list[str]:
    errors: list[str] = []
    allowed = state.get("external_actions", {}).get("allowed", [])
    for idx, action in enumerate(allowed):
        effect = action.get("effect")
        if effect not in EXTERNAL_EFFECTS:
            errors.append(f"external_actions.allowed[{idx}] has invalid effect {effect!r}")
        for field in ("plugin", "action", "target", "purpose"):
            if not action.get(field):
                errors.append(f"external_actions.allowed[{idx}] missing {field}")
    if state.get("effects", {}).get("external_write") and not allowed:
        errors.append("effects.external_write=true but external_actions.allowed is empty")
    if state.get("effects", {}).get("production_change") and not any(a.get("effect") == "PRODUCTION_CHANGE" for a in allowed):
        errors.append("effects.production_change=true but no PRODUCTION_CHANGE action is allowed")
    if state.get("effects", {}).get("destructive") and not any(a.get("effect") == "DESTRUCTIVE" for a in allowed):
        errors.append("effects.destructive=true but no DESTRUCTIVE action is allowed")
    return errors


def git_changed_files(base: str) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only", base, "HEAD"],
    ]
    last_error = ""
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
        last_error = result.stderr.strip()
    raise SystemExit(f"Unable to compute changed files from {base}: {last_error}")


CLASSIFY_DEFAULTS = {
    "sensitive": [
        "auth", "tenant", "permission", "guard", "security", "crypto", "secret", "token",
        "webhook", "upload", "payment", "migrations?/", "alembic", r"\.github/workflows",
        "(^|/)dockerfile", "docker-compose", "^deploy/", r"\.env",
        r"requirements\.txt", r"package(-lock)?\.json", r"pyproject\.toml", r"go\.mod",
    ],
    "non_code": [
        r"(^|/)(tests?|__tests__|docs|\.tasks|\.memory-bank|\.ai|tools)/",
        "(^|/)test_[^/]*$", r"\.(test|spec)\.[a-z]+$", r"\.md$", r"\.pdf$",
    ],
    "module_depth": 2,
    "max_task_code_files": 5,
    "max_feature_code_files": 15,
}
TRACK_ORDER = ["TASK", "BUGFIX", "FEATURE", "EPIC"]


def load_classify_config() -> dict:
    """Defaults overridden by `.ai/classify.json` (project-specific paths/limits)."""
    config = dict(CLASSIFY_DEFAULTS)
    path = ROOT / ".ai" / "classify.json"
    if path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))
    return config


def classify_paths(paths: Iterable[str], bugfix: bool = False, current: str | None = None,
                   config: dict | None = None) -> dict:
    """Deterministic track from touched paths. Only escalates, never downgrades `current`."""
    cfg = config or load_classify_config()
    sensitive_re = re.compile("(" + "|".join(cfg["sensitive"]) + ")", re.IGNORECASE)
    non_code_re = re.compile("(" + "|".join(cfg["non_code"]) + ")", re.IGNORECASE)
    files = [p.replace("\\", "/").removeprefix("./") for p in paths if p.strip()]
    sensitive = [p for p in files if sensitive_re.search(p)]
    code = [p for p in files if not non_code_re.search(p)]
    depth = cfg["module_depth"]
    modules = {"/".join(p.split("/")[:depth]) for p in code}
    max_task, max_feature = cfg["max_task_code_files"], cfg["max_feature_code_files"]
    reasons: list[str] = []
    track = "BUGFIX" if bugfix else "TASK"
    if sensitive:
        track = "FEATURE"
        reasons.append(f"sensitive paths: {', '.join(sensitive[:5])}")
    if len(modules) > 1:
        track = "FEATURE"
        reasons.append(f"{len(modules)} code modules")
    if len(code) > max_feature:
        track = "FEATURE"
        reasons.append(f"{len(code)} code files > {max_feature}")
    elif len(code) > max_task and track in ("TASK", "BUGFIX"):
        reasons.append(f"{len(code)} code files > {max_task}: split or justify")
    if current in TRACK_ORDER and TRACK_ORDER.index(current) > TRACK_ORDER.index(track):
        track = current
        reasons.append(f"kept {current} (never downgrade)")
    return {"track": track, "security_sensitive": bool(sensitive), "code_files": len(code),
            "modules": sorted(modules), "reasons": reasons}


def cmd_classify(args: argparse.Namespace) -> None:
    paths = args.paths or git_changed_files(args.base)
    print(json.dumps(classify_paths(paths, args.bugfix, args.current), indent=2))


def matches_scope(path: str, patterns: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        pattern = pattern.replace("\\", "/")
        if fnmatch.fnmatch(normalized, pattern):
            return True
        # Treat a bare directory path as recursive.
        if not any(ch in pattern for ch in "*?[") and normalized.startswith(pattern.rstrip("/") + "/"):
            return True
    return False


def secret_scan(paths: Iterable[str]) -> list[str]:
    findings: list[str] = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            continue
        if path.name == "Dockerfile":
            eligible = True
        else:
            eligible = path.suffix.lower() in SECRET_SCAN_SUFFIXES
        if not eligible or path.stat().st_size > 2_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, regex in SECRET_PATTERNS:
            if regex.search(content):
                findings.append(f"{relative}: possible {label}")
    return findings


def required_gate_errors(state: dict, stage: str) -> list[str]:
    errors: list[str] = []
    if state["track"] in FULL_GATE_TRACKS:
        for name in ("definition", "plan"):
            if state["gates"][name]["status"] not in {"approved", "not_required"}:
                errors.append(f"Human gate '{name}' is not approved")
        if state["gates"]["plan"]["status"] == "not_required":
            errors.append("Human gate 'plan' is not_required for a full-gate track")
    if stage in {"pr", "production", "post-production"} and state["security"]["security_review_required"]:
        if state["gates"]["security"]["status"] not in {"approved", "not_required"}:
            errors.append("Human security gate is not approved")
    if stage in {"production", "post-production"} and state.get("gates", {}).get("production", {}).get("status") != "not_required":
        if state["gates"]["production"]["status"] != "approved":
            errors.append("Human production gate is not approved")
    return errors


def completion_errors(state: dict) -> list[str]:
    errors: list[str] = []
    for item in PR_REQUIRED_STATUS:
        value = state["status"].get(item)
        if value not in {"completed", "not_required"}:
            errors.append(f"Completion status '{item}' is {value!r}, expected completed/not_required")
    if state["security"]["security_review_required"]:
        value = state["status"].get("security_review")
        if value != "completed":
            errors.append(f"Security review status is {value!r}, expected completed")
    return errors


def review_section_errors(directory: Path, state: dict) -> list[str]:
    """Lean tasks: review.md must exist for FEATURE+/sensitive work and carry a filled security section."""
    errors: list[str] = []
    if state.get("schema_version", 3) < LEAN_SCHEMA or not artifact_required("review.md", state):
        return errors
    review = directory / "review.md"
    if not review.exists():
        return ["review.md is missing"]
    if state["security"]["security_review_required"]:
        text = review.read_text(encoding="utf-8").replace("\r\n", "\n")
        match = re.search(r"^## Security review\s*\n(.*?)(?=^## |\Z)", text, flags=re.MULTILINE | re.DOTALL)
        body = [line for line in (match.group(1).splitlines() if match else []) if line.strip() and not line.strip().startswith("<!--")]
        if len(body) < 3:
            errors.append("review.md needs a filled '## Security review' section (invariants, findings, residual risk)")
    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    directory = find_task(args.task)
    state = load_json(directory / "state.json")
    errors: list[str] = []

    if state.get("blocked"):
        errors.append(f"Task is blocked: {state.get('block_reason') or 'no reason recorded'}")

    errors.extend(required_gate_errors(state, args.stage))
    errors.extend(external_action_errors(state))

    if args.stage in {"pr", "production", "post-production"}:
        errors.extend(completion_errors(state))
        errors.extend(review_section_errors(directory, state))
    if args.stage in {"production", "post-production"}:
        if state["status"].get("production_plan") not in {"completed", "not_required"}:
            errors.append(f"Production plan status is {state['status'].get('production_plan')!r}, expected completed/not_required")
    if args.stage == "post-production":
        if state["status"].get("production_verification") != "completed":
            errors.append(f"Production verification status is {state['status'].get('production_verification')!r}, expected completed")
        errors.extend(verified_production_evidence_errors(state))

    changed = git_changed_files(args.base) if not args.no_git else []
    if changed:
        current_task_prefix = str(directory.relative_to(ROOT)).replace("\\", "/") + "/**"
        allowed = list(state.get("repo_write_scope", [])) + [current_task_prefix]
        out_of_scope = [path for path in changed if not matches_scope(path, allowed)]
        if out_of_scope:
            errors.append("Files outside approved repo_write_scope:\n  - " + "\n  - ".join(out_of_scope))

        secrets = secret_scan(changed)
        if secrets:
            errors.append("High-confidence secret patterns found:\n  - " + "\n  - ".join(secrets))

    if errors:
        print("AI Engineering Protocol validation FAILED", file=sys.stderr)
        for error in errors:
            print(f"\n- {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"AI Engineering Protocol validation PASSED for {state['id']} stage={args.stage}")
    if changed:
        print(f"Validated {len(changed)} changed file(s) against {len(state.get('repo_write_scope', []))} declared scope pattern(s).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Engineering Protocol helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-project", help="Create PROJ-000 initialization task")
    p.add_argument("--title", required=True)
    p.add_argument("--complexity", type=int, default=8)
    p.add_argument("--risk", choices=["low", "medium", "high"], default="high")
    p.set_defaults(func=cmd_init_project)

    p = sub.add_parser("new-task", help="Create a task with state and artifacts")
    p.add_argument("--track", required=True, choices=list(TRACK_PREFIX))
    p.add_argument("--title", required=True)
    p.add_argument("--complexity", type=int, default=3)
    p.add_argument("--risk", choices=["low", "medium", "high"], default="low")
    p.add_argument("--security-sensitive", action="store_true")
    p.add_argument("--external-write", action="store_true", help="Task plans an external non-production write")
    p.add_argument("--production-change", action="store_true", help="Task plans a live production change")
    p.add_argument("--destructive", action="store_true", help="Task plans a destructive/irreversible action")
    p.set_defaults(func=cmd_new_task)

    p = sub.add_parser("status", help="Print task state")
    p.add_argument("--task", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("approve", help="Record an explicit HUMAN gate approval")
    p.add_argument("--task", required=True)
    p.add_argument("--gate", required=True, choices=["definition", "plan", "security", "production"])
    p.add_argument("--by", required=True)
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("mark", help="Update a workflow status item")
    p.add_argument("--task", required=True)
    p.add_argument("--item", required=True)
    p.add_argument("--status", required=True, choices=sorted(VALID_STATUS))
    p.set_defaults(func=cmd_mark)

    p = sub.add_parser("phase", help="Update current phase")
    p.add_argument("--task", required=True)
    p.add_argument("--phase", required=True)
    p.set_defaults(func=cmd_phase)

    p = sub.add_parser("scope", help="Add approved write-scope patterns")
    p.add_argument("--task", required=True)
    p.add_argument("--add", action="append", required=True, help="Glob or directory path; repeat as needed")
    p.set_defaults(func=cmd_scope)

    p = sub.add_parser("allow-action", help="Declare a planned external side effect before Plan Gate approval")
    p.add_argument("--task", required=True)
    p.add_argument("--plugin", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--effect", required=True, choices=sorted(EXTERNAL_EFFECTS))
    p.add_argument("--target", required=True)
    p.add_argument("--purpose", required=True)
    p.set_defaults(func=cmd_allow_action)

    p = sub.add_parser("checkpoint", help="Persist a cross-AI continuity checkpoint")
    p.add_argument("--task", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--current-unit")
    p.add_argument("--next-action")
    p.add_argument("--summary")
    p.add_argument("--completed", action="append")
    p.add_argument("--in-progress", action="append")
    p.add_argument("--verification", action="append")
    p.add_argument("--decision", action="append")
    p.add_argument("--known-issue", action="append")
    p.set_defaults(func=cmd_checkpoint)

    p = sub.add_parser("handoff", help="Create a fresh checkpoint and current session-handoff.md")
    p.add_argument("--task", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--current-unit")
    p.add_argument("--next-action", required=True)
    p.add_argument("--summary")
    p.add_argument("--completed", action="append")
    p.add_argument("--in-progress", action="append")
    p.add_argument("--verification", action="append")
    p.add_argument("--decision", action="append")
    p.add_argument("--known-issue", action="append")
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("resume", help="Reconstruct current task state for a new AI worker without mutating approvals")
    p.add_argument("--task", help="Task ID; omit only when exactly one task is active")
    p.add_argument("--available-capability", action="append", help="Installed/connected capability name; repeat to inventory current environment")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("record-evidence", help="Record plugin/tool evidence; evidence never approves a gate")
    p.add_argument("--task", required=True)
    p.add_argument("--plugin", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--effect", required=True, choices=["READ", "REPO_WRITE"] + sorted(EXTERNAL_EFFECTS))
    p.add_argument("--summary", required=True)
    p.add_argument("--artifact")
    p.set_defaults(func=cmd_record_evidence)

    p = sub.add_parser("verify-evidence", help="Independently verify recorded plugin/tool evidence")
    p.add_argument("--task", required=True)
    p.add_argument("--index", required=True, type=int)
    p.add_argument("--by", required=True)
    p.add_argument("--summary", required=True)
    p.set_defaults(func=cmd_verify_evidence)

    p = sub.add_parser("validate", help="Validate gates, write scope and high-confidence secret patterns")
    p.add_argument("--task", required=True)
    p.add_argument("--base", default="origin/main")
    p.add_argument("--stage", choices=["implementation", "pr", "production", "post-production"], default="implementation")
    p.add_argument("--no-git", action="store_true", help="Validate state only; skip diff/scope/secret scan")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("classify", help="Deterministic track from touched paths (default: git diff vs --base)")
    p.add_argument("paths", nargs="*")
    p.add_argument("--base", default="origin/main")
    p.add_argument("--bugfix", action="store_true", help="Work is a bug fix (adds regression-test requirement)")
    p.add_argument("--current", choices=TRACK_ORDER, help="Current track; result never goes below it")
    p.set_defaults(func=cmd_classify)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
