# Quickstart Validation Guide

This is the validation guide for the planned implementation. Commands become runnable after
implementation; this planning pass has not installed anything or run the future test suite.
Use contracts/cli.md for command meanings and data-model.md for state/recovery details.

## Prerequisites

Use Ubuntu Desktop 24.04 LTS x86_64, macOS 15 Intel/Apple Silicon, or macOS 26 Apple Silicon.
Install uv 0.12.16 following the linked official release instructions in research.md.
Clone the repository and enter its root. Python is provisioned explicitly during setup;
layout installation itself must not download or upgrade Python.

Ubuntu also requires xkb-data and libxkbcommon-tools (provides xkbcli). Install those packages
through the system package manager before running the installer. macOS requires its native
plutil tool. For actual desktop validation, use a disposable VM/account or a controlled machine
with recorded pre-install settings and recovery access.

## Prepare the environment

```sh
uv python install 3.14.7
uv sync --locked --dev
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic --help
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic --version
```

Expected: Python matches .python-version; uv.lock is accepted unchanged. Product launches use
--no-project --python .venv/bin/python --no-python-downloads --offline and cannot
provision or update the environment.
Read-only preflight must check the prepared environment, interpreter pin and runtime dependencies;
--no-project alone does not check freshness. Missing/stale prerequisites must fail without changing
the environment or using a global fallback. Repeat the explicit preparation commands after an
intentional runtime/dependency update. Help/version must not touch keyboard configuration.

## Run automated checks safely

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src
uv run --locked coverage erase
uv run --locked coverage run --parallel-mode -m pytest
uv run --locked coverage combine
uv run --locked coverage report -m
uv run --locked coverage json -o coverage.json
```

Tests configure whole-source measurement, branch collection, relative filenames and subprocess
coverage. They use temporary roots and must never edit live system layouts. A single platform's
coverage report is informative: the local sequence does not call the threshold checker. The
required final gate uses all required same-commit native jobs combined.
The checker rejects zero statements and line coverage at or below 80%; native tests must pass
separately even when combined coverage exceeds the threshold.

Run focused suites with:
```sh
uv run --locked pytest tests/unit tests/contract
uv run --locked pytest tests/integration
```

Expected fixtures cover fresh, legacy, outdated, missing/duplicate/damaged project components,
malformed unrelated configuration, concurrent writes, denied privileges, partial apply/restore
failure, unsupported environments, foreign working directory, and paths containing spaces/Cyrillic.
Critical native tests cannot silently skip on their supported OS.

## Fresh desktop installation

On macOS:
```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --dry-run
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install
```

On Ubuntu:
```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --scope system --dry-run
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --scope system
```

Expected: preview changes no installation/state files; actual run logs stages, requests required
authorization, validates final state, and reports installed plus activation pending.
The Linux privilege prompt authorizes protected-journal inspection or scoped apply, never
package-manager execution. A preview may read protected journals after authorization but cannot
change installation/recovery state or create locks, backups or journals.

Follow Input Sources guidance shown by the installer. On Ubuntu select Bulgarian's Dvorak
phonetic variant, retaining layout identity bg / variant bg-dvorak-phonetic. On macOS use
System Settings > Keyboard > Text Input > Edit to add the supplied source when discovered.
If a refresh or logout is necessary, save work and perform it manually. Verify expected Cyrillic
letters and shifted symbols against the supplied layout images/assets; do not infer typing
success from a headless validation report.

## Update, repair, and idempotency

Run the same install command three times on a current setup. Expect unchanged after the first
successful run, no new duplicates, no new backups on no-op, and unchanged unrelated settings.
In disposable fixtures, start with an older supplied version, a removed project registration,
a partial macOS bundle, and duplicated project entries; rerun and verify updated/repaired state.
Malformed shared files or ambiguous bundle ownership must be refused with a recovery action.
Do not introduce corruption on a personal live desktop to perform these tests.

From a different directory:
```sh
uv run --no-project --python /absolute/path/to/checkout/.venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic status
```

Repeat with a checkout path containing spaces and Bulgarian characters, properly quoted.

## Failure diagnostics and restoration

Capture diagnostics without requiring color:
```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --dry-run 2>installer.log
```

Use the system-scope option for Linux. Invalid input/missing tools must fail before writes.
Automated fault fixtures interrupt every mutation boundary and check the retained original
bytes, journal state, recovery messages, and successful retry.

For a real recorded transaction, use its reported recovery ID:
```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic recover RUN_ID
```

Add --scope system on Ubuntu. Add --dry-run to preview recovery; Linux may request authorization
to read its root-owned journal, but must make no installation/recovery-state writes. If authorization
is unavailable, report incomplete inspection and fail; never claim a clean state.
The command must refuse to overwrite intervening external edits. Interruption returns exit 130
only before mutation or after successful restoration; recovery still required returns exit 5.
A restored fresh install returns shared files to their prior content and removes only verified
project-created artifacts. See contracts/cli.md for status and exit-code meanings.

## CI and release evidence

A pull request or push to main must produce four required native jobs and one aggregation result:
ubuntu-24.04, macos-15-intel, macos-15, macos-26. Each uses the pinned Python/uv and locked tools.
Download same-commit coverage artifacts into one directory, combine with coverage combine,
generate JSON/HTML reports, and run the exact checker. Missing reports or any failed native job
must fail the final result; retain diagnostic logs for failed tests. Only after verifying that all
four native jobs and their same-commit artifacts are present, run the aggregate checker:

```sh
uv run --locked python tools/check_coverage.py coverage.json
```

Here coverage.json must be generated from the combined native artifacts, never the earlier local
single-platform report.

Before release record commit, OS version/architecture, Python version, desktop/session type,
fresh/update/repair/no-op outcomes, selected layout and actual typed output, activation steps,
and successful restoration. Cover both GNOME X11 and Wayland plus all declared macOS targets.
Headless CI cannot replace this manual evidence.
