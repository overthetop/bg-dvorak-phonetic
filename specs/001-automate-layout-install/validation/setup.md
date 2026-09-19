# Setup validation

Python 3.14.7 and uv 0.12.16 provisioned in isolated `/tmp/bg-dvorak-*` directories.
System Python remains 3.12.3; existing user uv remains 0.11.8.

- `uv lock`: passed; exact dependency resolutions recorded in uv.lock.
- `uv sync --locked --dev`: passed with project-local .venv.
- Offline/no-sync console `--help` and `--version`: passed.
- Ruff lint/format and strict mypy: passed for setup scaffolding.
- Stale metadata in a temporary copied project: `uv lock --check --offline` rejected it.

The initial scaffold intentionally refused installation; the final entry point now implements
installation, status, and recovery. The minimal uv_build backend is pinned to 0.12.16 in both
pyproject.toml and uv.lock. Final locked setup rebuilt the editable package successfully.
No keyboard configuration was modified. Lockfile is ready for review; no Git commit was made.

Final product launch uses `uv run --no-project --python .venv/bin/python
--no-python-downloads --offline`; missing-interpreter and stale-environment regression tests
verify no provisioning. The original --no-sync-only launch was corrected after an isolated
test demonstrated unwanted environment creation.
