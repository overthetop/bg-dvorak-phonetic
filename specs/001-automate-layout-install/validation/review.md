# Implementation review

Reviewed source, adapters, worker, contracts, tests, CI, documentation, and FR-001–FR-020.

Findings fixed:

- uv's --no-sync launch created missing environments. The documented explicit interpreter and
  --no-project launch refuses missing setup without creation. Contract/plan correction records
  the measured behavior; environment preflight remains read-only.
- Shared workflow originally contained Linux authorization details. Native recovery transport
  now belongs to adapters; common policy retains consent and ordering. Transaction locks and
  filesystem replacement boundaries are injectable; the fake adapter verifies extension.
- State-to-action selection is centralized, unsafe state cannot produce an apply plan, and
  every diagnostic in a run uses the same generated ID.
- Interrupted worker outcome could be mistaken for cancellation without mutation. Unknown
  apply/recovery outcomes now report exit 5 and a recovery location.
- Restoration now records phase before renaming displaced content. Fault tests exercise a crash
  between displacement and restore; external edits and changed staging objects are refused.
- Backup files and directory entries are flushed before mutations; backups are rehashed before
  applying. Source hashes and all observed destinations are revalidated under the lock.
- Worker source hashes are checked again after independent planning; fixed system destinations
  require root ownership and no group/other write permission. User-scope originals with another
  owner are refused because their ownership cannot safely be restored without elevation.
- A macOS duplicate with only one matching native identifier is a conflict, not an unrelated
  layout. Damaged identities require a remaining match or a trusted successful receipt.
- XML 1.1 keylayout control references are normalized only for structural validation, never in
  installed bytes. Malformed XML and invalid journal types receive classified failures.
- Native validator stderr is retained in actionable diagnostics; credential forms are redacted.
- Initial journal publication failure now permits safe retry when the protected generated run
  directory contains only abandoned initial journal staging; unexplained retained files still
  require recovery. Explicit restoration failures and failed recovery-journal updates preserve
  exit 5, even when storage errors prevent recording a newer phase.
- Build backend now uses minimal uv_build 0.12.16, pinned in project metadata and uv.lock.

All original layout assets remain unchanged. No shell product launcher, dynamic plugin loader,
Windows implementation, updater, or desktop preference mutation was introduced. Imports are safe;
native dependencies are loaded only when selected. Recovery copies retain original bytes/modes
and scoped ownership, and successful backups remain until explicit cleanup.

Evidence limits: native Linux uses temporary destinations and actual xkbcli. Native macOS,
privileged live desktop installations, hosted matrix aggregation, and manual typing remain pending.
These limits are retained in open tasks and are not inferred from portable tests.
