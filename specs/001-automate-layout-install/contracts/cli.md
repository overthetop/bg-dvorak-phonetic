# CLI Contract

The console command is bg-dvorak-phonetic. Prepare the environment explicitly with
uv python install 3.14.7 and uv sync --locked --dev before launching product commands.
The checkout invocation is uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic.
These flags disable environment synchronization, Python downloads, and uv network access;
they do not establish that an existing environment is current. Read-only preflight must verify
the prepared project environment, the pinned interpreter, and installed runtime dependencies
against project metadata and uv.lock. Missing or stale prerequisites must fail with the explicit
preparation commands, without provisioning an environment, falling back to a global installation,
or modifying the runtime. These are requirements for the implementation to be built.

## Commands

| Command | Behavior |
|---|---|
| install | Default when no command supplied; detect and install/update/repair/noop |
| status | Read-only inspection; show health, scope, conflicts, activation and next action |
| recover RUN_ID | Restore a known transaction from its protected state directory |
| --help / --version | Print help/version without OS mutation or privilege escalation |

Common options after the subcommand: --scope user\|system, --dry-run, --yes, --verbose.
--dry-run applies to install/recover: inspect and validate, show proposed action, and make no
writes to installation or recovery-state roots. On Linux, inspecting protected journals may
require authorization for the restricted read-only worker, including during install/recovery
previews and status. An inaccessible journal is not evidence of a clean state: fail with exit 3
and explain that inspection is incomplete when authorization is unavailable.
--yes accepts the displayed plan without a prompt;
it does not select system scope or bypass OS authorization. Logs go to stderr and can be
redirected; no persistent log file is required by default. stdout contains the final concise
result or help/version output. ANSI color is unnecessary.

macOS defaults to user scope; --scope system fails as unsupported.
Linux install requires --scope system; omission explains the scope and exact command to retry
without mutation. Linux status defaults to system scope; explain and obtain consent before
requesting authorization to inspect protected journals. Read-only worker access cannot create
journals, backups, lock files, or other installation/recovery state.
Noninteractive runs requiring confirmation fail promptly unless --yes is supplied.
A noninteractive privilege worker uses noninteractive authorization and fails if unavailable.

## Observable outputs

Progress stages: preflight, inspect, plan, authorize, backup, validate-staged, apply,
verify-installed, complete; recovery adds restore and verify-restored.
Each diagnostic identifies severity and stage; failures name operation/location, known cause,
and next action. Debug mode may include a chained traceback, never credentials or full environment.

Final result states action=installed/updated/repaired/unchanged/restored/refused/failed and
activation=pending/unknown, with changed locations, recovery ID/location when applicable, and
concrete next steps. status also reports health=absent/current/outdated/repairable/unsafe.
A displayed success must agree with post-write validation. No-op does not touch installed files.

| Exit code | Meaning |
|---|---|
| 0 | Requested operation completed, or status inspection completed; activation may be pending |
| 1 | Operational/validation failure; automatic restoration succeeded or no writes occurred |
| 2 | Invalid arguments, unsupported OS/scope/runtime, or missing prerequisites |
| 3 | Consent/authorization unavailable or refused |
| 4 | Concurrent run, changed snapshot, ambiguous ownership, or unsafe configuration |
| 5 | Recovery required; restoration could not safely finish, including after interruption |
| 130 | User interruption before mutation or after successful automatic restoration |

Exit 5 takes precedence over exit 130 whenever interruption leaves recovery_required state.
Include the recovery location in the exit-5 diagnostic.

## Privilege boundary

Ordinary CLI parsing, asset inspection, planning and logging run unprivileged. Linux apply/recovery
and read-only inspection of protected journals use the restricted worker after explicit scope
consent and authorization. No uv/dependency operation is run
elevated. Worker destinations are limited to validated XKB targets and its protected state root.
A plan contains data only; it cannot request arbitrary subprocesses. Worker revalidates the plan,
source checksums, destination identity and content before mutation. Interactive authorization
can prompt through the terminal; no password appears in CLI arguments or logs.

The worker entry is internal, versioned with the package, and is not a public plan-file execution
API. Production commands expose no test root, force overwrite, or unsupported-platform bypass.

## Recovery semantics

recover RUN_ID looks only in the selected scope's state directory and requires the same privilege
as installation. It validates hashes before restoring; current files changed by someone else
cause safe refusal. Restoring a fresh install removes only verified project-created artifacts
and restores shared pre-install files. This is transaction recovery, not general uninstallation.
Installer reruns inspect protected journals before deciding to apply changes or report no-op.
Actual installation restores interrupted transactions before planning new work and explains it;
status and dry-run only describe the required recovery. Any authorized inspection is followed by
fresh validation under the mutation lock before applying changes.

## Acceptance examples

- macOS: uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install
- Linux: uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --scope system
- Preview Linux: uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --scope system --dry-run
- Recovery: uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic recover RUN_ID --scope system

All paths are resolved independently of caller cwd; from elsewhere use uv run --no-project --python
/absolute/path/to/checkout/.venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic followed by the same arguments.

## Implementation correction (2026-09-19)

An isolated test with uv 0.12.16 showed that `uv run --no-sync` creates a missing .venv
before failing to find the console command. Product invocation therefore uses `--no-project`
and an explicit prepared `.venv/bin/python`; a missing interpreter fails without creating an
environment or selecting a global fallback. The redundant `--no-sync` flag is omitted because
uv warns it has no effect with `--no-project`. Explicit setup remains unchanged.
