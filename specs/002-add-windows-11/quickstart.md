# Windows 11 Validation Quickstart

**Status**: Native mapping/build/validation tools and isolated tests are being implemented.
The Windows installer adapter and desktop acceptance remain pending. Do not run live installation
commands until the native asset proof and isolated tests pass. This guide is not pass evidence.

## Prerequisites and preparation

- Disposable or snapshotted Windows 11 25H2 Home/Pro x64 machine; repeat desktop acceptance on
  both editions. Record edition, build/revision, architecture, Secure Boot/policy context and snapshot.
- A standard user with access to administrator authorization, another working input source,
  native Windows PowerShell 5.1 or PowerShell 7, and a complete trusted project checkout/release.
- Obtain uv 0.12.16 from its [official release](https://github.com/astral-sh/uv/releases/tag/0.12.16).
  No Git Bash, WSL, MSKLC or global Python is assumed. Git is needed only if cloning rather than
  extracting a release archive. Product commands use native x64 Python, not an emulated process.
- End-user release includes matching prebuilt Windows assets. Maintainers additionally install
  the selected VS 2022 17.14 C++ tools and matching SDK/WDK 26100.6584 following the
  [official kit archive](https://learn.microsoft.com/en-us/windows-hardware/drivers/other-wdk-downloads).
  The committed toolchain lock records exact compiler and package versions. Build tools run unelevated.

In PowerShell, enter a checkout path containing spaces and Bulgarian characters:

```powershell
Set-Location 'C:\work\Българска клавиатура\bg-dvorak-phonetic'
uv python install 3.14.7
uv sync --locked --dev
uv run --locked python -c "import platform, struct; print(platform.python_version(), platform.machine(), struct.calcsize('P') * 8)"
```

Expected runtime: Python 3.14.7, native AMD64, 64-bit pointers. Setup is the only dependency
provisioning step. Never run uv setup elevated. Release acquisition and dependency setup may use
the network; product commands below must work offline after preparation.

For maintainers, after explicit kit acquisition and extraction as in the prerequisite workflow:

```powershell
$vs = 'C:\Program Files\Microsoft Visual Studio\2022\Enterprise'
$compiler = Join-Path $vs 'VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64'
$msbuild = Join-Path $vs 'MSBuild\Current\Bin\MSBuild.exe'
# This directory contains the locked .zip packages and their package-ID extraction folders.
$kits = 'C:\work\bg-dvorak-kits'
uv run --locked python tools/build_windows_layout.py --compiler-root $compiler --msbuild $msbuild --kits $kits
uv run --locked python tools/validate_windows_layout.py --assets windows/assets
```

The builder verifies the explicitly supplied toolchain paths against the input lock, generates
tables from the reviewed mapping,
and produces DLL/manifest output. It fails on missing/mismatched tools, never installs them.
The validator checks hashes, PE metadata, mapping/source provenance and exported ABI metadata;
it does not register, activate, or claim desktop typing. The first native proof uses these assets
in a snapshotted disposable VM through a controlled manual test registration, before implementing
the product adapter (T011). Record the exact commands, native system directory and project registry
values, check the candidate identities for collisions, and capture the original file/registry state
before copying the verified DLL and creating only the test-owned registration. Manually select the
layout and run the required typing probes. Select another working layout afterward, remove only
verified test-created resources, restore the captured state, and verify restoration; retain the VM
snapshot as a fallback. Record the procedure and results in `validation/native-proof.md`.
This test procedure is not an end-user installation workflow. Dependent installer work waits for
its pass; a failed ABI, mapping or security-policy check requires a measured design correction,
not a protection bypass. Later acceptance scenarios below use the completed product adapter.

## Static and isolated native tests

```powershell
uv run --locked ruff check src tests tools
uv run --locked ruff format --check src tests tools
uv run --locked mypy src tools
uv run --locked python -m compileall -q src tools
uv run --locked coverage run --parallel-mode -m pytest --junitxml=test-results/pytest.xml
uv run --locked coverage combine
uv run --locked coverage report -m
uv run --locked coverage json -o coverage.json
```

The type-check command deliberately includes `tools` as well as `src`; the new build/validation
helpers must pass it locally and in CI without blanket exclusions.

All scenarios below must have automated fixtures. Native Windows tests use real temporary file
operations and test-owned registry keys, with injected roots and fault boundaries; no developer
keyboard settings. Include fresh/current/outdated/damaged/duplicate/conflicting states, loaded-file
failure, every write/flush/registration failure, uncertain crash steps, external edits, concurrency,
ACL/reparse attacks, denied authorization and worker transport loss. Validate v1 recovery compatibility
and Unix adapter contracts after the shared backend refactor. OS-specific integration tests run on
their applicable OS; portable workflow tests run on all platforms. A Windows runner must not skip
all Windows native tests and still count as passing.

The local coverage report is informational. CI must combine all five same-revision artifacts,
including the new Windows job, through the updated collector and require exact line coverage >80%.
Retain branch/missing-line reports and do not hide unexecuted production modules. For a clean run,
remove only prior local coverage output using the documented coverage erase command first.

## Controlled desktop acceptance

Record the project and asset revision and capture stdout/stderr for each command. Snapshot layout
registrations, project files, installed languages, default/active input and unrelated layout fixtures
before starting. Use a VM snapshot as the final restoration fallback, not as evidence that product
recovery succeeded. Observe the [CLI contract](contracts/cli.md) and
[resource rules](contracts/windows-platform.md).

### A. Inspect and preview (FR-005/006/008, SC-004)

```powershell
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic status
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic install --scope system --dry-run
```

Expect absent/current/repairable/etc. to match the fixture and the preview to list file plus registry
changes. Compare snapshots: no persistent installation/state changes, even when protected read
inspection requests UAC. Deny authorization and expect exit 3 with incomplete inspection. Omit
scope from install or select user scope and expect exit 2 without changes.

### B. Fresh install and typing (FR-001–007/012, SC-001/002)

```powershell
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic install --scope system
```

Accept the displayed plan and necessary UAC. Expect installed/current and activation pending,
with a recovery UUID/location. Unrelated layouts and default/active input remain unchanged.
Follow Settings activation from the CLI contract, select with Win+Space, and type every reviewed
case from `windows/mapping.json` in a native text editor and browser field. Include lowercase,
Shift, Caps, Shift+Caps, AltGr, Shift+AltGr, dead-key sequences, punctuation, keypad, and Ctrl shortcuts.
Run the 32-bit text-input probe built with the locked tools. Save evidence before manually signing
out/in; repeat discovery/selection/typing after sign-in. A failed 32-bit probe blocks the asset design.

### C. Repetition, update, repair, and conflicts (FR-009/010, SC-001/003)

Run the install command three more times. Expect unchanged and zero rewritten assets, duplicate
registrations or new journals/backups. For update, prepare a second trusted checkout with a newer
validation asset revision using the same mapping/identity, install the older validation revision
first, then run the newer checkout's same install command. Retain both manifests for rollback.
Expect one effective registration pointing to the new immutable file and retained previous assets.
Repeat with the old layout loaded in an editor and verify pending-refresh guidance.

In the snapshotted VM, remove a project registration value or project DLL, one fixture at a time,
then rerun install. Expect bounded repair when ownership survives. Seed a known project duplicate
and expect convergence. Seed an unrelated identity collision or unknown same-name registration;
expect refusal (4), with the unrelated data unchanged. Fixture creation uses internal test utilities
and controlled VM preparation, not a public force/root option. Isolated tests must automate these cases.

### D. Recovery and fault cases (FR-011, SC-004)

Use the UUID reported by a completed or intentionally interrupted controlled test transaction:

```powershell
$recoveryId = 'replace-with-reported-run-uuid'
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic recover $recoveryId --scope system --dry-run
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic recover $recoveryId --scope system
```

Expect preview to change nothing. Actual recovery restores verified registration/files and preserves
unrelated settings; repeated recovery is safe. Before restoring a fresh install, manually select
another working layout and remove the project source from your user keyboard list if necessary;
product recovery does not manage user selection. A loaded file that cannot be safely removed yields
5 and retains recovery state; follow reported sign-out/retry guidance, never force-delete journals.

Use isolated crash-injection tests to stop after every mutation before its completion marker.
Supplement with controlled VM interruption/worker-parent termination cases. Expect either proven
restoration or exit 5 with usable originals and instructions, never false success. Externally edit a
resource after interruption and expect conflict refusal with both versions preserved. Two concurrent
mutations must not interleave. Record successful retry after resolving the fixture condition.

### E. Paths, offline operation, and documentation (FR-013, SC-005)

Repeat status, preview, install/no-op and recovery from a different working directory using a quoted
absolute interpreter path. Verify spaces/Cyrillic paths, offline product execution, standard-user
UAC with a different administrator account, denied consent, and noninteractive `--yes` behavior.
Activation must apply only through the original user's manual Settings steps. Follow the walkthrough
without reading source; any undocumented prerequisite or step is a documentation failure.

## CI and release evidence (FR-014/015, SC-006)

Add `windows-2025` alongside `ubuntu-24.04`, `macos-15-intel`, `macos-15`, and `macos-26`.
Use native PowerShell for Windows, preserve command failures explicitly, record compiler/kit and
runner provenance, and upload hidden coverage files/test results even on failure. Keep current
read-only permissions, pinned action revisions, and no secrets for pull requests. Update the
coverage collector's required matrix and its missing/stale/failed-artifact tests together.

Hosted Windows Server validates native APIs/builds, not supported product detection or the Windows
11 desktop. Exercise product detection using fixtures plus actual Home and Pro desktops; do not
add a user-facing Server bypass. Desktop evidence can be controlled manual validation; do not run
untrusted PR code on a persistent privileged desktop runner.

Record each scenario with environment, exact commands, exit codes, before/after resource snapshots,
asset revision, diagnostics, typing evidence and final restoration outcome. Mark every case passed,
failed or pending. Missing Windows, Linux or macOS evidence remains a release blocker; planning or
passing coverage does not close it. Restore the VM snapshot after verification and retain records.

## Final candidate validation

The initial T059–T061 evidence is a baseline, not final approval if T062–T064 change code,
assets, runtime pins or documented workflows. T065 freezes the final candidate and reruns all
five native CI jobs plus the complete Home/Pro/Ubuntu/macOS desktop acceptance procedures on
that candidate. Replace stale evidence and record the immutable source revision, asset manifest
and runtime/lock hashes. If a substantive correction is needed, freeze the corrected candidate
and repeat the final validation cycle. Evidence-only record additions identify the tested
candidate and do not claim that subsequent implementation changes were tested.
