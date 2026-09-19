# Implementation Plan: Automated Linux and macOS Layout Installation

**Branch**: main (actual Git branch); setup-plan reports logical feature 001-automate-layout-install
**Date**: 2026-09-18
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from specs/001-automate-layout-install/spec.md

## Summary

Build one Python CLI that inspects current state and chooses install, update, repair, or no-op.
Reuse workflow, logging, and recovery policy across Linux/macOS adapters. Preserve existing
layout identities, validate staged assets before writes, journal every mutation, and report
desktop activation separately. Use uv-managed CPython 3.14.7, native CI, and a strict combined
line-coverage gate above 80%. Research decisions and primary sources are in research.md.
This plan defines work; it does not claim installation or tests have been implemented.

## Technical Context

**Language/Version**: CPython 3.14.7; supported >=3.14.7,<3.15; recheck latest stable before release.

**Primary Dependencies**: Standard-library runtime; uv 0.12.16; pytest, coverage.py, Ruff, mypy
as locked development dependencies. Linux native validator: xkbcli from libxkbcommon-tools
with installed xkb-data. macOS validator: plutil. Minimal package build backend locked with uv.

**Storage**: Existing XKB files or macOS bundle plus protected JSON transaction journals,
backup contents, and SHA-256 manifests. No server/database.

**Testing**: pytest unit, adapter contract, CLI, fault-injection, and native integration tests;
Ruff lint/format and mypy strict; branch-enabled coverage with exact line threshold.

**Target Platform**: Ubuntu Desktop 24.04 LTS x86_64 GNOME X11/Wayland; macOS 15 Intel/ARM64;
macOS 26 ARM64. Native CI on ubuntu-24.04, macos-15-intel, macos-15, macos-26.
Windows is an extension target, not a current compatibility claim.

**Project Type**: Local command-line installer operating from an obtained project checkout.

**Performance Goals**: On baseline machines, inspection/no-op under 5 seconds and file
installation under 30 seconds, excluding dependency setup, authorization, and desktop refresh.
These are engineering budgets; native validators time out after 30 seconds with actionable errors.

**Constraints**: One invocation after explicit environment preparation; launch product commands
with uv synchronization and Python downloads disabled, and read-only checks for a missing/stale
prepared environment. Fail with preparation instructions rather than implicitly repairing it.
No manual config edits; no automatic reboot,
session restart, network update, or input-source switching. Explicit Linux system consent,
user-local macOS scope, safe recovery, no arbitrary public destination override.

**Scale/Scope**: One keyboard layout per selected scope on one machine; two adapters and one
test-only extension adapter. Asset inventory and platform ownership bound every mutation.

## Constitution Check

Pre-research review: PASS with the explicit Windows-scope exception below.
Post-design review: PASS with the same exception; no unresolved design decisions block tasks.

| Principle | Design evidence / gate |
|---|---|
| I. Safe scripting | Python entry point, validated inputs, stderr diagnostics, checked argument-list subprocesses, secure temporary files, path tests; shell wrappers only if needed and separately checked |
| II. OS compatibility | Concrete native matrix; Windows deferred by the user's explicit feature scope; unsupported environments fail before mutation |
| III. SOLID | Pure inspection/planning, shared transaction engine, small typed adapter contract, injected filesystem/process/lock boundaries |
| IV. KISS | Standard-library runtime, static adapter registry, no daemon, plugin discovery, GUI, or self-updater |
| V. Validation | Native tests, failure/recovery scenarios, all matrix results required, exact combined line coverage >80%, manual desktop release records |
| VI. Python/uv | Exact Python/uv baseline, explicit locked setup, non-syncing/offline product launches with read-only environment checks, Ruff, mypy, typed interfaces and no import-time side effects |
| Installation constraints | Preserved identity, explicit scope, backups, journaled recovery, no session disruption |
| Governance | This design follows constitution 1.1.0; exceptions and release evidence remain reviewable |

Windows exception: the user's Linux/macOS request and subsequent explicit future-Windows
instruction authorize this feature scope. Principles II/V's Windows implementation and native
release tests are deferred through this feature. Mitigation: portable shared code, extension
contract test, safe unsupported-platform refusal, and no Windows support claim. Revisit before
any Windows-support release. The constitution itself is not amended by this plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-automate-layout-install/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── platform-adapter.md
└── checklists/requirements.md
```

tasks.md is created by the subsequent tasks workflow, not this planning phase.

### Source Code (repository root)

```text
pyproject.toml
uv.lock
.python-version
src/bg_dvorak_phonetic/
├── __init__.py
├── __main__.py
├── cli.py
├── models.py
├── workflow.py
├── transaction.py
├── diagnostics.py
├── privileged.py
└── platforms/
    ├── __init__.py
    ├── base.py
    ├── linux.py
    └── macos.py
linux/                         # existing authoritative layout assets
mac-os/                        # existing authoritative bundle
tests/
├── unit/
├── contract/
├── integration/
└── fixtures/
tools/check_coverage.py
.github/workflows/tests.yml
docs/
├── installation.md
├── development.md
└── release-validation.md
README.md
```

**Structure Decision**: One typed Python package and two adapters, with existing asset paths
unchanged. The CLI accepts a project checkout as the distribution model; no wheel-based asset
distribution is claimed. Resolve assets from an explicitly known project root, not cwd.
The development install exposes bg-dvorak-phonetic; a module entry point delegates to the same CLI.
The test-only third adapter stays under tests, not production.

## Design and Implementation Sequence

1. Establish Python/uv metadata, entry point, source-root discovery, shared models, logs,
   and test fixtures. The development tool versions become exact through the initial uv.lock.
2. Implement read-only platform detection, asset validation, identity-based inspection,
   immutable change planning, and contract tests.
3. Implement the shared journal/backup/lock engine and restricted Linux privileged worker.
   Inject failures at every mutation boundary, including recovery failure and concurrent edits.
4. Add Linux transforms/native compilation and macOS staged bundle validation, preserving
   existing manual installations and refusing ambiguous shared configuration.
5. Complete CLI outcomes, progress logs, scope consent, no-op behavior, and recovery command.
   Test subprocess boundaries, foreign cwd, Unicode paths, missing tools, and noninteractive use.
6. Add native CI, artifact aggregation and exact coverage gate; update quick-start, repair,
   activation, troubleshooting, contributor and release-validation documentation.
   These are implementation sequence decisions, not a generated task list.

### Platform behavior

Linux modifies only verified project spans within symbols/bg and Bulgarian variant lists in
evdev.xml and distinct base.xml. Use complete staged XKB validation, not just file presence.
Installation requires --scope system. Elevation is confined to the restricted worker for
protected-journal inspection and authorized apply/recovery.
The README's incorrect standalone layout invocation is replaced by bg + variant guidance.
GNOME Input Sources selection remains a user step; setxkbmap is not used to configure Wayland.

macOS defaults to user scope, stages and validates the existing bundle, and reports Input Sources
instructions. Detect system duplicates but do not modify them. A requested system scope is
unsupported in this feature. Preserve bundle/input-source IDs and do not rewrite preferences.

### Transaction and failure behavior

Preflight -> inspect assets and protected journals (authorize read-only access if needed) ->
recover interrupted work if this is an actual mutation request -> plan -> authorize writes ->
lock -> revalidate -> backup/journal -> stage/validate -> apply -> verify -> commit. Any failure after mutation triggers reverse-order restoration.
A crash leaves a journal and retained originals; the next run repairs that transaction before
starting new work. Refuse automatic restoration if post-crash content no longer matches recorded
before/after hashes. Report the backup path and manual recovery instructions.

Dry-run and status may authorize read-only Linux journal inspection but cannot change installation
or recovery state, including creating backups, journals or locks. Denied authorization produces an
incomplete-inspection error, never a clean-state or no-op claim. Fresh validation under the mutation
lock is mandatory after a preview. Exit 5 takes precedence over exit 130 when interruption leaves
recovery required; exit 130 applies only before mutation or after successful restoration.

Use same-filesystem staging and individual atomic file replacements; a multi-file update or
bundle directory swap is recoverable, not globally atomic. Locks prevent installer collisions;
hash checks detect external edits. Scope directories and manifests cannot be user-writable in
system mode. No-op leaves installed assets and backups untouched.

### Validation and CI

Required matrix jobs run locked setup, lint, format, types, all shared contracts, and native
integration fixtures. Linux installs native validation prerequisites in the disposable runner;
macOS validates plists with its native tool. Tests never target live keyboard locations.
Fault injection covers denied sudo, failures between replacements, out-of-space, interruption,
rollback failure, symlinks, races, malformed files, duplicate identity, and activation pending.

Coverage measures all src production modules, including worker subprocess execution in tests.
Each OS must pass independently; a final job requires all four same-commit coverage artifacts,
combines relative paths, produces reports, and enforces covered_lines*100 > num_statements*80.
Branch coverage is reported separately. Local reports are informational and do not invoke the
aggregate threshold checker. Only the complete same-commit native aggregate enforces the >80%
line threshold. The gate's own boundary tests prevent exactly-80% success.
Upload diagnostics even for failed tests; missing/failed jobs cannot produce a green aggregate.
Actions use reviewed commit SHA pins, read-only repository permissions, and no PR secrets.
Workflow triggers: pull_request, push to main, and workflow_dispatch.

Manual release checks cover discovery, selection, expected Cyrillic output and modifiers,
old-install repair, refresh/logout instructions, and recovery on the declared desktop matrix.
Do not publish a compatibility claim before this evidence exists.

### Requirement traceability

| Requirements | Design / validation |
|---|---|
| FR-001–005 | CLI install mode, state model, per-platform transforms, fresh/update/repair/no-op fixtures |
| FR-006–008 | Journal/lock/backup worker, scoped authorization, fault/concurrency tests |
| FR-009–012 | Native validation, separate activation state, structured diagnostics and exit tests |
| FR-013–015 | Unit/contract/native/CLI suites, OS matrix, required results and coverage aggregation |
| FR-016–017 | README/docs and quickstart, recorded manual release matrix |
| FR-018–020 | Python package, platform protocol, test-only extension adapter and contract suite |
| SC-001–007 | Quickstart validation scenarios plus CI and manual release evidence |
| Constitution coverage | Exact whole-source line gate >80%, branch report, all artifacts required |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Windows coverage deferred (Principles II/V) | Explicit user scope: Linux/macOS now, Windows later | Implementing Windows now expands the authorized feature; reusable contract and safe refusal preserve future support |

No other constitution deviations. Journaled writes and the privileged worker are required by
recovery and least-privilege requirements; no general-purpose transaction framework is planned.

## Implementation correction (2026-09-19)

The originally planned `uv run --no-sync` invocation was experimentally shown to create a
missing .venv. To honor the existing no-provisioning requirement, use `uv run --no-project
--python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic`. From another
directory, pass the absolute prepared interpreter path. This changes command syntax, not
the runtime pin, setup policy, or authorized feature scope. See validation/review.md.
