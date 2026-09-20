# Research: Windows 11 Support

**Date**: 2026-09-19 | **Status**: Design decisions resolved; native proof remains implementation work.

## 1. Supported platform and runtime

**Decision**: Target Windows 11 25H2 Home and Pro, native x64, build family 26200.
Test both editions at the cumulative update current when release evidence is collected.
Reject other build families, Server, ARM64, and 32-bit installer processes before mutation.
Retain Python 3.14.7 (`>=3.14.7,<3.15`) and uv 0.12.16 from the repository.
Use native PowerShell 5.1 or 7 for documented commands, with `.venv\Scripts\python.exe`;
Git Bash, WSL, MSKLC, and a `py` launcher are not user prerequisites.

**Rationale**: A narrow explicit target is testable. Microsoft's release table lists 25H2
Home/Pro servicing through October 2027, while 24H2 ends in October 2026. The Python release
index identifies 3.14.7 as the current stable maintenance release. Recheck before release.

**Alternatives considered**: Every Windows 11 version (unsupported evidence burden), 24H2
(short remaining servicing period), ARM64 (outside spec), runtime upgrade (not presently needed).

Sources: [Windows release information](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information),
[Python releases](https://www.python.org/downloads/).

## 2. Native layout assets and build

**Decision**: Generate a native x64 keyboard-layout DLL from reviewed mapping data, using
Microsoft's layout sample as the table/export ABI reference. Use the VS 2022 17.14 toolchain
and the matching SDK/WDK 26100.6584 release, acquired explicitly for maintainers/CI.
Record exact compiler version, kit package versions, source revision, and hashes in the asset
manifest; implementation must commit the build lock and fail rather than silently use another kit.
End users receive prebuilt assets with the matching project release; installation never compiles,
downloads, or upgrades tools. A source checkout without built assets fails with preparation guidance.

**Rationale**: A layout DLL integrates with ordinary Windows text input without a resident
remapper. Microsoft provides a native sample; MSKLC's download page does not establish Windows
11 compatibility. The WDK compatibility table identifies 26100.6584 as a VS 2022-compatible kit.
The small generated C table/export shim is a native asset, not installation logic; all product
installation/update/repair behavior remains Python.

**Alternatives considered**: MSKLC as a user prerequisite (legacy tooling), key interception
service (different behavior and scope), an IME (unnecessary complexity).

Sources: [Microsoft layout sample](https://github.com/microsoft/Windows-driver-samples/tree/main/input/layout),
[WDK versions](https://learn.microsoft.com/en-us/windows-hardware/drivers/other-wdk-downloads),
[MSKLC](https://www.microsoft.com/en-us/download/details.aspx?id=102134).

**Implementation proof gate**: Before building the full installer, prove the DLL's discovery,
selection, and text output on a disposable 25H2 desktop, including a 32-bit text-input probe.
Ship an x64 DLL as the selected architecture. Do not blindly install an ordinary x86 DLL into
SysWOW64: the selected headers and native probe must establish any required compatibility ABI.
If native x64-only deployment fails the 32-bit probe, stop dependent implementation and revise
this asset contract with the measured requirement; do not claim compatibility or silently exclude
32-bit applications. This is an engineering validation gate, not an unresolved product choice.
Use unique project files; do not follow legacy sample advice to overwrite built-in layouts or
disable Windows protection. Validate with normal Windows security settings, including Secure Boot.

Source: [Windows filesystem redirection](https://learn.microsoft.com/en-us/windows/win32/winprog64/file-system-redirector).

## 3. Mapping authority

**Decision**: Use `linux/symbols-bg-dv` as the Windows character-position authority, with a
reviewable UTF-8 mapping manifest and expected-output fixtures. Preserve all explicit levels:
base, Shift, AltGr, Shift+AltGr. Resolve the existing macOS differences explicitly rather than
asserting all platform layers are identical. See [mapping contract](contracts/windows-layout.md).

**Rationale**: Local inspection found common Bulgarian letter positions, but different punctuation
and modifier layers. Linux has grave/tilde at TLDE and Bulgarian quotation marks at shifted AD02/AD03;
macOS has ч/Ч at ANSI key code 50 and quotation/equal characters at those shifted positions.
macOS Option contains a Latin QWERTY layer and its Caps layer changes some punctuation.
The Linux source expresses portable physical positions and all intended extra Cyrillic symbols.

**Alternatives considered**: Copying macOS Option/Command behavior (platform-specific), limiting
support to base letters (loses supplied mappings), changing existing platform assets (outside scope).

## 4. Scope and installation mechanism

**Decision**: Use explicit system scope for Windows files and layout registration, with manual
per-user activation. The Python adapter manages only project DLLs under the native Windows
system directory and one project registration under
`HKLM\SYSTEM\CurrentControlSet\Control\Keyboard Layouts`. No user-scope installation.
Use a project-specific KLID candidate `A0D00402`, layout ID candidate `0D00`, and display name
`Bulgarian (Dvorak phonetic)`. Candidates become release identities only after the native proof;
any pre-existing unrelated identity or Layout Id collision causes refusal, never takeover or
silent reassignment. Ownership requires trusted project evidence, not a matching display name.

**Rationale**: A native layout needs machine registration but selecting it belongs to the user.
Direct bounded file/registry operations retain the project's Python transaction and recovery model.
The native registration model is documented by Microsoft; choosing direct operations instead of
MSI is a project design inference and must be validated by the native proof gate.

**Alternatives considered**: MSI (good OS integration, but introduces another installer state
machine and ownership database alongside recorded recovery), per-user remapping (not the same
native layout), editing built-in registration (unsafe and contrary to requirements).

Sources: [Layout registry metadata](https://learn.microsoft.com/en-us/windows/win32/intl/using-registry-string-redirection),
[Layout loading](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-loadkeyboardlayoutw).

## 5. Portable workflow and native resource boundary

**Decision**: Retain shared action selection, consent, diagnostics, and transaction phase ordering.
Introduce a narrow resource backend for snapshot, stage, apply, verify, restore, state storage,
and locking. Preserve existing POSIX behavior as the default. Windows supplies registry snapshots,
ACL checks, handle-based locks, and durable file operations. Add typed registry operations and a
Windows journal schema v2; continue reading/recovering existing schema-v1 POSIX journals.

**Rationale**: Repository inspection found `fcntl`, `getuid/geteuid`, Unix ownership/modes,
`O_NOFOLLOW`, and directory `fsync` in `transaction.py`. Windows cannot safely emulate these by
ignoring errors. `workflow.inventory` is also hard-coded to Linux/macOS, and result formatting
assumes every operation has a filesystem destination. These are concrete extension seams.

**Alternatives considered**: Copying the transaction engine into a Windows module (policy drift),
pretending registry keys are files (ambiguous validation), platform-conditionals everywhere
(weak boundaries), an extensible plugin framework (unnecessary).

## 6. Authorization and trust

**Decision**: Keep the public process unelevated; launch a restricted Python worker through the
Windows elevation interface for protected inspection or mutation. Only fixed actions and validated
run IDs cross the boundary. Recompute the plan and compare its digest inside the worker. Use an
ACL-restricted, nonce-bound local IPC exchange; no arbitrary command or destination supplied by
clients. Never elevate uv or accept user-supplied registry scripts. `--yes` does not grant UAC
consent. A noninteractive unelevated caller fails promptly rather than displaying an unusable prompt.

**Rationale**: OS authorization and project plan consent are separate. Protect snapshots and
recovery state from modification by nonadministrators, including a different requesting user.
The user must trust the acquired project code, runtime, and asset manifest; a checksum alone is
not a publisher signature. A worker must use a validated stable code snapshot for the operation,
not import newly changed modules midway through privileged execution.

**Alternatives considered**: Running the full CLI or dependency manager as administrator (too
broad), persistent privileged service (unnecessary), unrestricted subprocess requests (unsafe).

Sources: [ShellExecuteExW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shellexecuteexw),
[Execution parameters](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-shellexecuteinfow).

## 7. Recovery and loaded files

**Decision**: Use immutable, content-addressed DLL filenames for new versions. Stage new files
before switching the registration value; retain prior files for rollback. Do not overwrite or
schedule deletion of a loaded DLL, schedule reboot work, or automatically unload a user's layout.
Recovery reverses registration first and removes only verified new unreferenced files; if Windows
keeps one locked, retain the record as recovery-required and provide manual sign-out/retry guidance.
An unchanged install creates neither a lock file nor backups. Preview/inspection create no durable
state. State resides under the native ProgramData known folder in `bg-dvorak-phonetic` with a
protected DACL permitting Administrators and SYSTEM only.

**Rationale**: Versioned files avoid most in-use update failures without claiming active applications
have reloaded the layout. Journals capture complete before/after snapshots and uncertain writes.
Windows path guards reject junctions and all reparse points, not just symbolic links. Use native
flush semantics and write-through journal replacement; do not treat POSIX modes as Windows ACLs.

**Alternatives considered**: In-place overwrite (loaded-file failure), automatic reboot/pending
rename (disruptive hidden state), deleting all old versions (breaks recovery).

Sources: [Reparse points](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points),
[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).

## 8. Validation and CI

**Decision**: Add a native `windows-2025` job using PowerShell and keep all four existing Linux/macOS
jobs. Build native assets explicitly; use real Windows filesystem/registry operations against
isolated temporary files and test-owned registry subkeys. Exercise elevation/real registration in
a controlled Windows 11 VM. Update the artifact collector to require all five same-revision jobs
and exact unrounded line coverage greater than 80%, with branch and missing-line reports.
Record Home and Pro desktop evidence separately and carry forward existing Linux/macOS blockers.

**Rationale**: GitHub's Windows 2025 runner is Windows Server, so it provides useful native API/build
evidence but cannot prove the Windows 11 desktop claim. Product detection must continue rejecting
Server; tests inject a fixture context without adding a public override flag.

**Alternatives considered**: Treating hosted Server as Windows 11 (false claim), WSL testing
alone (does not exercise Windows host integration), public-PR execution on privileged persistent
self-hosted desktops (unnecessary exposure).

Source: [GitHub Windows runner image](https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-Readme.md).

## Resolution summary

Platform, scope, tooling, mapping authority, resource contracts, authorization, recovery, and CI
strategy are selected. No product clarification is outstanding. ABI, signing/policy compatibility,
actual Settings discovery, and crash recovery require empirical acceptance evidence before release;
they are explicitly ordered implementation gates, not presumed successes.
