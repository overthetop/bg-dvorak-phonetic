# Data Model: Windows 11 Support

## Layout manifest

Fields: schema version, `layout_id=bg-dvorak-phonetic`, project revision, mapping revision/hash,
Windows KLID, Layout Id, display name/resource ID, supported build family/editions/architecture,
asset list (relative path, SHA-256, PE machine type, export name, content-addressed installed
basename), and build provenance (compiler/kit versions, input hashes).

The manifest belongs to the acquired project version. Relative paths must stay within its asset
root, reference regular non-reparse files, and contain no alternate data streams, device names,
parent traversal, or absolute paths. Reject case-insensitive duplicate names. The DLL must match
the x64 ABI and expose `KbdLayerDescriptor`; export checks do not substitute for native typing.
The manifest digest is integrity evidence within a trusted release, not a publisher signature.
Linux/macOS inventories remain valid without Windows build products on non-Windows runs.

## Mapping case

Fields: physical key (XKB position and Windows scan code), virtual key, modifier set, Caps behavior,
expected Unicode output or named dead-key state, and source position/level. Dead-key cases add
next input and expected result. Every explicit Linux symbol has a Windows case or an explicitly
reviewed platform difference. ASCII control/navigation expectations are recorded separately.
A complete expected-output fixture is independently reviewed; do not test a generator only against
its own generated tables. See [mapping contract](contracts/windows-layout.md).

## Windows registration

Fields: registry hive/view, KLID subkey, typed values `Layout File`, `Layout Text`, `Layout Id`,
`Layout Display Name`, complete observed value/subkey snapshot, and security descriptor.
A registration references one immutable installed asset revision. Treat registry key/value names
case-insensitively. Snapshot ordering is canonical, but raw value types and content are preserved.

Ownership: a protected prior receipt or matching released project identity and known asset hash
can establish ownership. Display names alone cannot. Missing or corrupt components are repairable
only when surviving identity plus trusted evidence bounds the resources to this project. Unexpected
subkeys/values, mismatched identity, or another registration referencing a proposed removable DLL
block destructive replacement. Registration ID collisions are unsafe, not a request to allocate
a new identity silently. Receipts track historical project revisions for upgrades and restoration.

## Installation state

Retain `Health`: absent, current, outdated, repairable, unsafe. Include the installed manifest,
owned resource IDs, registration snapshots, conflicts, and activation status. Pending transaction
IDs are an independent recovery overlay; they take precedence over no-op or fresh work.

| Observed condition | State / next action |
| --- | --- |
| No registration, files, or receipts | absent / install |
| Exact current identity and complete hashes | current / no-op |
| Complete known earlier revision | outdated / update |
| Bounded missing/damaged/duplicate project components | repairable / repair |
| Unknown ownership, conflicting identity, unsafe path or ACL | unsafe / refuse |
| Unfinished journal regardless of asset health | recovery required / describe or restore first |

Unreferenced retained old DLLs are recovery assets, not duplicate effective registrations.
Activation remains pending/unknown; installed files alone never prove currently active input.
Inspection denied or unreadable means incomplete inspection, never absent/current.

## Resource operations and change plan

Preserve schema-v1 `FileOperation` and POSIX plans. Introduce schema-v2 Windows plans with a
discriminated union of file and registry operations; never encode a registry path as `Path`.

Common fields: resource ID, operation kind, before fingerprint/absent, after fingerprint/absent,
observed security descriptor fingerprint, and ownership evidence reference. File operations add
canonical destination, staged asset digest, backup reference, and retained ACL metadata. Registry
operations add fixed hive, view, bounded subkey, exact typed before/after snapshots, and key-created
flag. Only project resource types are permitted; plans contain no executable commands.

Plan fields retain run UUIDv4, platform, scope, action, source hashes, observed snapshots,
validation results, schema version, and a canonical digest over the approved operations. Registry
changes appear as distinct resource summaries in output. A no-op has no operations and causes no
state creation. Update order is files first, then registration; old files remain available.

## Recovery record

Windows schema v2 includes platform/scope, canonical run UUIDv4, original request digest,
source/installed revision, phase, resource snapshots and backup hashes, expected post-state,
intent step, completed steps, retained resources, timestamps, and any recovery diagnostics.
Snapshots preserve absent vs present-empty, registry value types, unknown observed values, and
security descriptors. Backups and journal live under the protected state root; no arbitrary paths.

Existing v1 POSIX records remain readable and recoverable without rewriting them. New Windows
records cannot be consumed by an older binary; unknown versions fail safely. Test v1 compatibility
before accepting the shared transaction refactor.

State transitions:

```text
prepared -> applying -> verified -> committed
    |           |           |
    +-----------+-----------+-> rolling_back -> restored
                                     |
                                     +-> recovery_required -> rolling_back
```

Persist originals and operation intent before each mutation. A crash after a write but before its
completion marker is reconciled from observed before/after snapshots, not the completed list alone.
If neither matches, stop with recovery-required. Recovery validates all relevant resources before
restoring any, reverses applied operations, verifies the restored state, and persists its outcome.
Never delete backups on successful install. Repeated recovery of a restored record is read-only.

## Validation evidence

Extend existing validation records with Windows edition/build, process/native architecture, shell,
asset/mapping/build revisions, x64/32-bit application identity, Secure Boot/policy context, scenario,
commands, exit code, diagnostics, before/after evidence, and restoration result. Record CI runner
identity separately from product target. A desktop record must identify manual or automated actual
input evidence; a Server job cannot satisfy it. All release evidence refers to the release revision.
