# Tasks: Windows 11 Support

**Input**: Design documents in `specs/002-add-windows-11/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [contracts/windows-platform.md](contracts/windows-platform.md), [contracts/windows-layout.md](contracts/windows-layout.md), [quickstart.md](quickstart.md), and `.specify/memory/constitution.md`.

**Tests**: Required by spec FR-014/015 and the constitution. Add the named tests before the associated behavior, observe the relevant failure, then implement and make them pass. Do not invent passed native evidence from mocks or inspection.

**Organization**: Four user-story phases follow shared setup and foundation. Code-formatted file paths are repository-relative; Markdown links resolve relative to this document. The project already exists; extend its Python package, locked environment and workflow. Every checkbox below represents work still to do.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies tasks that can run together after their stated prerequisites finish; it never overrides native gates or authorizes concurrent edits to the same file.
- `[US1]`–`[US4]` map to the specification. Setup, foundation and polish have no story label.
- Each task names its exact files and dependencies. References to design constraints in quotation marks are normative excerpts from `specs/002-add-windows-11/data-model.md` with line wrapping normalized.
- A native evidence task remains incomplete if its environment is unavailable unless the project owner explicitly waives that gate. Record any waiver and its unverified scope; do not present hosted Server or mock results as desktop proof.

## Path Conventions

Production Python: `src/bg_dvorak_phonetic/`; native assets: `windows/`; build/validation tooling: `tools/`; tests: `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/` and `tests/native/`; evidence: `specs/002-add-windows-11/validation/`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose / goal**: Prepare the existing repository, native build prerequisites, and isolated validation scaffolding; do not reinitialize the Python project.

### Implementation

- [X] T001 Run the existing locked checks, inventory runtime/asset/test assumptions, and record the branch, source revision, available native environments, existing Linux/macOS release blockers, and unmodified baseline results in `specs/002-add-windows-11/validation/baseline.md`; retain Python 3.14.7 and uv 0.12.16 from `pyproject.toml` and `uv.lock`.
- [X] T002 Create `windows/toolchain.lock.json` and the native build prerequisite section in `docs/development.md` for VS 2022 17.14 and matching SDK/WDK 26100.6584; record actual compiler/package versions, acquisition locations, input hashes, and upstream sample license/provenance in `windows/layout/NOTICE.md`; explicitly record unavailable tools instead of fabricating lock values. Depends on T001.
- [X] T003 [P] Create isolated Windows resource fixture factories in `tests/fixtures/windows_resources.py` using temporary files and test-owned registry keys, capture/restore original test resources, and prohibit live keyboard roots; support injected contexts and fault hooks without adding public test-root or platform-bypass switches. Depends on T001.
- [X] T004 [P] Create `specs/002-add-windows-11/validation/README.md` defining pending/passed/failed evidence records, exact revision/environment/command capture, Home/Pro desktop access, VM snapshots and cleanup; map the native proof and final release gates to the scenarios in `specs/002-add-windows-11/quickstart.md`. Depends on T001.

**Checkpoint**: The existing baseline and native environment availability are recorded. No Windows compatibility is claimed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose / goal**: First prove the Windows layout ABI; only then extend shared resource and recovery infrastructure used by every story.

**Independent test**: A disposable Windows 11 25H2 native proof passes, then typed resource, schema compatibility, and native backend checks preserve the existing platform guarantees.

### Native asset proof: tests before build

- [X] T005 [P] Create independently reviewed expected-output cases in `tests/fixtures/windows_mapping_expected.json` for all 47 physical Linux positions, explicit modifier levels, Caps, dead sequences, US Dvorak Ctrl shortcuts, control/navigation/keypad/ISO keys, and documented macOS differences; enforce “Every explicit Linux symbol has a Windows case or an explicitly reviewed platform difference.” and “ASCII control/navigation expectations are recorded separately.” Depends on T002, T003, T004.
- [X] T006 [P] Add build/asset contract tests in `tests/contract/test_windows_layout.py` against `specs/002-add-windows-11/contracts/windows-layout.md`: deterministic generation, x64 export/resource metadata, missing/mismatched tools, malformed manifests, unsupported architecture, source/hash mismatch, trusted provenance, and no compile/download during product operations; the independently maintained expected fixture is the oracle, not generated tables. Depends on T002, T003, T004.

### Native asset proof: implementation

- [X] T007 Create `windows/mapping.json` with physical XKB position, scan code, virtual key, modifier set, Caps behavior, expected Unicode output or named dead state, source level, and next-input/result cases; implement the complete `specs/002-add-windows-11/contracts/windows-layout.md` policy and record review in `specs/002-add-windows-11/validation/mapping.md`; enforce “A complete expected-output fixture is independently reviewed; do not test a generator only against its own generated tables.” Depends on T005, T006.
- [X] T008 Implement the locked, bounded native build in `tools/build_windows_layout.py` and `windows/layout/bgdv.vcxproj`, with generated C tables, export definition and display-name resources; emit `windows/assets/manifest.json` and a content-addressed x64 DLL, record compiler/kit/source/mapping hashes, and fail on tool mismatch without provisioning tools or embedding installer logic in C. Depends on T007.
- [X] T009 Implement `tools/validate_windows_layout.py` with manifest schema, hashes, PE/resource/export checks and trusted-build provenance checks without registration or DLL execution; enforce “Relative paths must stay within its asset root, reference regular non-reparse files, and contain no alternate data streams, device names, parent traversal, or absolute paths.”, “Reject case-insensitive duplicate names.”, and “The DLL must match the x64 ABI and expose `KbdLayerDescriptor`; export checks do not substitute for native typing.”; make the layout contract tests pass. Depends on T008.
- [X] T010 Create a minimal native text-input probe in `tests/native/windows_typing_probe.c` and its x64/32-bit build entry in `tools/build_windows_layout.py`; capture actual translated input, modifier/dead-key sequences and application architecture without adding a second layout DLL or a resident remapper. Depends on T009.

### Native asset proof: blocking gate

- [X] T011 **WAIVED 2026-09-20 by project owner for implementation sequencing.** The controlled 25H2 Home/Pro x64 asset proof was unavailable and was not executed. The missing registration/restoration, identity collision, normal security/Secure Boot, Settings discovery, selection, x64 editor/browser, and 32-bit translated-input observations are recorded in `specs/002-add-windows-11/validation/native-proof.md`. Hosted Enterprise/Server evidence unblocks dependent implementation but is not presented as Home/Pro desktop proof. Depends on T010.

### Shared resource foundation: tests

- [X] T012 [P] Add schema/serialization tests in `tests/unit/test_windows_models.py` and immutable v1 fixtures in `tests/fixtures/windows_v1_journals.json` covering canonical UUIDv4, v2 tagged operations, absent versus empty registry values, value types, canonical fingerprints, unknown versions, no-op constraints, and old POSIX journal recovery without rewriting. Depends on T011.
- [X] T013 [P] Add backend and transaction contract tests in `tests/contract/test_resource_backend.py` for snapshot/stage/apply/verify/restore/storage/locking, typed registry resources, write-ahead ordering, v1 behavior, reverse rollback, and before/after/third-state reconciliation; exercise real isolated Windows resources with `tests/fixtures/windows_resources.py` and the default POSIX backend on their native hosts. Depends on T011.

### Shared resource foundation: implementation

- [X] T014 Extend `src/bg_dvorak_phonetic/models.py` with v2 file/registry operation union, registration snapshots and plan digest; retain “canonical run UUIDv4”, platform/scope/action/source hashes and observation metadata. Enforce “Preserve schema-v1 `FileOperation` and POSIX plans.”, “never encode a registry path as `Path`.”, “Only project resource types are permitted; plans contain no executable commands.”, “A no-op has no operations and causes no state creation.” and “Update order is files first, then registration; old files remain available.”; registry fields include fixed hive/view/bounded subkey/typed before-after values/key-created flag, and file fields include canonical destination/staged digest/backup/ACL metadata. Depends on T012, T013.
- [X] T015 Add v2 recovery serialization and validation in `src/bg_dvorak_phonetic/models.py`: request/source digests, resource snapshots/backup hashes, expected post-state, intent/completed steps, retained resources, timestamps and diagnostics; constrain phases to prepared/applying/verified/committed/rolling_back/restored/recovery_required and validate step indices. Enforce “Snapshots preserve absent vs present-empty, registry value types, unknown observed values, and security descriptors.”, “Backups and journal live under the protected state root; no arbitrary paths.”, “Existing v1 POSIX records remain readable and recoverable without rewriting them.” and “unknown versions fail safely.” Depends on T014.
- [X] T016 Extract the concrete POSIX operations behind a narrow resource protocol in `src/bg_dvorak_phonetic/resources.py`, inject it into `src/bg_dvorak_phonetic/transaction.py`, and extend `src/bg_dvorak_phonetic/platforms/base.py` compatibly; keep existing adapters on the default backend, preserve shared transaction policy, and remove Unix-only assumptions from shared paths without copying the engine. Depends on T015.
- [ ] T017 Implement lazy native registry snapshot/typed mutation, known-folder/root resolution, ACL/owner checking, file-handle identity and path guards in `src/bg_dvorak_phonetic/platforms/windows_native.py`; reject reparse ancestors/junctions, unexpected hardlinks, alternate streams, device paths and case aliases, bound writes to fixed resources, and preserve security descriptors. Enforce “Treat registry key/value names case-insensitively.” and “Snapshot ordering is canonical, but raw value types and content are preserved.” Depends on T016.
- [ ] T018 Implement the Windows resource backend in `src/bg_dvorak_phonetic/platforms/windows_native.py` using protected ProgramData state, Administrators/SYSTEM-only DACL, exclusive nonblocking handle lock, destination-volume staging, verified backup/journal durability and registry flush checks; expose read-only inspection that never creates lock/journal/staging files, retain loaded files, and fail rather than ignoring unsupported durability operations. Depends on T017.
- [ ] T019 Extend shared v2 apply/automatic-rollback behavior in `src/bg_dvorak_phonetic/transaction.py`: reobserve under lock, retain originals, persist intent, write immutable files before registration, verify before commit, and reconcile uncertain steps by snapshots. Enforce “Persist originals and operation intent before each mutation.”, “If neither matches, stop with recovery-required.”, “Recovery validates all relevant resources before restoring any, reverses applied operations, verifies the restored state, and persists its outcome.” and “Never delete backups on successful install.”; this minimum safety path must work before any public Windows mutation. Depends on T018.
- [ ] T020 Refactor `src/bg_dvorak_phonetic/workflow.py` for selected-platform inventories and injected resource engines while retaining legacy defaults; normalize Windows editable-install URIs/paths read-only and preserve explicit offline environment validation. Enforce “Linux/macOS inventories remain valid without Windows build products on non-Windows runs.” and keep registry summaries distinct from filesystem paths. Depends on T019.

### Shared resource foundation: gate

- [ ] T021 Run shared and native resource/schema tests plus existing Linux/macOS contract, failure and v1 recovery checks; record exact commands/results and unavailable native checks in `specs/002-add-windows-11/validation/foundation.md`, fix regressions in `src/bg_dvorak_phonetic/resources.py` and `src/bg_dvorak_phonetic/transaction.py`, and proceed only with the required foundation evidence passing. Depends on T020.

**Checkpoint**: All foundation tasks must pass before story implementation. The native proof task blocks installer expansion. Missing native access stays pending; it is not a passed gate.

---

## Phase 3: User Story 1 - Install and Type on Windows 11 (Priority: P1)

**Purpose / goal**: Deliver a safe fresh install with explicit system scope, bounded elevation, manual activation and correct typing. This is the first demonstrable MVP, not a release waiver.

**Independent test**: On clean Home and Pro 25H2 desktops, run one install after preparation, preserve other input settings, select the layout manually, verify every mapping in an editor/browser and the 32-bit probe, then sign out/in and repeat.

### Tests

- [ ] T022 [P] [US1] Add CLI/adapter contract tests in `tests/contract/test_windows_cli.py` for explicit install scope, status default, unsupported user scope/OS/architecture/runtime, offline prerequisites, help/version without elevation, --yes versus UAC, immutable outcomes and no automatic activation/restart, following `specs/002-add-windows-11/contracts/cli.md`. Depends on T021.
- [ ] T023 [P] [US1] Add privileged boundary contract tests in `tests/contract/test_windows_worker.py` for fixed actions, protocol/run-ID/digest validation, unknown fields, bounded messages, nonce/peer binding, UAC cancellation, noninteractive refusal, stable code snapshot checks, argument quoting and transport loss; inspect/preview must not create durable state. Depends on T021.
- [ ] T024 [P] [US1] Add native fresh-install integration tests in `tests/integration/test_windows_install.py` for file-before-registration ordering, original snapshots, preserved unrelated settings and ACLs, full post-write verification, rollback on injected failure, Unicode/space paths, alternate cwd and activation-pending output; use isolated native resource fixtures. Depends on T021.

### Implementation

- [ ] T025 [US1] Implement `WindowsAdapter.probe` and platform registration in `src/bg_dvorak_phonetic/platforms/windows.py`, `src/bg_dvorak_phonetic/platforms/__init__.py` and `src/bg_dvorak_phonetic/cli.py`; allow only native x64 Windows 11 25H2/build 26200 Home/Pro, explicit system install/recover scope, read-only status default, and lazy native imports; reject Server, ARM64, 32-bit process and other build families before mutation. Depends on T022, T023, T024.
- [ ] T026 [US1] Implement Windows manifest inventory/validation in `src/bg_dvorak_phonetic/platforms/windows.py` and connect it through `src/bg_dvorak_phonetic/workflow.py`; carry all layout/mapping/build identity fields from `specs/002-add-windows-11/data-model.md`, including “`layout_id=bg-dvorak-phonetic`”, validate DLL/export/resource/hash metadata before privileges, enforce the asset path constraints tested in T009, and explain how to obtain matching prebuilt assets without compiling/downloading during install. Depends on T025.
- [ ] T027 [US1] Implement read-only fresh/current/conflicting registration inspection and bounded fresh-install planning in `src/bg_dvorak_phonetic/platforms/windows.py`; snapshot the exact four typed layout values, ACL and references, use the validated fixed identity and manifest DLL basename, reject identity collisions/unknown contents, and supply both file and registry plan summaries without changing user language preferences. Depends on T026.
- [ ] T028 [US1] Implement ShellExecuteExW/runas transport and authenticated local named-pipe exchange in `src/bg_dvorak_phonetic/platforms/windows_native.py` and `src/bg_dvorak_phonetic/windows_worker.py`; use the explicit prepared x64 interpreter with isolated/no-bytecode mode, SID-restricted pipe DACL, remote-client rejection, peer/nonce validation, bounded launch/IPC timeouts, and fixed request actions; never elevate uv or expose arbitrary command/path execution. Depends on T027.
- [ ] T029 [US1] Implement restricted worker dispatch in `src/bg_dvorak_phonetic/windows_worker.py`: validate stable code/assets before optional imports, use an in-memory verified snapshot for read-only actions, reconstruct native roots, reobserve under lock and recompute the approved plan digest before applying the shared engine; reject mismatches and use only trusted run IDs for recovery access, preserving durable state if the parent disappears. Depends on T028.
- [ ] T030 [US1] Connect `apply_authorized`, protected read-only `recovery_access`, `verify_installed` and staged validation in `src/bg_dvorak_phonetic/platforms/windows.py`; install immutable DLLs and exact project registration via the shared Windows backend, refuse or recover pending work before a new apply, verify file/registry snapshots, and retain originals on every partial failure without invoking keyboard activation. Depends on T029.
- [ ] T031 [US1] Add Windows activation guidance and resource-aware final output in `src/bg_dvorak_phonetic/platforms/windows.py`, `src/bg_dvorak_phonetic/cli.py` and `src/bg_dvorak_phonetic/diagnostics.py`; show scope, plan, progress, outcome, recovery UUID/location, manual Settings/Win+Space steps and delayed discovery guidance; map native failures to existing codes and never claim active typing from installed hashes. Depends on T030.
- [ ] T032 [US1] Add the initial native Windows setup/install/activation section in `README.md` and `docs/installation.md` with Python/uv acquisition, prebuilt asset requirement, `.venv\Scripts\python.exe` invocation, explicit system scope, trust/privilege explanation and another working input source; mark support verification status accurately until the desktop gate passes. Depends on T031.
- [ ] T033 [US1] Run the US1 contract/native tests and controlled Home/Pro clean-install walkthrough; record complete mapping/shortcut/dead-key output, x64/32-bit application identities, unchanged unrelated preferences, alternate-admin UAC behavior, delayed discovery and post-sign-in availability in `specs/002-add-windows-11/validation/us1.md`; require the independently reviewed expected mapping to match 100%. Depends on T032.

**Checkpoint**: US1 is independently demonstrated on a clean VM, with automatic rollback and retained recovery state already provided by the foundation.

---

## Phase 4: User Story 2 - Inspect, Update, and Repair an Installation (Priority: P1)

**Purpose / goal**: Converge known older/damaged project installations safely, expose full status/preview, and ensure healthy repeats are true no-ops.

**Independent test**: Seed current, old, incomplete, duplicate and conflicting states independently in fixtures; compare status/preview with snapshots, apply repairs/updates, and run three unchanged installs with zero persistent changes.

### Tests

- [ ] T034 [P] [US2] Add full state/action/status/preview contract tests in `tests/contract/test_windows_state.py`, including every Health value, incomplete inspection, pending recovery overriding clean/no-op, no durable preview writes and three no-op repetitions; verify file/registry plans and retained old DLLs are not mistaken for duplicate effective registrations. Depends on T033.
- [ ] T035 [P] [US2] Add native update/repair fixtures and tests in `tests/integration/test_windows_repair.py` for known earlier revisions, missing registration/DLL/value, damaged files with trusted receipts, exact-identity duplicates, OS-update registration loss, same-name strangers, KLID/Layout Id conflicts, other-user/scoped settings, unexpected registry data and loaded previous DLLs. Depends on T033.

### Implementation

- [ ] T036 [US2] Implement historical receipt/manifest matching in `src/bg_dvorak_phonetic/platforms/windows.py`; enforce “Display names alone cannot.”, “Missing or corrupt components are repairable only when surviving identity plus trusted evidence bounds the resources to this project.” and “Registration ID collisions are unsafe, not a request to allocate a new identity silently.”; unexpected subkeys/values, conflicting identity and external DLL references must block destructive replacement. Depends on T034, T035.
- [ ] T037 [US2] Complete `InstallationState` construction and classification in `src/bg_dvorak_phonetic/platforms/windows.py` using the exact `specs/002-add-windows-11/data-model.md` table; enforce “Retain `Health`: absent, current, outdated, repairable, unsafe.” with installed manifest/owned resources/registration snapshots/conflicts and pending overlay. Enforce “Activation remains pending/unknown; installed files alone never prove currently active input.” and “Inspection denied or unreadable means incomplete inspection, never absent/current.” Depends on T036.
- [ ] T038 [US2] Implement update/repair/owned-duplicate plans in `src/bg_dvorak_phonetic/platforms/windows.py`: verify ownership and all before snapshots, create immutable new version files, switch one effective registration, retain previous files/receipts, refuse basename hash collisions or unsafe deletion, and never unload a layout or schedule reboot work. Depends on T037.
- [ ] T039 [US2] Complete status/preview and no-op integration in `src/bg_dvorak_phonetic/workflow.py` and `src/bg_dvorak_phonetic/platforms/windows.py`, including protected read authorization, distinct incomplete/recovery-required results, zero lock/journal/backup/file creation, and no rewrites on current installs; expose recovery overlay before action selection and measure read-only stage timings. Depends on T038.
- [ ] T040 [US2] Document update, repair ownership boundaries, existing/manual layout conflicts, immutable file retention and loaded-session refresh in `docs/installation.md`; run seeded native and controlled-desktop US2 cases, record three no-op snapshots plus warm status/preview timings excluding authorization in `specs/002-add-windows-11/validation/us2.md`, and verify the same command chooses the correct action without manual configuration edits. Depends on T039.

**Checkpoint**: US2 works against pre-seeded installations without depending on a prior US1 acceptance run; its implementation reuses the US1 adapter.

---

## Phase 5: User Story 3 - Recover from Failure (Priority: P1)

**Purpose / goal**: Expose recorded recovery and prove interrupted, concurrent, denied, locked and externally changed states remain understandable and recoverable.

**Independent test**: Induce prerequisite/authorization/write failures and crashes, preview and restore the recorded transaction, repeat recovery, then test conflicts/concurrency while preserving unrelated resources and originals.

### Tests

- [ ] T041 [P] [US3] Add public Windows recover/result contract tests in `tests/contract/test_windows_recover.py`: canonical run IDs, fixed protected root, scope/authorization, preview read-only behavior, repeat recovery, phase transitions, diagnostic destinations and all exit codes including 5 overriding 130 when state remains incomplete. Depends on T040.
- [ ] T042 [P] [US3] Add native fault-injection and process-termination cases in `tests/integration/test_windows_recovery.py` at every backup/intent/write/flush/verification/commit boundary, especially successful write before completion marker; cover disk exhaustion, access denial, loaded files, changed registry types/ACLs, external edits/references, and verified repeated restoration using real isolated Windows resources. Depends on T040.
- [ ] T043 [P] [US3] Add Windows concurrency and worker transport tests in `tests/integration/test_windows_worker_safety.py`: simultaneous operations, parent disappearance, worker timeout/interruption, stale nonce, peer mismatch, changed code/assets/plan, malicious journal paths, unsafe DACLs and path-swap/reparse/hardlink attempts; require no unrelated writes and durable recovery when outcome is uncertain. Depends on T040.

### Implementation

- [ ] T044 [US3] Complete `WindowsRecoveryAccess` and fixed inspect/recover-preview/recover dispatch in `src/bg_dvorak_phonetic/platforms/windows.py` and `src/bg_dvorak_phonetic/windows_worker.py`; read journals only from protected validated roots, keep read-only code snapshots in memory, reauthorize mutations as needed, reject unknown schemas/run IDs and report unreadable state as incomplete rather than empty. Depends on T041, T042, T043.
- [ ] T045 [US3] Complete v2 recovery replay in `src/bg_dvorak_phonetic/transaction.py` and Windows restore primitives in `src/bg_dvorak_phonetic/platforms/windows_native.py`; restore registration before deleting verified new unreferenced files, prevalidate all resources, reconcile uncertain steps and stop on third-state changes, retain locked files/backups with recovery-required, and enforce “Repeated recovery of a restored record is read-only.” without breaking v1 POSIX restore. Depends on T044.
- [ ] T046 [US3] Complete pending-transaction coordination and transport-loss handling in `src/bg_dvorak_phonetic/workflow.py` and `src/bg_dvorak_phonetic/windows_worker.py`: actual install restores unfinished changes before replanning, status/preview describe only, workers leave recoverable state if clients vanish, retries inspect durable state under the lock, and no-op never bypasses pending recovery. Depends on T045.
- [ ] T047 [US3] Finish actionable Windows failure mapping in `src/bg_dvorak_phonetic/diagnostics.py` and `src/bg_dvorak_phonetic/cli.py`: operation/location/cause/remedy, unsuccessful or recovery-required outcomes, redacted traces and non-color stderr logging, bounded noninteractive failure, recovery UUID/location and interruption precedence; never infer no changes from a failed IPC response. Depends on T046.
- [ ] T048 [US3] Complete recovery and retained-backup instructions in `docs/installation.md`, including preview/restore commands, selecting another working layout, locked-file sign-out/retry, external edit reconciliation, run-ID retention and explicit cleanup eligibility; no automatic reboot, journal deletion workaround, general uninstall, or other-user profile edits. Depends on T047.
- [ ] T049 [US3] Run crash/safety/recovery tests and controlled Home/Pro denied-UAC, interrupted update, alternate-admin, locked-file, conflict, concurrency and safe-retry demonstrations; compare exact restored snapshots, retain diagnostics and record outcomes in `specs/002-add-windows-11/validation/us3.md`, distinguishing product restoration from VM snapshot fallback. Depends on T048.

**Checkpoint**: Every induced failure has the documented result and next action, and all mutation failures either restore verified state or retain demonstrably usable recovery state.

---

## Phase 6: User Story 4 - Verify and Document Windows Support (Priority: P2)

**Purpose / goal**: Provide repeatable five-job native CI, accurate evidence provenance, complete Windows documentation and a three-platform release gate.

**Independent test**: A clean-account documentation walkthrough succeeds without source inspection, a deliberate failed required check fails aggregation, and same-revision evidence distinguishes hosted Server tests from Windows 11 Home/Pro desktop typing and recovery.

### Tests

- [ ] T050 [P] [US4] Extend artifact/coverage contract tests in `tests/unit/test_coverage_artifacts.py` and `tests/unit/test_coverage_gate.py` for five required same-revision native jobs, missing/failed/stale/empty Windows evidence, cross-platform coverage paths, unexecuted production modules, exact 80% rejection and positive denominator; retain branch and missing-line reporting. Depends on T049.
- [ ] T051 [P] [US4] Add validation-record compatibility/provenance tests in `tests/unit/test_windows_validation_record.py` covering edition/build, process/native architecture, shell, asset/mapping/build revisions, x64/32-bit apps, security context, command/result/snapshot/restoration evidence; enforce “Record CI runner identity separately from product target.”, “a Server job cannot satisfy it.” and “All release evidence refers to the release revision.” Depends on T049.
- [ ] T052 [P] [US4] Extend documented-command integration tests in `tests/integration/test_documented_commands.py` for native PowerShell 5.1/7 invocation, missing/stale setup, offline product runs, paths with spaces/Cyrillic and alternate cwd; ensure missing Windows prerequisites fail rather than silently skip native coverage and that documentation examples preserve failure exit codes. Depends on T049.

### Implementation

- [ ] T053 [US4] Extend `ValidationRecord` in `src/bg_dvorak_phonetic/models.py` with optional backwards-compatible Windows/native evidence fields tested above; keep passed/failed/pending distinctions, require positive evidence for a pass, and prevent hosted build/API results from substituting for desktop acceptance. Depends on T050, T051, T052.
- [ ] T054 [US4] Extend `.github/workflows/tests.yml` with a `windows-2025` native PowerShell job using locked Python/uv and explicitly acquired locked build tools, asset build/validation, Ruff/format/compile checks, `uv run --locked mypy src tools` covering all production Python helpers, and real isolated Windows tests; resolve type errors without blanket exclusions; preserve all four Unix jobs, read-only permissions and pinned action revisions, reject silently skipped Windows native coverage, and upload logs/JUnit/provenance/hidden coverage even on failure without executing untrusted PRs on privileged persistent desktops. Depends on T053.
- [ ] T055 [US4] Update `tools/collect_coverage.py` and `pyproject.toml` to require five complete same-commit native artifacts, normalize Windows/Unix coverage paths, and include every first-party production Python module including new build/validation helpers in the denominator; enforce `covered_lines * 100 > num_statements * 80` with no new production exclusions, publish line/branch/missing reports, and make the artifact tests pass. Depends on T054.
- [ ] T056 [US4] Add matching-source release asset assembly to `tools/build_windows_layout.py` and usage in `docs/development.md` so a prebuilt Windows DLL/manifest travels with its exact checkout/release source, lock and mapping provenance; validate a fresh extracted artifact without compiler tools and prepare a reviewable local release archive without publishing it. Depends on T055.
- [ ] T057 [P] [US4] Finalize Windows sections in `README.md` and `docs/installation.md` for supported target, source/release acquisition, native Python and uv setup, scopes, all six workflows, activation/mapping differences, logs/exit codes/retained backups and repair limitations; replace the old blanket Windows exclusion only with evidence-qualified support wording. Depends on T056.
- [ ] T058 [P] [US4] Finalize native setup/build/local testing/CI/coverage instructions in `docs/development.md` and `docs/release-validation.md`, including exact locked prerequisites, x64/32-bit probes, Server versus Home/Pro evidence, workflow dependencies, manual restoration, `uv run --locked mypy src tools` for both local and CI type checking, and pending native blockers; document that unavailable platform evidence cannot count as a pass. Depends on T056.
- [ ] T059 [US4] Execute or obtain all five same-revision CI jobs, exercise a deliberate required-test failure and a missing/stale Windows artifact fixture, verify aggregation fails as intended, then obtain successful required static/tests/coverage results and record them in `specs/002-add-windows-11/validation/ci.md`; missing hosted execution stays pending. Depends on T057, T058.
- [ ] T060 [US4] Run every `specs/002-add-windows-11/quickstart.md` scenario from clean Home and Pro accounts without reading source and record exact environment/revision, commands, x64/browser/32-bit typing, sign-in persistence, old/current repair, all recovery outcomes, permissions, noninteractive behavior and VM cleanup in `specs/002-add-windows-11/validation/us4.md`; fix undocumented prerequisites/commands before marking complete. Depends on T059.
- [ ] T061 [US4] Run same-revision native regression and desktop checks for Ubuntu 24.04 GNOME X11/Wayland, macOS 15 Intel/Apple Silicon and macOS 26 Apple Silicon; carry forward and close only evidence-backed prior-feature blockers in `specs/002-add-windows-11/validation/regressions.md`, preserving existing layouts/commands and recording missing native access explicitly. Depends on T060.

**Checkpoint**: All required automation and native acceptance records pass; missing evidence is an explicit release blocker, not a checked-off task.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose / goal**: Complete cross-artifact consistency, performance review and final acceptance without publishing or claiming unverified compatibility.

### Implementation

- [ ] T062 Review recorded status/preview timing and diagnostics across scenarios in `specs/002-add-windows-11/validation/performance.md`; investigate the plan's 5-second warmed-VM budget excluding authorization, fix justified bottlenecks in `src/bg_dvorak_phonetic/platforms/windows.py`, and rerun affected safety/no-write tests for any changes; any change to code, assets, runtime or documented workflow invalidates earlier acceptance evidence and triggers the final T065 replay. Depends on T061.
- [ ] T063 Run final locked syntax, Ruff, formatting, `uv run --locked mypy src tools`, behavioral and combined native coverage checks, resolving type errors in new and changed production tooling; apply ShellCheck/PSScriptAnalyzer if any shell/PowerShell helper was introduced, recheck the official stable Python baseline before release as constitutionally required, and record results or an explicit upgrade blocker in `specs/002-add-windows-11/validation/final-checks.md` with any coordinated pin/lock changes in `.python-version`, `pyproject.toml` and `uv.lock`; changed pins or implementation invalidate earlier acceptance evidence and trigger the final T065 replay. Depends on T062.
- [ ] T064 Audit FR-001–FR-015 and SC-001–SC-006 against final code, contracts, commands and evidence in `specs/002-add-windows-11/validation/review.md`; review privilege/resource bounds, model constraints, v1 compatibility, mapping preservation and three-platform gates, then update `specs/002-add-windows-11/plan.md` and `specs/002-add-windows-11/quickstart.md` only for measured implementation corrections. Depends on T063.
- [ ] T065 Freeze the final candidate code, asset manifest, runtime/lock and documented workflows after T062–T064. Against that exact candidate, rerun the validation procedures of T059–T061 (all five CI jobs and the complete Home/Pro/Ubuntu/macOS desktop acceptance), refresh their evidence files, and create `specs/002-add-windows-11/validation/release.md` linking the new same-revision records, asset provenance and recovery evidence; if validation requires a substantive change, invalidate those records, freeze the corrected candidate and repeat this replay; mark any unavailable/failed requirement as a release blocker and leave this task unchecked until every required gate passes; do not publish, tag, or deploy a release. Depends on T064.

**Checkpoint**: Tasks are complete only with their artifacts and required evidence present. No release publication is included in this task list.

---

## Dependencies & Execution Order

### Phase and user-story graph

```text
Setup (T001–T004)
  -> native assets and proof (T005–T011) [hard gate]
  -> shared schema/resource foundation (T012–T021) [hard gate]
  -> US1 fresh install and typing (T022–T033)
  -> US2 inspection/update/repair (T034–T040)
  -> US3 recovery/failure handling (T041–T049)
  -> US4 CI/docs/release evidence (T050–T061)
  -> cross-cutting final gates (T062–T065)
```

The three P1 stories deliberately share the same adapter/worker/transaction files. Their implementation
is sequenced to avoid conflicting changes; independent tests seed their own state rather than relying
on another story's test run. US3 is not the first introduction of rollback: T019
provides the mandatory safe mutation foundation before US1. US3 completes public recovery and adversarial
acceptance. US4 integrates evidence across completed behavior; it cannot declare success from earlier
mock or Server-only results.

The native proof uses a documented controlled test registration, not the unimplemented product adapter;
this breaks the potential proof/installer circular dependency. Its manual steps must snapshot and restore
only test-owned resources, and a failed probe requires a measured contract revision before proceeding.

### Final evidence replay

T059–T061 establish an initial acceptance baseline. T062–T064 may still change implementation,
assets, runtime pins or documented workflows, so those earlier records cannot approve the final
candidate. T065 explicitly reruns the T059–T061 procedures after candidate freeze and replaces
the release evidence with results for that candidate. This is a validation replay within T065,
not a backward prerequisite edge. Any substantive correction during replay restarts the final
validation cycle. Evidence-only record additions may refer to the immutable tested candidate;
record the candidate revision and asset/runtime hashes rather than pretending they test later code.

### Parallel execution examples

| Story / group | Ready after | Tasks that can run together | Separate outputs |
| --- | --- | --- | --- |
| Setup | T001 | T003, T004 | Fixture factories and evidence protocol |
| Asset proof | Setup complete | T005, T006 | Reviewed expected fixture and asset contract tests |
| Foundation | T011 | T012, T013 | Model tests/v1 fixture and backend contracts |
| US1 | T021 | T022, T023, T024 | CLI, worker and fresh-install test files |
| US2 | T033 | T034, T035 | State contract and repair integration tests |
| US3 | T040 | T041, T042, T043 | Recovery contract, crash and worker-safety tests |
| US4 | T049 | T050, T051, T052 | Artifact gates, evidence models and documented commands |
| US4 docs | T056 | T057, T058 | User docs versus developer/release docs |

Each listed pair/group has different edited files. Unmarked tasks are sequential according to their
explicit dependencies. No parallelism is implied for live keyboard mutation or VM acceptance scenarios.

## Requirement Coverage

| Requirement | Primary tasks / gate |
| --- | --- |
| FR-001, FR-002: existing workflows and automatic action choice | T030, T037, T038, T044, T046 |
| FR-003: mapping preservation/reference | T005, T007, T008, T009, T011, T033 |
| FR-004: discovery/selection/input/persistence | T010, T011, T031, T033, T060 |
| FR-005: complete preflight | T009, T020, T022, T025, T026 |
| FR-006: explicit scope and least privilege | T023, T025, T028, T029, T043 |
| FR-007: preserve unrelated settings/no disruption | T017, T024, T030, T031, T033 |
| FR-008: state and no-write preview | T034, T037, T039, T044 |
| FR-009: bounded repair and ownership | T035, T036, T038, T040 |
| FR-010: no-op and concurrency | T018, T039, T043, T046 |
| FR-011: durable originals/recovery | T015, T019, T042, T045, T049 |
| FR-012: diagnostics/outcomes | T031, T047, T048 |
| FR-013: complete setup and workflow docs | T002, T032, T040, T048, T057, T058, T060 |
| FR-014: native automated coverage | T013, T021, T054, T055, T059 |
| FR-015: desktop and regression evidence | T011, T033, T049, T060, T061, T065 |

SC-001 is checked by T033, T040; SC-002 by T011, T033;
SC-003 by T040; SC-004 by T034, T049; SC-005 by
T060; SC-006 by T059, T061, T065.

## Implementation Strategy

### MVP first

Complete setup, prove native assets, preserve shared backend/v1 recovery, then finish US1 for a controlled
fresh-install/typing demonstration. Do not weaken baseline rollback, ownership, elevation or mapping
checks to make an earlier MVP. This milestone is a demonstration scope, not permission to release
without US2–US4 and the constitution's evidence gates.

### Incremental delivery

1. Prove build/ABI/mapping feasibility before expanding installation code; stop dependent work if the
   empirical design gate fails and correct the measured design first.
2. Preserve existing behavior while extracting the resource seam, with v1 journals as compatibility fixtures.
3. Demonstrate US1 on a clean machine; add US2 against independently seeded older/damaged fixtures.
4. Complete US3 recovery/transport/adversarial evidence, then US4 automation and clean documentation walkthroughs.
5. Run final native/static/coverage/release review. Keep unsupported or missing evidence pending, and leave
   publication outside this implementation task list.

## Validation Summary

- Total: 65 tasks; setup 4, foundation 17, US1 12, US2 7, US3 9, US4 12, polish 4.
- Parallel candidates: 19 tasks in the independent groups listed above.
- All tasks use an unchecked checkbox, sequential task ID, phase-appropriate story label, concrete file paths and explicit prerequisite references.
- All four story acceptance flows, all 15 functional requirements and all six success criteria have mapped work and evidence gates. Task generation does not establish implementation or compatibility.

## Implementation progress — 2026-09-19

T001 and independent T004 are complete; see validation/baseline.md and validation/README.md.
T002 is partially prepared: the lock and NOTICE explicitly record unavailable native tools,
with no invented versions, hashes or license provenance. It remains unchecked until native
acquisition/provenance is captured. On continuation, independent T003 was completed with portable safety tests and a
separate pending native registry test. Foundation/story tasks remain unexecuted. No Windows support or release readiness is claimed.

T003 continuation: added isolated temporary file and unique HKCU Software registry factories,
file/value snapshot restoration, cleanup, and internal fault hooks. Portable checks pass;
registry behavior still needs the collected Windows-only test. T002 remains the prerequisite
blocking T005 onward; no native build or desktop gate was waived.

User-directed CI continuation: use GitHub Actions for available native Windows validation.
An early standalone prerequisite workflow runs T003 fixtures and captures T002 tool inventory
on Windows Server 2025 x64 and Windows 11 ARM64. It does not complete T054, expand architecture
support, or waive T011's Home/Pro x64 desktop proof. Local Windows availability is no longer
required for the hosted checks.

Hosted prerequisite run 35467757790 passed: 12 fixture tests passed and one non-Windows-only
test skipped on each of Windows Server x64 and Windows 11 Enterprise ARM64. T003 native
fixture execution is now evidenced in validation/hosted-prerequisites.md. T002 remains partial:
measured inventory exists, but package/provenance/build-lock requirements are not all satisfied.

T002 completed after native run 35468187758: exact VS/compiler/linker/MSBuild versions,
72 compiler input hashes, SDK/WDK package acquisition URLs/versions/hashes and pinned sample
MS-PL provenance are recorded. The input lock is ready; this does not claim a built layout.
Earlier pending T002 notes above are historical and superseded by this measured capture.

T005–T007 completed: independent full mapping oracle, test-first build/asset contracts (initial
missing-module failure observed), and source-derived scan/VK/modifier/composition manifest.
See validation/mapping.md. T008/T009 are in progress; no native layout build claimed yet.
