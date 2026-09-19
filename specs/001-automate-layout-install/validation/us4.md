# CI and coverage validation

Passed locally: actionlint v1.7.12 validates .github/workflows/tests.yml; coverage checker tests
reject malformed/missing/empty counts, zero statements, below/exactly 80%, and misleading rounded
or branch percentages. Artifact collector tests reject missing jobs/data, failed jobs, and stale
commit metadata before copying any aggregation input. The third test adapter exercises shared
install/update/repair/noop policy without modifying either native adapter.

Official Action tags resolved to the immutable SHAs used in the workflow. The workflow uses
read-only permissions, no PR secrets, pinned uv/Python, locked setup, all four native labels,
separate results, and hidden coverage artifacts with same-commit metadata. Python subprocess
instrumentation includes the internal worker refusal subprocess.

Commands: `actionlint .github/workflows/tests.yml`; `uv run --locked pytest
 tests/unit/test_coverage_gate.py tests/unit/test_coverage_artifacts.py
 tests/unit/test_validation_record.py tests/contract/test_extensibility.py`.

Hosted runs were not launched. No run URLs or complete same-commit native aggregate are available.
Controlled failure/missing-artifact behavior passed local tests; hosted exercises remain pending.
T051 remains open. Local coverage is informative and does not replace the required aggregate gate.
