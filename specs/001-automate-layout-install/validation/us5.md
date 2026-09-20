# Documentation validation

Passed locally: prepared help/version, status, preview, and install through injected temporary
adapters; explicit interpreter invocation from a foreign working directory; missing prepared
environment refusal without creating files; changed Python pin, changed runtime dependencies,
changed project version, and missing lockfile refusal without environment modification.

Command: `uv run --locked pytest tests/integration/test_documented_commands.py tests/unit/test_assets.py`.

The originally planned `uv run --no-sync` created a missing .venv in an isolated test. Commands
were corrected to `uv run --no-project --python .venv/bin/python --no-python-downloads --offline`.
From a different directory use the absolute prepared interpreter path. The corrected invocation
was tested against both existing and missing environments.

README and guides now distinguish installation from activation, explain authorization for protected
read-only inspection, identify backups/recovery and safe cleanup, and separate local coverage from
native aggregation. Clean/existing-install desktop walkthroughs on Linux/macOS remain pending;
T056 remains open. No native macOS or actual typing result is claimed.
