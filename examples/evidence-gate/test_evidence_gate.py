"""Deterministic stdlib tests for a public standalone demonstration."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evidence_gate import evaluate


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = {
            "repository": "example/synthetic-repo",
            "allowed_actors": ["demo-agent"],
            "required_checks": ["unit-tests", "style-check"],
        }
        self.report = {
            "repository": "example/synthetic-repo",
            "actor": "demo-agent",
            "task_id": "DEMO-1",
            "execution_state": "completed",
            "checks": [],
        }
        for name in ("unit-tests", "style-check"):
            filename = f"{name}.txt"
            data = f"synthetic fixture for {name}\n".encode()
            (self.root / filename).write_bytes(data)
            self.report["checks"].append({
                "name": name, "status": "passed", "artifact": filename,
                "sha256": hashlib.sha256(data).hexdigest(),
            })

    def decision(self):
        return evaluate(self.policy, self.report, self.root)

    def blocked(self):
        self.assertEqual(self.decision().status, "BLOCKED")

    def test_consistent_input(self):
        self.assertEqual(self.decision().status, "CONSISTENT_INPUT")
        self.assertEqual(self.decision().findings, ())

    def test_missing_check(self):
        self.report["checks"].pop()
        self.blocked()

    def test_failed_check(self):
        self.report["checks"][0]["status"] = "failed"
        self.blocked()

    def test_skipped_check(self):
        self.report["checks"][0]["status"] = "skipped"
        self.blocked()

    def test_wrong_repository(self):
        self.report["repository"] = "other/repo"
        self.blocked()

    def test_wrong_actor(self):
        self.report["actor"] = "other-agent"
        self.blocked()

    def test_no_execution(self):
        self.report["execution_state"] = "pending"
        self.blocked()

    def test_duplicate_check(self):
        self.report["checks"].append(dict(self.report["checks"][0]))
        self.blocked()

    def test_unexpected_check(self):
        extra = dict(self.report["checks"][0], name="not-in-policy")
        self.report["checks"].append(extra)
        self.blocked()

    def test_tampered_artifact(self):
        (self.root / "unit-tests.txt").write_text("tampered", encoding="utf-8")
        self.blocked()

    def test_missing_artifact(self):
        (self.root / "style-check.txt").unlink()
        self.blocked()

    def test_path_traversal(self):
        self.report["checks"][0]["artifact"] = "../secret.txt"
        self.blocked()

    def test_duplicate_artifact(self):
        self.report["checks"][1]["artifact"] = "unit-tests.txt"
        self.blocked()

    def test_invalid_hash(self):
        self.report["checks"][0]["sha256"] = "definitely-not-a-digest"
        self.blocked()

    def test_report_unknown_field(self):
        self.report["trust_me"] = True
        self.blocked()

    def test_missing_policy_field(self):
        del self.policy["required_checks"]
        self.blocked()

    def test_duplicate_policy_check(self):
        self.policy["required_checks"].append("unit-tests")
        self.blocked()

    def test_non_string_check_name(self):
        self.report["checks"][0]["name"] = None
        self.blocked()

    def test_empty_task_id(self):
        self.report["task_id"] = ""
        self.blocked()

    def test_artifact_size_limit(self):
        (self.root / "unit-tests.txt").write_bytes(b"0" * (1024 * 1024 + 1))
        self.blocked()

    def test_symlink_artifact(self):
        target = self.root / "style-check.txt"
        link = self.root / "unit-tests.txt"
        link.unlink()
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        self.blocked()


if __name__ == "__main__":
    unittest.main()
