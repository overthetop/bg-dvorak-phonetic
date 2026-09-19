# Final local validation — native release evidence pending

Implementation is present, with **53 of 60 tasks checked**. Seven tasks remain open because
native macOS, hosted CI aggregation, and controlled desktop validation are unavailable here.
No Git commit or remote publication was made.

Base commit: `3c6cc98fff37fef39984a451ff284e18a8208895`. Tests ran against the uncommitted implementation worktree.
The source/test/tool/config/documentation fingerprint is `fe1c73f8cec814fe8b0f674437b53d1dffd6437c1a7494839712e443ed6d0ef0`;
individual file hashes are recorded in worktree-manifest.json.

## Observed results

- Environment: Ubuntu 24.04 x86_64; CPython 3.14.7; uv 0.12.16.
- Locked setup: passed with uv_build 0.12.16 and standard-library-only runtime dependencies.
- Ruff lint and formatting: passed. Strict mypy: passed for all 12 source modules.
- Python compileall: passed. actionlint 1.7.12: passed.
- pytest: **123 passed, 1 skipped**, in 6.54 seconds. The skip is native macOS installation.
- Local line coverage: **1074/1219 = 88.1050%**.
  Branch counts: 370/482 covered.
  Coverage includes every src production module and Python subprocesses, with no production
  exclusions. Tests and validation tools are outside the production-src denominator.
- Local coverage is informational: the required threshold was not applied to this single-OS
  report. The four-native-job aggregate and its strict >80% line gate remain pending.
- Native Linux fixtures use the actual extracted Ubuntu xkbcli compiler, including copies of
  real distro XKB data and explicitly seeded fresh/update/repair/noop scenarios.
- Missing environment, stale pin/dependency/version/lock, and foreign-cwd launch checks passed.
- Original linux/ and mac-os/ assets are unchanged; git diff --check passed.

## Commands

```sh
uv sync --locked --dev
uv run --locked ruff check src tests tools
uv run --locked ruff format --check src tests tools
uv run --locked mypy src
uv run --locked python -m compileall -q src tools
actionlint .github/workflows/tests.yml
uv run --locked coverage erase
uv run --locked coverage run --parallel-mode -m pytest --junitxml=test-results/pytest.xml
uv run --locked coverage combine
uv run --locked coverage report -m
uv run --locked coverage json -o coverage.json
uv run --locked python tools/measure_linux.py
```

The session's pinned uv/Python and extracted native validator were supplied from isolated
/tmp tooling directories; no system Python or live keyboard configuration was changed.
The corrected product command is `uv run --no-project --python .venv/bin/python
--no-python-downloads --offline bg-dvorak-phonetic`.

## Success criteria and outstanding evidence

| Criterion | Local evidence | Still required |
|---|---|---|
| SC-001 one invocation | Native Linux fresh/update/repair; portable workflow tests | Native macOS and desktop walkthroughs |
| SC-002 idempotency/preservation | Three-run stability, bounded transforms, unrelated bytes/modes | Native macOS repeat runs |
| SC-003 recoverable failures | Journals, rollback, external edits, symlinks, races, interrupted restoration | Native macOS confirmation |
| SC-004 CI results | Pinned workflow, actionlint, missing/failed/stale artifact tests | Four hosted native jobs and same-commit aggregate |
| SC-005 documentation/typing | Automated documentation commands | Controlled desktop discovery/selection/typing |
| SC-006 diagnostics | Ordered events, consistent IDs, classified exits, pending activation | Native desktop confirmation |
| SC-007 extension | Test-only third adapter through unchanged shared workflow | Same contract suite on native macOS |

Open tasks: T026, T036, T051, T056, T058, T059, T060. See us1.md–us5.md,
performance.md, review.md, and release.md. No hosted run URLs are available. Release readiness
and macOS compatibility are not claimed from portable tests.
