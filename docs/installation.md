# Installation and recovery

Start with the [README prerequisites and setup](../README.md). Keep the complete checkout:
this installer uses its authoritative Linux files and macOS bundle, not a separately distributed wheel.
Run all commands from the checkout, or replace `.venv/bin/python` with `"/absolute/path/to/checkout/.venv/bin/python"`. Quote paths containing spaces or Bulgarian characters.

## Inspect and preview

```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic status
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --scope system --dry-run
```

The second example is Ubuntu; omit `--scope system` on macOS. Status defaults to system
inspection on Linux and user inspection on macOS. Linux's root-owned recovery journals can
require consent and sudo even for status or a preview. That authorization grants read-only
inspection: it creates no installation files, journals, backups, or locks. Denied access
means inspection is incomplete; it never means the installation is clean.

Installation/update/repair uses the same command as the README. It validates candidates,
retains recoverable originals, checks the installed result, and prints activation instructions.
No-op runs do not rewrite layouts or create new backups. Never run the entire installer with sudo;
it delegates only the necessary fixed Linux operations to its worker.

## Activation

Ubuntu GNOME: open Settings → Keyboard → Input Sources and add Bulgarian (Dvorak phonetic).
The XKB identity is `bg` with variant `bg-dvorak-phonetic`. Select it using GNOME's input-source
switcher. Under Wayland, `setxkbmap` does not configure the compositor. Under X11, an optional
session-only selection is `setxkbmap -layout bg -variant bg-dvorak-phonetic` after installation.
Keep another working input source available. If discovery requires a new session, save work
and log out/in manually. The installer never restarts the display manager.

macOS: open System Settings → Keyboard → Text Input → Edit, add the supplied Bulgarian
Dvorak phonetic source, then select it from the input menu. If it is not discovered, save
work and log out/in manually before trying again. The installer does not edit input preferences,
force logout, or claim that successful file installation proves actual typing.

## Repair boundaries

Linux repairs complete identifiable project blocks and registrations in `symbols/bg`,
`rules/evdev.xml`, and a distinct `rules/base.xml`. A verified base-to-evdev alias is handled
once. Unrelated bytes are retained. Malformed shared XML or unbounded XKB is refused:
restore a valid distro configuration first, then rerun.

macOS repairs empty destinations and damaged bundles with a remaining matching identity or
trusted prior transaction receipt. Conflicting identifiers or unidentified populated bundles
block replacement. Only exact-identity duplicates in the selected user scope are removed.
A matching system bundle under `/Library/Keyboard Layouts` blocks user installation; reconcile
that global installation manually with its owner. This feature does not modify system macOS layouts.

## Logs and exit codes

Progress and errors go to stderr; a concise final result goes to stdout. Capture plain diagnostics:

```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic install --scope system --dry-run 2>installer.log
```

Omit system scope on macOS. `--verbose` adds a redacted traceback to failures.

| Code | Meaning |
|---|---|
| 0 | Operation completed; activation may still be pending |
| 1 | Operational/validation failure; no writes or successful restoration |
| 2 | Invalid arguments or unsupported/missing prerequisites |
| 3 | Confirmation or OS authorization unavailable/declined |
| 4 | Concurrent run, changed snapshot, unsafe configuration, or ambiguous ownership |
| 5 | Recovery required; retain the reported originals |
| 130 | Interrupted before mutation or after successful restoration |

Code 5 takes precedence over 130 if interruption leaves restoration incomplete.

## Recover a recorded transaction

State and retained originals are stored outside discoverable keyboard paths:

- Ubuntu: `/var/lib/bg-dvorak-phonetic`, root-owned, directory mode 0700.
- macOS: `~/Library/Application Support/bg-dvorak-phonetic`, user-owned, directory mode 0700.

Each generated run-ID directory includes a mode-0600 journal and original resources.
Backups remain after successful changes. Keep the reported recovery ID and location.

```sh
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic recover RUN_ID --scope system --dry-run
uv run --no-project --python .venv/bin/python --no-python-downloads --offline bg-dvorak-phonetic recover RUN_ID --scope system
```

Replace `RUN_ID` with the reported identifier; omit system scope on macOS. Recovery accepts
only IDs inside the known state root, never arbitrary journal paths. It restores shared original
files and removes verified newly created artifacts. It is transaction recovery, not general uninstall.
A preview can authorize protected journal reads but never restores or writes state.

An actual install rerun restores unfinished transactions before planning new work. Status and
preview only describe pending recovery. External edits after a crash cause refusal; preserve
both those edits and the retained originals, reconcile them manually, and retry. Do not delete
journals to bypass a recovery warning. A failure between files is recoverable, not globally atomic.

## Explicit backup cleanup

There is no automatic cleanup command. When you no longer need rollback, inspect the journal
for each exact run-ID directory. Only `committed` or `restored` transactions are eligible for
manual deletion; retain every unfinished or unknown transaction. Removing a completed run directory
removes its rollback capability. Never delete the whole state root, the stable lock file, or a
run directory while an installer/recovery process is active. Use your OS's authorized file tools
for the applicable scope and preserve the state root's ownership and mode.
