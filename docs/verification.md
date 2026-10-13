# Verification and Evidence — Public Overview

Reliability claims require a clearly defined **scope**, reproducible evidence, and explicit limitations.

## Approach

- **Regression checks:** rerun defined tests to detect unexpected behavior changes.
- **Independent review:** obtain a separate assessment of designated artifacts or decisions.
- **Execution context:** distinguish the tested configuration from other machines, providers, or environments.
- **Fail-closed decisions:** when required evidence or authority is missing, a result should not be reported as fully qualified.
- **Traceability:** link a claim to its corresponding test report or review record where disclosure is permitted.

## How to read results

A useful public result should include:

| Field | Meaning |
| --- | --- |
| Scope | Exactly what component or behavior was tested |
| Environment | Relevant OS, runtime, and test conditions (safely generalized) |
| Outcome | Pass, fail, blocked, or inconclusive |
| Evidence | Redacted report, checksums, or reproducible demonstration |
| Limitations | What the result does **not** prove |

## Evidence status

A curated summary of selected historical results is available in [Engineering milestones](milestones.md). Original test logs, execution records, attestations, and internal review documents remain private. The summary distinguishes results supported by historical handoffs from bounded reviews checked against their original reports.

No global statement that NEXUS V3 is fully certified is made or implied.
