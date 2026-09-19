# Data Model: Installation and Recovery

All models are typed Python dataclasses/enums. No database is required. Persistent journal JSON
uses schema_version=1 and explicit UTF-8; unsupported schemas are refused without mutation.

## Entities

| Entity | Fields | Rules and relationships |
|---|---|---|
| PlatformContext | os_id, os_version, architecture, session_type, scope, project_root, destination_roots, state_root | Validated support matrix; canonical roots determined by adapter; no user-supplied arbitrary root in production |
| LayoutAssets | layout_id, project_revision, relative_paths, SHA-256 file manifest, native_identifiers | Source must be complete and validate; hashes, not bundle version alone, determine updates |
| InstallationState | health, installed_manifest, registrations, owned_paths, conflicts, activation | health: absent/current/outdated/repairable/unsafe; only project identities count as registrations |
| ChangePlan | schema_version, run_id, platform, scope, action, operations, observed_hashes, source_hashes, validation_results | Immutable after authorization; install/update/repair/noop; unsafe state yields no apply plan |
| FileOperation | kind, destination, before_hash_or_absent, after_hash_or_absent, staged_path, backup_path, metadata | Restricted destinations; replace/create/remove-owned-duplicate; no arbitrary commands; symlinks rejected except verified distro registry alias |
| RecoveryRecord | run_id, schema_version, scope, phase, ordered_operations, completed_steps, retained_originals, timestamps | Persist before each mutation; protect permissions; durable step transitions; backup ownership matches scope |
| RunResult | run_id, action, installation_status, activation_status, changed_paths, warnings, recovery_id, next_steps, exit_code | Installation success never implies active keyboard selection |
| DiagnosticEvent | timestamp_utc, run_id, level, stage, message, operation, path, cause, remedy | Ordered stderr messages; no credentials; traceback only in debug mode |
| ValidationRecord | commit, os/runtime versions, architecture, scenario, result, diagnostics, coverage_artifact, manual_evidence | Same-commit artifacts for combined coverage; missing required evidence is not success |

## Identity and ownership

Linux: symbols block named bg-dvorak-phonetic inside symbols/bg; registry entry with that exact
name under the unique layout whose configItem/name is bg. Similar names elsewhere are unrelated.
A malformed unbounded block cannot establish safe replacement spans.

macOS: canonical project bundle with matching CFBundleIdentifier and TISInputSourceID from
the supplied assets. A trusted prior receipt or remaining matching identity can establish
ownership of damaged files; a conflicting identifier blocks overwrite. Empty destination
directories may be repaired. Duplicates must share the exact identity, not just display name.

A manifest records byte hashes and relative paths; metadata records modes and ownership needed
for restoration. Backups of shared files retain all original bytes. Unrelated data is preserved.

## State transitions

1. Inspect: absent -> install; current -> noop; outdated -> update; repairable -> repair.
   Unsafe/conflicting/unsupported -> refused with no installation mutation.
2. Preparing: validate assets/prerequisites and inspect pending recovery before producing a plan.
   Protected Linux journal reads require authorized read-only worker access. Status/dry-run report
   pending recovery without restoring it; an actual install restores it before planning new work.
3. Authorized: scope consent and required privilege established.
4. Locked: exclusive scope lock acquired; before hashes and source hashes rechecked.
5. Prepared: backups, journal, and staged native validation complete.
6. Applying: each completed operation recorded before moving to the next.
7. Verified: installed manifest and native validation match plan.
8. Committed: final result and retained recovery record written, lock released.
9. On failure after mutation: rolling_back -> restored or recovery_required.
10. A subsequent invocation detects applying/rolling_back/recovery_required before new work;
    mutation requests restore verified originals or refuse unsafe intervening edits. Read-only
    requests preview recovery only; inaccessible protected state yields an inspection error.
11. Interruption returns 130 before mutation or after successful restoration; unresolved
    recovery_required state returns 5 even when interruption caused it.

Activation is orthogonal: pending or unknown until manually confirmed. No automatic session
switching or persistent claim of active typing. Successful file installation can return exit 0
with activation=pending and explicit instructions.

## Persistence and cleanup

Linux system state: /var/lib/bg-dvorak-phonetic, owned by root, directory mode 0700.
macOS user state: ~/Library/Application Support/bg-dvorak-phonetic, user-owned, mode 0700.
Authorized Linux read-only worker access inspects these protected records without changing their
permissions or creating state/lock files. No journal access means inspection is incomplete, not clean.
Journals and backup metadata use mode 0600. Backups of layout resources preserve restoration
metadata and are not exposed as additional discoverable keyboard bundles.

Store run IDs as generated identifiers, never user-controlled path fragments. Recovery selects
an ID within the known state root, validates all recorded destinations and hashes, and cannot
read arbitrary journal paths. Retain successful-change backups until documented explicit user
cleanup; do not create a new backup for noop. Cleanup must never delete unfinished transactions.
