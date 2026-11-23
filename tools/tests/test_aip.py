import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "aip.py"
spec = importlib.util.spec_from_file_location("aip", MODULE_PATH)
aip = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(aip)


class ProtocolTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(aip.slugify("SOC Integration / Employees"), "soc-integration-employees")

    def test_security_sensitive_bugfix_rejected(self):
        with self.assertRaises(SystemExit):
            aip.blank_state("BUG-001", "auth bug", "BUGFIX", 2, True, "high")

    def test_classify_small_docs_and_tests_is_task(self):
        cfg = aip.CLASSIFY_DEFAULTS
        r = aip.classify_paths(["src/app/tests/test_a.py", "docs/x.md", ".tasks/T/plan.md"], config=cfg)
        self.assertEqual(r["track"], "TASK")

    def test_classify_sensitive_or_multi_module_is_feature_and_never_downgrades(self):
        cfg = aip.CLASSIFY_DEFAULTS
        self.assertEqual(aip.classify_paths(["src/auth/jwt.py"], config=cfg)["track"], "FEATURE")
        self.assertEqual(aip.classify_paths(["src/a/x.py", "src/b/y.py"], config=cfg)["track"], "FEATURE")
        self.assertEqual(aip.classify_paths(["src/a/x.py"], current="FEATURE", config=cfg)["track"], "FEATURE")
        self.assertEqual(aip.classify_paths(["src/a/x.py"], bugfix=True, config=cfg)["track"], "BUGFIX")

    def test_feature_requires_plan_gate_only(self):
        state = aip.blank_state("FEAT-001", "x", "FEATURE", 4, False, "medium")
        self.assertEqual(state["gates"]["definition"]["status"], "not_required")
        errors = aip.required_gate_errors(state, "implementation")
        self.assertEqual(len(errors), 1)
        state["gates"]["plan"]["status"] = "approved"
        self.assertEqual(aip.required_gate_errors(state, "implementation"), [])

    def test_legacy_v3_definition_gate_still_enforced(self):
        state = aip.blank_state("FEAT-002", "x", "FEATURE", 4, False, "medium")
        state["schema_version"] = 3
        state["gates"]["definition"]["status"] = "pending"
        state["gates"]["plan"]["status"] = "approved"
        self.assertEqual(len(aip.required_gate_errors(state, "implementation")), 1)

    def test_security_is_folded_into_merge_but_requires_review_section(self):
        state = aip.blank_state("FEAT-001", "auth", "FEATURE", 5, True, "high")
        self.assertEqual(state["gates"]["security"]["status"], "not_required")
        state["gates"]["plan"]["status"] = "approved"
        self.assertEqual(aip.required_gate_errors(state, "pr"), [])
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.assertIn("review.md is missing", aip.review_section_errors(d, state))
            empty = "# Review\n\n## Security review\n\n<!-- fill -->\n"
            filled = "# Review\n\n## Security review\n\nInvariants: A\nFindings: none\nResidual risk: low\n\n## Other\n"
            (d / "review.md").write_text(empty, encoding="utf-8")
            self.assertTrue(aip.review_section_errors(d, state))
            (d / "review.md").write_text(filled, encoding="utf-8")
            self.assertEqual(aip.review_section_errors(d, state), [])

    def test_plan_gate_requires_threat_model_for_sensitive_work(self):
        state = aip.blank_state("FEAT-003", "auth", "FEATURE", 5, True, "high")
        self.assertEqual(state["status"]["threat_model"], "pending")
        self.assertEqual(state["status"]["artifact_review"], "not_required")

    def test_scope_matching(self):
        self.assertTrue(aip.matches_scope("src/Auth/Login.cs", ["src/Auth/**"]))
        self.assertTrue(aip.matches_scope("src/Auth/Login.cs", ["src/Auth"]))
        self.assertFalse(aip.matches_scope("src/Billing/Pay.cs", ["src/Auth/**"]))

    def test_secret_patterns(self):
        content = "key=" + "AKIA" + "ABCDEFGHIJKLMNOP"
        self.assertTrue(any(regex.search(content) for _, regex in aip.SECRET_PATTERNS))

    def test_completion_accepts_not_required(self):
        state = aip.blank_state("TASK-001", "label", "TASK", 1, False, "low")
        for key in ("implementation", "testing", "code_review"):
            state["status"][key] = "completed"
        state["status"]["verification"] = "not_required"
        state["status"]["retrospective"] = "not_required"
        self.assertEqual(aip.completion_errors(state), [])

    def test_lean_artifacts(self):
        feature = aip.blank_state("FEAT-001", "x", "FEATURE", 4, False, "medium")
        task = aip.blank_state("TASK-001", "x", "TASK", 1, False, "low")
        self.assertTrue(aip.artifact_required("plan.md", task))
        self.assertFalse(aip.artifact_required("review.md", task))
        self.assertTrue(aip.artifact_required("review.md", feature))
        for name in ("prd.md", "specification.md", "architecture.md", "threat-model.md", "retrospective.md", "security-review.md"):
            self.assertFalse(aip.artifact_required(name, feature))

    def test_project_requires_threat_model(self):
        state = aip.blank_state("PROJ-000", "x", "PROJECT", 8, True, "high")
        self.assertTrue(state["security"]["threat_model_required"])
        self.assertEqual(state["status"]["threat_model"], "pending")


class PluginGovernanceTests(unittest.TestCase):
    def test_production_change_requires_security_and_production_gate(self):
        state = aip.blank_state("FEAT-010", "deploy", "FEATURE", 5, False, "medium", production_change=True)
        self.assertTrue(state["security"]["security_sensitive"])
        self.assertTrue(state["effects"]["production_change"])
        self.assertEqual(state["gates"]["production"]["status"], "pending")
        self.assertEqual(state["status"]["production_plan"], "pending")

    def test_destructive_bugfix_rejected(self):
        with self.assertRaises(SystemExit):
            aip.blank_state("BUG-010", "drop thing", "BUGFIX", 2, False, "high", destructive=True)

    def test_external_action_errors_require_matching_production_action(self):
        state = aip.blank_state("FEAT-011", "deploy", "FEATURE", 5, False, "high", production_change=True)
        errors = aip.external_action_errors(state)
        self.assertIn("effects.production_change=true but no PRODUCTION_CHANGE action is allowed", errors)
        state["external_actions"]["allowed"].append({
            "plugin": "Cloudflare",
            "action": "deploy",
            "effect": "PRODUCTION_CHANGE",
            "target": "production",
            "purpose": "Deploy approved release",
        })
        self.assertEqual(aip.external_action_errors(state), [])

    def test_production_gate_required_only_at_production_stage(self):
        state = aip.blank_state("FEAT-012", "deploy", "FEATURE", 5, False, "high", production_change=True)
        state["gates"]["definition"]["status"] = "approved"
        state["gates"]["plan"]["status"] = "approved"
        state["gates"]["security"]["status"] = "approved"
        self.assertNotIn("Human production gate is not approved", aip.required_gate_errors(state, "pr"))
        self.assertIn("Human production gate is not approved", aip.required_gate_errors(state, "production"))

    def test_read_evidence_does_not_need_external_allowlist(self):
        state = aip.blank_state("FEAT-013", "read docs", "FEATURE", 4, False, "low")
        self.assertEqual(state["external_actions"]["allowed"], [])

    def test_schema_v3_contains_external_governance(self):
        state = aip.blank_state("FEAT-014", "x", "FEATURE", 4, False, "low")
        self.assertEqual(state["schema_version"], aip.LEAN_SCHEMA)
        self.assertIn("effects", state)
        self.assertIn("external_actions", state)
        self.assertIn("production", state["gates"])

class GovernanceMutationTests(unittest.TestCase):
    def setUp(self):
        self._tasks_dir = aip.TASKS_DIR
        self.tmp = tempfile.TemporaryDirectory()
        aip.TASKS_DIR = Path(self.tmp.name)

    def tearDown(self):
        aip.TASKS_DIR = self._tasks_dir
        self.tmp.cleanup()

    def _write_task(self, state):
        d = aip.TASKS_DIR / f"{state['id']}-test"
        d.mkdir()
        aip.save_json(d / "state.json", state)
        return d

    def test_new_production_boundary_adds_production_gate_and_threat_model(self):
        state = aip.blank_state("FEAT-020", "feature", "FEATURE", 4, False, "medium")
        state["status"]["threat_model"] = "not_required"
        state["status"]["security_review"] = "not_required"
        directory = self._write_task(state)
        args = type("Args", (), {
            "task": "FEAT-020", "plugin": "Cloudflare", "action": "deploy",
            "effect": "PRODUCTION_CHANGE", "target": "production", "purpose": "Deploy"
        })()
        aip.cmd_allow_action(args)
        updated = aip.load_json(directory / "state.json")
        self.assertEqual(updated["gates"]["production"]["status"], "pending")
        self.assertEqual(updated["gates"]["security"]["status"], "not_required")
        self.assertEqual(updated["status"]["threat_model"], "pending")
        self.assertTrue((directory / "review.md").exists())

    def test_repo_scope_frozen_after_plan_gate(self):
        state = aip.blank_state("FEAT-021", "feature", "FEATURE", 4, False, "low")
        state["gates"]["plan"]["status"] = "approved"
        self._write_task(state)
        args = type("Args", (), {"task": "FEAT-021", "add": ["src/**"]})()
        with self.assertRaises(SystemExit):
            aip.cmd_scope(args)


class CrossAIHandoffTests(unittest.TestCase):
    def setUp(self):
        self._tasks_dir = aip.TASKS_DIR
        self.tmp = tempfile.TemporaryDirectory()
        aip.TASKS_DIR = Path(self.tmp.name)

    def tearDown(self):
        aip.TASKS_DIR = self._tasks_dir
        self.tmp.cleanup()

    def _write_task(self, state):
        d = aip.TASKS_DIR / f"{state['id']}-test"
        d.mkdir()
        aip.save_json(d / "state.json", state)
        (d / "checkpoints").mkdir()
        (d / "session-handoff.md").write_text("# Session Handoff\n", encoding="utf-8")
        return d

    def test_schema_v3_contains_continuity_without_changing_gates(self):
        state = aip.blank_state("FEAT-030", "handoff", "FEATURE", 4, False, "low")
        self.assertEqual(state["schema_version"], aip.LEAN_SCHEMA)
        self.assertIn("continuity", state)
        self.assertIsNone(state["continuity"]["last_checkpoint"])
        self.assertEqual(state["gates"]["plan"]["status"], "pending")

    def test_create_task_files_creates_plan_review_and_checkpoints(self):
        state = aip.blank_state("FEAT-031", "handoff", "FEATURE", 4, False, "low")
        directory = aip.TASKS_DIR / "FEAT-031-handoff"
        aip.create_task_files(directory, state)
        self.assertTrue((directory / "plan.md").exists())
        self.assertTrue((directory / "review.md").exists())
        self.assertFalse((directory / "session-handoff.md").exists())
        self.assertTrue((directory / "checkpoints").is_dir())

    def test_checkpoint_preserves_gate_and_scope(self):
        state = aip.blank_state("FEAT-032", "handoff", "FEATURE", 4, False, "low")
        state["gates"]["definition"]["status"] = "approved"
        state["gates"]["plan"]["status"] = "approved"
        state["repo_write_scope"] = ["src/**"]
        directory = self._write_task(state)
        before = json.loads(json.dumps(state))

        snapshot = {
            "branch": "feat/x", "head": "abc123", "working_tree": "dirty",
            "changed_files": ["src/a.py"], "untracked_files": [],
        }
        path = aip.create_checkpoint(directory, state, agent="Codex", current_unit="Task 3", next_action="Continue tests", verification=["12 tests passed"], git_snapshot=snapshot)
        updated = aip.load_json(directory / "state.json")

        self.assertTrue(path.exists())
        self.assertEqual(updated["gates"], before["gates"])
        self.assertEqual(updated["repo_write_scope"], before["repo_write_scope"])
        self.assertEqual(updated["continuity"]["last_checkpoint"], path.name)
        self.assertEqual(updated["continuity"]["current_unit"], "Task 3")

    def test_resume_detects_uncheckpointed_changes(self):
        state = aip.blank_state("FEAT-033", "handoff", "FEATURE", 4, False, "low")
        directory = self._write_task(state)
        checkpoint_snapshot = {
            "branch": "feat/x", "head": "abc123", "working_tree": "dirty",
            "changed_files": ["src/a.py"], "untracked_files": [],
        }
        aip.create_checkpoint(directory, state, agent="Codex", current_unit="Task 3", next_action="Continue", verification=[], git_snapshot=checkpoint_snapshot)
        current = {
            "branch": "feat/x", "head": "abc123", "working_tree": "dirty",
            "changed_files": ["src/a.py", "src/b.py"], "untracked_files": [],
        }
        report = aip.build_resume_report(directory, aip.load_json(directory / "state.json"), current, available_capabilities=[])
        self.assertIn("src/b.py", report["uncheckpointed_changes"])
        self.assertEqual(report["next_action"], "Continue")


    def test_resume_detects_same_file_change_via_fingerprint(self):
        state = aip.blank_state("FEAT-035", "same file", "FEATURE", 4, False, "low")
        directory = self._write_task(state)
        checkpoint_snapshot = {
            "branch": "feat/x", "head": "abc123", "working_tree": "dirty",
            "changed_files": ["src/a.py"], "untracked_files": [],
            "working_tree_fingerprint": "old",
        }
        aip.create_checkpoint(directory, state, agent="Codex", current_unit="Task 3", next_action="Continue", verification=[], git_snapshot=checkpoint_snapshot)
        current = {
            "branch": "feat/x", "head": "abc123", "working_tree": "dirty",
            "changed_files": ["src/a.py"], "untracked_files": [],
            "working_tree_fingerprint": "new",
        }
        report = aip.build_resume_report(directory, aip.load_json(directory / "state.json"), current, available_capabilities=None)
        self.assertEqual(report["uncheckpointed_changes"], [])
        self.assertTrue(report["working_tree_changed_since_checkpoint"])

    def test_resume_reports_missing_required_capabilities_without_mutating_state(self):
        state = aip.blank_state("FEAT-034", "deploy", "FEATURE", 5, False, "high", production_change=True)
        state["external_actions"]["allowed"].append({
            "plugin": "Cloudflare", "action": "deploy", "effect": "PRODUCTION_CHANGE",
            "target": "production", "purpose": "Deploy approved release",
        })
        directory = self._write_task(state)
        before = json.loads(json.dumps(state))
        current = {"branch": "feat/x", "head": "abc123", "working_tree": "clean", "changed_files": [], "untracked_files": []}
        report = aip.build_resume_report(directory, state, current, available_capabilities=["GitHub"])
        self.assertIn("Cloudflare", report["missing_capabilities"])
        self.assertEqual(aip.load_json(directory / "state.json"), before)


if __name__ == "__main__":
    unittest.main()
