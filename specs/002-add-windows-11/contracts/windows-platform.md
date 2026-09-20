# Windows Platform and Resource Contract

## Integration with existing code

Register `win32 -> windows` in CLI detection and `WindowsAdapter` in the static lazy registry.
Keep the existing PlatformAdapter methods and RecoveryAccess guarantees. Extend asset inventory
with a selected-platform argument defaulting to existing behavior for compatibility. Inventory
Windows source/build assets only when Windows is selected; Linux/macOS must not require a Windows
compiler or DLL. Keep runtime environment validation read-only, including Windows editable-install
URI and case/path normalization checks.

Add an injected resource backend to the shared Transaction engine with the existing POSIX backend
as default. Windows `apply_authorized` invokes the same engine in its protected worker using the
Windows backend. Existing Linux/macOS adapters and journals retain their observable behavior.
Backend responsibilities are resource snapshot, stage, apply, postcondition verification, restore,
protected state storage, and lock acquisition. Shared code retains phase ordering, failure handling,
and recovery policy. Registry operations are typed values, never shell commands or pseudo-file paths.

## Probe, inspection, and planning

- Verify native x64 process and host, Windows client Home/Pro edition, version 25H2/build 26200,
  and explicit system scope for mutation. Derive Windows/ProgramData paths through native system
  interfaces, not untrusted environment variables or a hardcoded C drive.
- Validate manifest, known project identity, DLL hashes/PE architecture/exports and runtime before
  privileged writes. No compilation or downloads inside product commands.
- Inspect the native registration view and both identity and references to project files. Detect
  duplicates by proven ownership, never display-name similarity. Leave unknown registrations alone.
- Read trusted receipts to attribute incomplete/damaged installations. No trustworthy evidence
  means conflict rather than destructive repair. Refuse unexpected registration contents where
  replacement would discard unknown data.
- Pure inspection and planning allocate no persistent installation/state resources. Protected
  read access is authorized separately and never calls mutation code or creates a lock file.
- Build a canonical plan with source hashes, complete before snapshots, concrete resource actions,
  and intended after snapshots. Display registry as well as file changes to the user.

## Fixed mutation resources

Allow only manifest-validated project DLL basenames under the native System32 directory, the
selected project KLID subkey beneath the native HKLM Keyboard Layouts branch, safely identified
project duplicate subkeys, and the protected project ProgramData state root. No entire shared
registry subtree restore/import. Do not touch user language lists or registration of built-in layouts.

The project registration contains `Layout File` (basename), `Layout Text`, `Layout Id`, and
`Layout Display Name` (resource reference to the same DLL). Check KLID and Layout Id collisions
against existing registrations. Use explicit registry view selection, even from a native process.
Resource display names and registry paths are presentation data, not executable input.

File names use a project prefix plus content digest, e.g. `bgdv_<digest>.dll`; the manifest records
the exact basename. Reject any existing file under that basename with different content. Previous
versions remain until explicitly eligible recovery retention cleanup; cleanup is not part of this
feature's installer. No-op runs must not create new retained state.

## Worker authorization

The normal CLI performs input parsing, source validation, planning, and user consent. Elevate only
the fixed Python worker through ShellExecuteExW/runas. Launch the explicit prepared x64 interpreter
with isolated mode and bytecode writes disabled, never uv, a shell command string, or a PATH-resolved
executable. Quote Windows process arguments with tested Windows rules, including spaces/Cyrillic.

Request schema: protocol version, fixed action (`inspect`, `apply`, `recover-preview`, `recover`),
canonical run ID when relevant, expected plan digest, source-manifest digest, and request nonce.
Reject unknown fields, unbounded payloads, arbitrary paths, scripts, commands, and invalid IDs.
Use local named-pipe IPC with a restricted DACL for the requesting SID, SYSTEM, and Administrators;
reject remote clients and authenticate peer/process identity plus nonce. Bind results to the request;
untrusted pipe messages never authorize writes.

The worker reconstructs native roots, validates its stable code/asset snapshot, obtains its own
resource observations and recomputes the approved plan. Any digest/state mismatch returns 4 before
installation changes. The trusted distribution and Python runtime remain an explicit trust boundary;
a privileged worker cannot make arbitrary untrusted checkout code safe. Validate/stage a stable
private worker-code snapshot before importing optional project modules, and abort on changes.
No persistent worker service, scheduled task, credential storage, or broad registry privileges.

Wait with a bounded launch/IPC timeout and report UAC cancellation as 3. If a worker times out or
its parent disappears during mutation, retain/finish recovery independently; the parent must not
claim no changes just because transport failed. Correlate by run ID and inspect durable state on
retry. `inspect` and `recover-preview` cannot create durable state or a code staging directory;
use an in-memory verified snapshot for read-only execution.

## Windows backend safety and durability

- Create state under the ProgramData known folder with protected DACL granting SYSTEM and
  Administrators only. Validate owner/DACL for every existing state, backup, and lock object.
  Preserve relevant original file/registry security descriptors. Reject unsafe inherited access.
- Use handle-based, exclusive nonblocking locking on a stable protected lock file for mutation;
  a crash releases the OS lock. Obtain it before re-reading snapshots and planning any writes.
  Inspect/preview uses no new lock file. Recheck pending transactions under the lock.
- Reject all reparse-point ancestors, junctions, unexpected hardlinks, alternate data streams,
  device paths, ambiguous case aliases, and destinations outside the fixed resource set. Validate
  final handle paths and identities to close path-replacement races; string prefix checks are insufficient.
- Preserve and flush backups and write-ahead intent before mutation. Use Windows-native durable
  journal replacement and flush checks, including registry flush at transaction boundaries. If the
  backend cannot establish a required durable step, fail before further changes; do not swallow
  unsupported POSIX operations or promise whole-transaction atomicity.
- Stage verified immutable DLL content on the destination volume. Switch the registration only
  after all required files exist and validate. Verify resulting file/registry snapshots before commit.
  Do not load DLLs or activate a layout in the elevated process merely to claim typing success.
- Roll back reverse order. Compare current content/types/security with recorded before/after
  states, including an uncertain last step. A third state causes recovery-required without overwrite.
  Retained previous DLLs enable registration restoration without rewriting loaded files.
- Remove a newly created file only if its identity/hash and absence of external registration
  references are verified. A loaded/locked file or external edit retains recovery-required state.
  Never queue hidden reboot work, forcibly unload keyboards, or restart applications/sessions.

## Required backend contract checks

Run the same phase/intent/recovery checks against POSIX and Windows resources. Include failure at
every durable-step boundary, write-success-before-marker crashes, registration write failures,
read-only inspection, DACL refusal, junction/hardlink attacks, changed snapshots, external registration
references, duplicate identities, simultaneous processes, parent/worker transport loss, stale nonces,
and v1 journal compatibility. Use real temporary Windows files and test-owned registry keys for
native API checks, with production roots impossible to select via public test flags.
