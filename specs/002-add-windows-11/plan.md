# Implementation Plan: Windows 11 Support

**Branch**: `automate` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-add-windows-11/spec.md`

The setup script resolved feature identifier `002-add-windows-11`; the actual Git branch is
`automate`. No branch was created or switched. This plan ends at Phase 1 design.

## Summary

Extend the existing Python CLI with native Windows installation, inspection, update, repair,
preview, and recovery. Target Windows 11 25H2 Home/Pro x64. Ship a generated native layout DLL,
install in explicit system scope, and leave keyboard selection to the user. Preserve shared
workflow and recovery policy while adding typed registry operations and a Windows resource backend.
Use immutable versioned DLLs to avoid overwriting loaded layouts. Verify real desktop typing and
recovery before claiming support; hosted native tests are a separate evidence layer.

## Technical Context

**Language/Version**: Python 3.14.7, supported metadata `>=3.14.7,<3.15`; native generated C
keyboard tables/export shim only. PowerShell 5.1/7 invocation examples; no new shell installer.

**Primary Dependencies**: Existing uv 0.12.16 lock and standard-library Python runtime;
`ctypes` and `winreg` in lazy Windows modules. Maintainer-only VS 2022 17.14 with SDK/WDK
26100.6584; build manifest locks exact installed tool versions and hashes. Prebuilt DLL assets
are supplied with the release. No runtime compilation, MSI, MSKLC, or background service.

**Storage**: Project-specific native System32 DLLs; bounded HKLM keyboard registration;
protected ProgramData recovery root with JSON journals and original snapshots. No database.

**Testing**: Existing pytest, coverage, Ruff, mypy; portable resource contract tests; native
Windows registry/filesystem tests; compiled mapping checks; controlled 25H2 Home/Pro desktop
validation including x64 and 32-bit application typing. Type-check production package and tools
with `uv run --locked mypy src tools` locally and in CI. Required combined line coverage >80%.

**Target Platform**: Windows 11 25H2 Home/Pro x64 (build family 26200); regressions on Ubuntu
24.04 GNOME X11/Wayland x86_64, macOS 15 Intel/Apple Silicon, macOS 26 Apple Silicon.
`windows-2025` is a native API/build CI host, not a supported product target.

**Project Type**: Existing CLI with native platform assets and adapters.

**Performance Goals**: One install invocation after explicit preparation; zero writes for preview
and no-op. Engineering budget: local inspection/preview under 5 seconds on a warmed test VM,
excluding human authorization; record timings, do not make unsupported hardware guarantees.

**Constraints**: Offline product commands, explicit system scope, bounded elevation, preserved
unrelated settings, no automatic activation/reboot/sign-out, recoverable partial changes, no
compatibility claim without native evidence. No production Python coverage exclusions.

**Scale/Scope**: One logical project layout, one machine registration, two Windows editions,
six existing command outcomes/workflows; no new GUI, general uninstall, ARM64, or enterprise fleet management.

## Constitution Check

*Gate assessed before research and re-evaluated after Phase 1 design.*

| Principle / constraint | Before research | Post-design evidence and gate |
| --- | --- | --- |
| I. Safe scripts | Pass: keep Python workflow | Argument-list commands, bounded timeouts, explicit setup; no new shell product script. Static analysis applies to any retained/added launcher. |
| II. Three platforms | Pass: Windows is now in scope | Exact support matrix, native runtime commands, Server/WSL evidence separation; unavailable native evidence blocks release. |
| III. SOLID | Pass: existing adapter seam | Shared workflow/phase policy, injectable resource backend, lazy Windows imports, unchanged POSIX adapter behavior; no duplicate installer. |
| IV. KISS | Pass: no general plugin/GUI | Direct bounded file/registry changes; no MSI/service/dependency manager during installation. |
| V. Evidence | Pass: required work identified | Five CI inputs, >80% exact line coverage, branch report, failure/recovery tests and Home/Pro desktops. Native gates remain pending execution. |
| VI. Python/uv | Pass: existing stable pin retained | All installation logic Python; lock remains authoritative; native C contains only required layout data/ABI. Recheck current stable Python before release. |
| Reversible changes and least privilege | Pass: explicit design requirement | Versioned DLLs, protected journals, UAC worker, explicit system scope, snapshot comparisons, recovery conflict refusal. |
| Mapping preservation | Pass: sources available | Linux explicit levels are Windows authority; platform differences documented in mapping contract; existing assets unchanged. |

No constitution exception is required. Post-design gate passes for planning; this is not a test or
release approval. No Windows native validation was performed during planning. The prior feature's
Windows exclusion does not apply here. Existing platform validation gaps remain release blockers.

## Project Structure

### Documentation (this feature)

```text
specs/002-add-windows-11/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
└── contracts/
    ├── cli.md
    ├── windows-platform.md
    └── windows-layout.md
```

`tasks.md` is the next command's output and is not created by this plan.

### Source Code (repository root)

```text
src/bg_dvorak_phonetic/
├── cli.py                         # win32 detection and scope defaults
├── workflow.py                    # platform asset inventory, resource result summaries
├── models.py                      # typed registry operations, compatible v2 journals
├── transaction.py                 # shared phase/recovery policy, injected resource backend
├── resources.py                   # narrow backend protocol; existing POSIX implementation
├── windows_worker.py              # constrained elevation/IPC entry point
└── platforms/
    ├── __init__.py                 # static lazy Windows registration
    ├── base.py                     # compatible extension of current contracts
    ├── windows.py                  # probe, ownership, plan, verification, guidance
    └── windows_native.py           # registry, ACLs, paths, locking, elevation primitives
windows/
├── mapping.json                   # reviewed Windows expected mappings
├── layout/                        # generated table inputs, export/resource definitions, build project
├── toolchain.lock.json             # exact build tooling/provenance
└── assets/                        # release manifest and prebuilt x64 layout DLL
tools/                            # existing directory, no separate package
├── build_windows_layout.py
├── validate_windows_layout.py
└── collect_coverage.py             # fifth required native artifact
tests/                            # existing unit/contract/integration organization
├── unit/                          # mappings, operations, platform probe, IPC parsing
├── contract/                      # same workflow/backend guarantees for all platforms
├── integration/                   # real isolated Windows resources and crash injection
└── fixtures/                      # mapping expectations, registry states, old journals/assets
.github/workflows/tests.yml         # existing workflow, add Windows job
docs/                              # installation, development, release validation
```

**Structure Decision**: Extend the existing src-layout package and tests. New native behavior
is isolated; common resource support is extracted only where required for registry/ACL differences.
The implementation must use the existing workflow filename rather than creating a second test pipeline.

## Phase 0: Research Results

[research.md](research.md) records decisions, evidence, and alternatives. Principal findings:
Unix locks/ownership/directory durability cannot be reused unchanged; the two existing layout
assets have different modifier layers; Windows hosted runners do not establish Windows 11 support.
All design unknowns have selected approaches. The first implementation gate is a native layout
proof, including Windows security policy and 32-bit application behavior, before broader installer work.

## Phase 1: Design

- [data-model.md](data-model.md): source manifests, registration identity, resource operations,
  compatible recovery schemas, and state transitions.
- [CLI contract](contracts/cli.md): invocation, scope, results, consent, and recovery.
- [Windows platform contract](contracts/windows-platform.md): native operations, privilege boundary,
  ownership checks, durability, and extension seams.
- [Layout contract](contracts/windows-layout.md): mapping authority, modifier behavior, build assets,
  identity, and empirical native proof.
- [quickstart.md](quickstart.md): commands and controlled validation scenarios for implementation.

## Implementation Order and Acceptance Gates

1. **Native asset proof**: lock build inputs, generate/review mapping fixtures, compile and check
   DLL identity/exports, prove Settings discovery and x64/32-bit typing on 25H2 with normal security.
   Use controlled manual test registration/restoration in a snapshotted VM; the proof must not
   depend on the later product adapter. Do not expand the installer if this proof fails; amend the
   measured design first.
2. **Portable resource seam**: add typed registry operations and backend injection while preserving
   v1 POSIX recovery; prove existing Linux/macOS contracts and failure behavior unchanged.
3. **Windows read path**: platform detection, inventories, ownership, preview/status, and protected
   read-only journal access. Prove no persistent changes including no lock/journal creation.
4. **Windows mutations**: protected worker, durable snapshots, versioned DLL registration, verify,
   repair, replay, interrupted-step reconciliation, and conflict-safe rollback.
5. **Evidence and docs**: fifth native CI job and coverage input, exact commands, controlled Home/Pro
   desktop walkthroughs and existing-platform regression evidence. After final code, asset, runtime
   and workflow corrections, freeze the candidate and replay all required CI and desktop acceptance
   on that exact candidate (T065). Substantive corrections invalidate prior evidence and require
   another final validation cycle. No support claim until all gates pass.

Requirement traceability: FR-001/002/005/008/012 → CLI and platform contracts; FR-003/004 → layout
contract; FR-006/007/009/010/011 → platform/data model; FR-013/014/015 → quickstart and validation gates.
SC-001–SC-006 are checked by the corresponding quickstart scenarios and release record.
