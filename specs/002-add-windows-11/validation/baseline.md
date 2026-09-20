# Unmodified baseline — T001

Recorded 2026-09-19. Status: passed for available local checks; native release evidence pending.
Branch: `automate`. Source commit: `733d5c58e027514d75b15051a68696359df24115`.
The feature design directory was untracked; production code, tests, tools, configuration and
Linux/macOS assets were unchanged when these checks ran.

## Environment and setup

Ubuntu 24.04.5 LTS, Linux 6.8.0-139-generic, x86_64. Default uv was 0.11.8 and the existing
virtual environment referenced a removed temporary interpreter. Restored isolated uv 0.12.16
and CPython 3.14.7 under `/tmp`, then ran `uv sync --locked` successfully. No pins changed.
Runtime dependencies remain standard-library-only. System Python remains 3.12.3.

Isolated uv archive: `https://github.com/astral-sh/uv/releases/download/0.12.16/uv-x86_64-unknown-linux-gnu.tar.gz`.
The native Linux compiler came from Ubuntu noble package `libxkbcommon-tools 1.6.0-1build1`,
downloaded with `apt-get download libxkbcommon-tools` and extracted with `dpkg-deb -x`.
Package SHA-256: `b4e4967e04d2211149fcdd0cbf1de8326932a68ba3220a39e6b331055978186d`.
Its dispatcher has a fixed `/usr/libexec/xkbcommon` lookup. Two initial runs therefore reported
121 passed, 2 failed, 1 skipped (`compile-keymap` unavailable). A temporary shell launcher
accepting only `compile-keymap` and executing the extracted, unmodified
`xkbcli-compile-keymap` fixed the environment. No live keyboard files or installed packages changed.
The final run uses real distro data from `/usr/share/X11/xkb`.

## Commands and results

Working directory was the repository root. PATH prepended
`/tmp/bg-dvorak-windows-setup/bin` (the launcher) and
`/tmp/bg-dvorak-windows-setup/uv-x86_64-unknown-linux-gnu`.

| Command | Result |
|---|---|
| `uv sync --locked` | Passed, 15 packages installed |
| `uv run --locked ruff check src tests tools` | Passed |
| `uv run --locked ruff format --check src tests tools` | Passed, 39 files |
| `uv run --locked mypy src` | Passed, 12 source files |
| `uv run --locked python -m compileall -q src tools` | Passed |
| `uv run --locked coverage erase` | Passed, cleared failed-run data |
| `uv run --locked coverage run --parallel-mode -m pytest --junitxml=test-results/windows-baseline.xml` | 123 passed, 1 skipped, 6.39 seconds |
| `uv run --locked coverage combine` | Passed |
| `uv run --locked coverage json -o /tmp/bg-dvorak-windows-setup/baseline-coverage.json` | Passed |

The skip is native macOS installation. Local source line coverage is 1074/1219 (88.1050%);
branch coverage is 370/482. This is the existing baseline denominator, not the planned
source-plus-tools, five-platform release aggregate. JUnit and raw coverage are local ignored
artifacts; the numerical results above are recorded evidence, not hosted CI results.

## Inventory and inherited blockers

- `src/bg_dvorak_phonetic/`: shared CLI, workflow, models, diagnostics, privileged boundary,
  transaction engine and Linux/macOS adapters. Registry resources and Windows adapter do not exist.
- `workflow.py` inventories both `linux/` and `mac-os/`; the Windows seam must preserve existing
  assets on non-Windows hosts. Transaction assumptions include POSIX ownership, modes, locking
  and directory durability, requiring the planned backend abstraction.
- `linux/symbols-bg-dv` is the Windows mapping authority; `mac-os/` differs on some layers.
- 124 collected unit/contract/integration cases; Linux native cases use temporary destinations.
  Portable macOS tests do not establish native macOS compatibility.
- CI currently declares Ubuntu and three macOS jobs. Windows assets/build tooling are absent.
- No accessible Windows 11 Home/Pro desktop, Windows SDK/WDK, MSVC, MSBuild or PowerShell was
  found in this session. No native macOS host or hosted CI run was available. Linux desktop
  typing was not exercised by this baseline.
- Prior feature tasks T026, T036, T051, T056, T058, T059 and T060 remain open for native macOS,
  hosted aggregation and controlled desktop evidence. See
  [prior final validation](../../001-automate-layout-install/validation/final.md).

Unchanged input SHA-256 values:

| Input | SHA-256 |
|---|---|
| `pyproject.toml` | `91d3d128c9c8cb8e860d996675e0efb94c5e31473b3b215e1e9a1b6e31af394b` |
| `uv.lock` | `cfe227b9a58d364c5f153b247820049dd9c454d4546873d179388d67d8ef3cd5` |
| `linux/symbols-bg-dv` | `9a36eb692d95ee9dd7a499f6559bb39a17fc61cc7e78b7d0f411cdb317a38739` |
