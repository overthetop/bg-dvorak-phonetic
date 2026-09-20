# Development

Install uv 0.12.16, then explicitly prepare the checkout:

```sh
uv python install 3.14.7
uv sync --locked --dev
uv run --locked ruff check src tests tools
uv run --locked ruff format --check src tests tools
uv run --locked mypy src
uv run --locked python -m compileall -q src tools
uv run --locked pytest
```

Ubuntu tests require `xkb-data` and `libxkbcommon-tools`; native macOS tests require `plutil`.
Tests write only to temporary destinations. Missing validators fail native tests on their OS;
foreign-OS native tests are explicitly skipped. Portable mocked native calls establish shared
behavior only, not macOS compatibility. Install/update/repair commands use the README's
`--no-project --python .venv/bin/python --no-python-downloads --offline` flags after preparation. Do not elevate uv.

The standard-library runtime is import-safe, uses a src package, and exposes console and module
entry points to the same CLI. Dependency changes require a reviewed `uv lock`, locked setup,
and the complete suite. `uv sync --locked` rejects stale metadata.

## Coverage and CI

```sh
uv run --locked coverage erase
uv run --locked coverage run --parallel-mode -m pytest
uv run --locked coverage combine
uv run --locked coverage report -m
uv run --locked coverage json -o coverage.json
```

This local report is informational. It includes every production module, unimported code,
branches, and instrumented Python subprocesses. There are no production coverage exclusions.
Coverage's displayed combined percentage includes branches; the required gate compares exact
line counts separately.

CI runs locked lint/format/types/tests on `ubuntu-24.04`, `macos-15-intel`, `macos-15`, and
`macos-26`. Every native job must pass. Artifacts include the commit, runner, runtime, result,
raw hidden coverage files, and test logs. Aggregation rejects missing/failed/stale artifacts,
combines all four inputs, and requires `covered_lines * 100 > num_statements * 80` with a
positive denominator. Exactly 80% fails. `tools/check_coverage.py` is used only after the
complete same-commit native aggregate has been validated by `tools/collect_coverage.py`.
The CI action SHAs are pinned; repository permissions are read-only and PR jobs use no secrets.
Hosted execution and manual desktops remain separate evidence requirements.

## Extend the platform interface

Implement the nine operations in
[the adapter contract](../specs/001-automate-layout-install/contracts/platform-adapter.md): probe,
validate assets, inspect, plan, validate staged content, acquire a lock, apply authorized work,
verify installed content, and provide activation guidance. Supply `recovery_access` for native journal access and restoration authorization.
Register the adapter statically in
`platforms/__init__.py`; load native dependencies only when selected. Add its authoritative
assets, identity rules, supported scopes, tests, documentation, and native CI job.

Inspection/planning must not write installation or recovery state. Plans contain bounded data
operations, not commands. Shared workflow owns action selection, consent, diagnostics, and recovery;
all changes must preserve the common error and rollback contracts. A new OS can inject its native
transaction/locking implementation through the adapter boundary. The test-only fake adapter proves
common workflow extension and provides no Windows installation support.

See [release validation](release-validation.md) before declaring compatibility or publishing.

For native Ubuntu fixture timings and diagnostic transcripts, run
`uv run --locked python tools/measure_linux.py`. It reads distro XKB inputs, seeds explicit
fresh/update/repair states in temporary copies, runs the native validator, and refreshes
`validation/performance.md` and `validation/us3.md`. It never writes live keyboard paths.

## Windows native build prerequisites

Native input acquisition is locked in `windows/toolchain.lock.json`: VS 2022 17.14.37628.2,
MSVC 19.44.35228.0 (toolset directory 14.44.35207), linker 14.44.35228.0, MSBuild 17.14.51.32402,
and Microsoft SDK CPP, SDK CPP x64 and WDK x64 NuGet packages 10.0.26100.6584. Package URLs,
SHA-256 values and native tool hashes are recorded. All 72 files alongside the selected
Hostx64/x64 compiler were hashed. Upstream sample revision/license is in `windows/layout/NOTICE.md`.

GitHub Actions run 35468187758 captured these tools on `windows-11-arm` image 20260914.169.1;
the selected compiler targets x64 using Windows x64 emulation. ARM64 product support is not
implied. Acquisition occurs only in the explicit maintainer prerequisite workflow. Future
builds must verify the input lock and fail on mismatch rather than accepting runner updates.
Product install/status/recover must never provision build tools or compile assets.

The input lock being ready does not mean a layout was built or proved. The native proof still
requires Windows 11 25H2 Home/Pro x64 desktop acceptance under normal security settings; follow
the [validation protocol](../specs/002-add-windows-11/validation/README.md) and
[quickstart](../specs/002-add-windows-11/quickstart.md). Hosted ARM64 Enterprise and x64 Server
provide separate native API/build evidence.

### Hosted Windows prerequisite checks

`.github/workflows/windows-prerequisites.yml` runs the isolated resource fixture tests on
`windows-2025` (x64 Server) and `windows-11-arm` (Windows 11 ARM64), with locked Python/uv.
It records actual OS/build/architecture, installed Visual Studio/SDK inventory and available
compiler/header hashes as downloadable artifacts. Missing tools remain missing; inventory
collection alone does not establish a usable lock; run 35468187758 additionally acquired and
verified the exact pinned packages and tools.

The initial run uses the dedicated `windows-prerequisites-ci` branch. The workflow also supports
manual dispatch once available on the default branch. This early prerequisite check is separate
from the later five-job release coverage matrix. The ARM64 run tests resource scaffolding;
it does not expand the product's x64 support scope or replace Home/Pro desktop acceptance.
