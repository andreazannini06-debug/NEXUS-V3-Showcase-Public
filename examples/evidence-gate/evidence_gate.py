"""Standalone, synthetic demonstration of fail-closed evidence integrity checks.

Not extracted from NEXUS V3. This cannot authenticate an execution or an actor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HEX_DIGEST = re.compile(r"^[a-fA-F0-9]{64}$")
MAX_ARTIFACT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class Decision:
    status: str
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "findings": list(self.findings)}


def _keys(obj: Any, expected: set[str], name: str, findings: list[str]) -> bool:
    if type(obj) is not dict:
        findings.append(f"{name}: expected an object")
        return False
    unknown = obj.keys() - expected
    missing = expected - obj.keys()
    if unknown:
        findings.append(f"{name}: unexpected fields: {', '.join(sorted(unknown))}")
    if missing:
        findings.append(f"{name}: missing fields: {', '.join(sorted(missing))}")
    return not unknown and not missing


def _nonempty(value: Any) -> bool:
    return type(value) is str and bool(value.strip()) and value == value.strip()


def _valid_filename(value: Any) -> bool:
    return _nonempty(value) and bool(FILE_NAME.fullmatch(value)) and value not in {".", ".."} and ".." not in value


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate(policy: Any, report: Any, artifacts: Path) -> Decision:
    """Check consistency of *reported* results and the bytes of local evidence.

    No process execution, identity authentication, provenance or signature validation.
    Any missing, malformed, contradictory or unverifiable input is BLOCKED.
    """
    issues: list[str] = []
    if not _keys(policy, {"repository", "allowed_actors", "required_checks"}, "policy", issues):
        return Decision("BLOCKED", tuple(issues))
    if not _keys(report, {"repository", "actor", "task_id", "execution_state", "checks"}, "report", issues):
        return Decision("BLOCKED", tuple(issues))

    if not _nonempty(policy["repository"]):
        issues.append("policy: repository must be non-empty")
    actors = policy["allowed_actors"]
    if (type(actors) is not list or not actors or
            any(not _nonempty(a) for a in actors) or len(set(actors)) != len(actors)):
        issues.append("policy: allowed_actors must be a non-empty unique string list")
        actors = []
    required = policy["required_checks"]
    if (type(required) is not list or not required or
            any(not _nonempty(c) for c in required) or len(set(required)) != len(required)):
        issues.append("policy: required_checks must be a non-empty unique string list")
        required = []

    for field in ("repository", "actor", "task_id"):
        if not _nonempty(report[field]):
            issues.append(f"report: {field} must be non-empty")
    if report["repository"] != policy["repository"]:
        issues.append("repository context mismatch")
    if report["actor"] not in actors:
        issues.append("reporting actor is not on the allowed list")
    if report["execution_state"] != "completed":
        issues.append("execution state is not completed")

    checks = report["checks"]
    if type(checks) is not list:
        issues.append("report: checks must be an array")
        return Decision("BLOCKED", tuple(issues))

    seen_names: set[str] = set()
    seen_files: set[str] = set()
    root = Path(artifacts)
    if not root.is_dir() or root.is_symlink():
        issues.append("artifact directory missing or is a symlink")
        return Decision("BLOCKED", tuple(issues))

    for position, check in enumerate(checks):
        prefix = f"checks[{position}]"
        if not _keys(check, {"name", "status", "artifact", "sha256"}, prefix, issues):
            continue
        name, status, filename, reported_hash = (
            check["name"], check["status"], check["artifact"], check["sha256"]
        )
        if not _nonempty(name):
            issues.append(f"{prefix}: invalid name")
        elif name in seen_names:
            issues.append(f"{prefix}: duplicate check name")
        else:
            seen_names.add(name)
            if name not in required:
                issues.append(f"{prefix}: check not required by policy")
        if status != "passed":
            issues.append(f"{prefix}: check did not pass")
        if not _valid_filename(filename):
            issues.append(f"{prefix}: unsafe artifact name")
            continue
        if filename in seen_files:
            issues.append(f"{prefix}: duplicate artifact")
        seen_files.add(filename)
        if type(reported_hash) is not str or not HEX_DIGEST.fullmatch(reported_hash):
            issues.append(f"{prefix}: malformed SHA-256")
            continue
        candidate = root / filename
        if candidate.is_symlink() or not candidate.is_file():
            issues.append(f"{prefix}: artifact missing or symlinked")
            continue
        try:
            if candidate.stat().st_size > MAX_ARTIFACT_BYTES:
                issues.append(f"{prefix}: artifact exceeds demo size limit")
            elif _digest_file(candidate) != reported_hash.lower():
                issues.append(f"{prefix}: artifact digest mismatch")
        except OSError:
            issues.append(f"{prefix}: artifact could not be read")

    for name in required:
        if name not in seen_names:
            issues.append(f"required check missing: {name}")
    return Decision("BLOCKED" if issues else "CONSISTENT_INPUT", tuple(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "BLOCKED", "findings": [f"input error: {type(error).__name__}"]}))
        return 2
    outcome = evaluate(policy, report, args.artifacts)
    print(json.dumps(outcome.as_dict(), indent=2))
    return 0 if outcome.status == "CONSISTENT_INPUT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
