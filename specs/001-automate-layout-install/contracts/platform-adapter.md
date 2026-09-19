# Platform Adapter Contract

A small typed Python Protocol separates native operations from shared workflow policy.
Registration is a static mapping from supported platform IDs to adapter factories.
No dynamic plugin discovery or third-party extension loading is needed.

## Operations

| Operation | Input | Output / guarantee |
|---|---|---|
| probe | OS facts, requested scope | Validated PlatformContext or UnsupportedEnvironment; no writes |
| validate_assets | Context, LayoutAssets | Native/structural validation evidence or actionable failure |
| inspect | Context, filesystem reader | InstallationState and content snapshot; protected journal reads may use an authorized read-only worker; no writes |
| plan | State, assets | Bounded ordered FileOperations; no writes; no-op has no operations |
| validate_staged | Context, staged candidate | Native validation evidence; never activates keyboard |
| acquire_lock | Context | Exclusive scoped lock with deterministic release; contention is an error |
| apply_authorized | Validated ChangePlan, transaction engine | Executes shared engine at required privilege, using only scoped operations |
| verify_installed | Context, expected manifest | Verified installation or failure triggering shared recovery policy |
| activation_guidance | Context, result | User-facing supported steps without changing input preferences |

The shared workflow chooses action, coordinates events, and owns recovery policy. Adapters define
platform identities, supported scopes, paths, validation, locking, and privilege transport.
Filesystem and command runners are injected for tests. A common transaction engine interprets
bounded data operations; platform-specific rename/metadata details may be behind a small filesystem
interface rather than repeated workflow code.

## Invariants

- Pure inspection/planning never creates backup, lock, journal, or destination files.
- Protected journal inspection may require authorization; unavailable access is an error, not a
  clean state. Revalidate under the mutation lock after any read-only preview.
- Native imports are confined to their adapter and loaded only when selected.
- Linux/macOS share outcome and error meanings from cli.md and models from data-model.md.
- Every mutation is journaled; destination snapshots are rechecked under lock.
- External command arguments are lists, with checked exit codes and validator timeouts.
- Unsupported platforms fail before mutation; shared code remains importable without their APIs.
- Input source selection is never an adapter side effect.
- Validators reject malformed source and preserve legacy mapping identifiers.
- Project-owned duplicate removal cannot cross scope or match only a display name.

## Contract tests

Run shared tests for absent/current/outdated/repairable/unsafe states, mutation-free dry runs,
identical repeated results, injected errors, preserved unrelated data, recovery outcomes, and
diagnostic guarantees on both OS families. Linux/macOS native integrations additionally exercise
their real filesystem/validator paths in temporary locations.

A test-only third adapter implements the contract using fixtures and proves that registration,
assets and adapter implementation are enough to participate in the shared install/update/repair
workflow. Existing adapters and shared policy must not need editing for this test.
This is extensibility evidence, not a Windows compatibility test.

## Adding Windows later

Provide a Windows adapter, scoped filesystem/lock/privilege behavior, native layout assets,
identity rules, activation guidance, contract/native tests, and a Windows CI job. Update the
supported matrix and documentation. The current feature creates none of these Windows artifacts.

## Recovery transport boundary

The nine operations are supplemented by `recovery_access(context, assets)`, which returns a
small native transport exposing `requires_authorization`, `pending()`, and
`restore(run_id, dry_run=...)`. Shared workflow requests consent and owns recovery ordering;
Linux sudo transport and user-local access are adapter choices. Transactions accept injected
lock factories and filesystem replacement boundaries for fault tests.
