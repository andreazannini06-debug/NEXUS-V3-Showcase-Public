# Evidence Gate — standalone public demonstration

This is an **original, self-contained educational demo**, written for the NEXUS V3 Showcase. It is **not extracted from NEXUS V3**, is not an implementation of NEXUS V3's internal controls, and does not validate the private project's milestones.

## Problem

A reported agent execution can look successful even when required checks are missing, its repository context is wrong, or its referenced evidence has changed. This demo uses deterministic, fail-closed rules to check the **internal consistency of a synthetic report** and match recorded SHA-256 digests to local artifact bytes.

## Run (Python 3.10+, no third-party dependencies)

From this folder:

```bash
python evidence_gate.py --policy policy.json --report report.json --artifacts artifacts
python -m unittest discover -v -p 'test_*.py'
```

On a consistent sample, the command prints `"status": "CONSISTENT_INPUT"` (exit code 0). If a required check fails, evidence is missing or altered, or inputs conflict, it prints `"status": "BLOCKED"` (exit code 1). Malformed/unreadable input files cause a blocked result (exit code 2).

Try changing a byte in `artifacts/unit-tests.txt` and rerun the first command: it must reject the report with an artifact digest mismatch. Restore the sample before running again.

## Checks performed

- Exact repository context and an actor string from the configured allowlist
- Completed execution state as *reported in the input* (not independently observed)
- Presence and success claims for every mandatory check
- No duplicate or unexpected check names, no duplicate evidence filenames
- SHA-256 equality between each referenced artifact and its recorded digest
- Strict shape validation and rejection of unsafe artifact filenames, symlinks, missing files and oversized inputs

## Explicit limitations

All example identities and execution results are **synthetic**. SHA-256 matching establishes only that the supplied bytes match the supplied digest; an attacker controlling both can forge a mutually consistent report. Allowlisted actor strings are **not identity authentication**. The demo does not execute tasks, authenticate an owner, verify independent reviewer identity, validate signatures, or establish software safety, provenance or production readiness.

`CONSISTENT_INPUT` means **local input consistency**, not verified execution or approval. No property of the private NEXUS V3 system is proved by this separate example.

## Layout

- `evidence_gate.py`: deterministic gate + CLI
- `test_evidence_gate.py`: Python standard-library test suite
- `policy.json`, `report.json`: entirely synthetic example inputs
- `artifacts/`: entirely synthetic fixture bytes

See the root showcase README for the conceptual design and separately documented historical milestones of NEXUS V3.
