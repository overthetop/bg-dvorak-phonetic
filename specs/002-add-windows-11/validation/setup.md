# Setup continuation — T003

Date: 2026-09-19. Base commit: 733d5c58e027514d75b15051a68696359df24115, modified worktree.
Environment: Ubuntu 24.04.5 x86_64, Python 3.14.7, uv 0.12.16, isolated XKB launcher
as recorded in baseline.md. This is local scaffolding validation, not release evidence.

Added tests/fixtures/windows_resources.py and tests/unit/test_windows_resources.py.
First run failed collection because the fixture module did not exist. After implementation,
portable checks cover snapshot/restore of existing and absent files, temporary-root cleanup,
path containment, symlink/hardlink refusal, fault injection and non-Windows registry refusal.
A Windows-only test checks real REG_SZ/REG_BINARY snapshots, missing versus empty values,
restoration after edits and deletion of the owned HKCU key. It remains skipped here.
Windows hosts without symlink privilege explicitly skip the symlink case.

The fixture creates no live keyboard registration and exposes no product CLI override.
Registry snapshots cover values, not child trees or ACLs; production resource validation
belongs to the later native backend tasks. Native registry results remain pending.

Validation commands from the repository root:

- `uv run --locked ruff check src tests tools`: passed.
- `uv run --locked ruff format --check src tests tools`: passed, 41 files.
- `uv run --locked mypy src`: passed, 12 production source files.
- `uv run --locked pytest -q`: 135 passed, 2 skipped in 8.35 seconds.
  Skips: native macOS install and native Windows registry fixture.
- `git diff --check`: passed.

T003 implementation is complete; native fixture execution is pending. T002 still lacks actual
Windows compiler/package acquisition and hashes. T005 and later dependencies remain blocked.
No pre/post implementation extension hooks are configured.
