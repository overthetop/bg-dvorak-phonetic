# Windows CLI Contract

This extends the [existing CLI contract](../../001-automate-layout-install/contracts/cli.md).
Commands below describe the implementation target; Windows support is not implemented by this plan.

## Setup and invocation

Prepare native x64 Python 3.14.7 and uv 0.12.16 explicitly. The checkout includes matching built
Windows assets. From PowerShell, use the prepared interpreter without environment synchronization:

```powershell
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic status
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic install --scope system --dry-run
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic install --scope system
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic recover RUN_ID --scope system --dry-run
uv run --no-project --python .venv\Scripts\python.exe --no-python-downloads --offline bg-dvorak-phonetic recover RUN_ID --scope system
```

From a different directory, give `--python` the quoted absolute path to the checkout interpreter.
An incomplete or stale environment fails with explicit preparation instructions and makes no changes.

| Command / option | Windows behavior |
| --- | --- |
| `install --scope system` | Inspect, select fresh/update/repair/no-op, obtain consent and needed OS authorization, verify results. |
| `status` | System inspection by default; report health, conflicts, pending recovery and activation instructions. |
| `recover RUN_ID --scope system` | Restore the verified recorded changes only; not a general uninstall. |
| `--scope user` | Exit 2; native Windows installation supports system scope only. |
| Omitted install/recover scope | Exit 2 before mutation, with exact explicit-scope retry command. |
| `--dry-run` | Read-only preview for install/recover; status remains read-only. No journals, backups, lock files, registrations, DLLs or durable IPC artifacts. |
| `--yes` | Accept displayed project plan; never grants UAC consent or chooses system scope. |
| `--verbose` | Additional redacted diagnostics; no passwords or complete environment dumps. |
| `--help`, `--version` | No elevation or installation effects, even on unsupported platforms. |

Noninteractive requests lacking project consent fail with 3 unless `--yes` is present. If a protected
operation cannot be authorized without interactive UAC, fail promptly with 3. An already authorized
worker can be used in controlled automation; never run dependency setup elevated. Protected journal
reads can require separate read-only elevation even for status/preview. Denial yields incomplete
inspection with exit 3, not a clean state.

## Output and exit status

Retain existing progress stages and final action/health/activation fields. Summarize registry
resources separately from filesystem paths and report scope, recovery UUID/location, and next action.
stdout is concise outcome text; stderr carries ordered progress/errors. A successfully inspected
unsafe installation may return 0 for `status` with `health=unsafe` and conflict details; an attempted
unsafe install returns 4. Pending recovery yields 5, including status/preview, consistently with the
existing workflow. A successful install may have `activation=pending`.

| Code | Meaning |
| --- | --- |
| 0 | Requested operation or inspection completed; activation can remain pending. |
| 1 | Operation failed before changes or automatic restoration succeeded. |
| 2 | Invalid input, unsupported target/scope/runtime, missing or invalid prerequisites/assets. |
| 3 | Plan consent or OS authorization unavailable/declined. |
| 4 | Concurrent mutation, changed snapshot, unsafe ownership/ACL/path, identity conflict. |
| 5 | Recorded changes require recovery; include recovery ID/location. |
| 130 | Interrupted before mutation or after successful restoration. |

Exit 5 overrides 130 when interruption leaves recovery incomplete. Windows errors are translated
into these outcomes rather than leaking unrelated native status codes.

## Activation and recovery

Print the installed name, instructions to add Bulgarian if absent, and the Windows Settings path:
Settings → Time & language → Language & region → Bulgarian → Language options → Keyboards →
Add a keyboard → Bulgarian (Dvorak phonetic). Select with Win+Space. Keep another working layout.
Validate this path on both supported editions before publishing it. If discovery is delayed, tell
the user to save work and sign out/in manually. Do not edit HKCU, another user's language profile,
the default user, default input source, or keyboard selection.

DLL/registration validation proves installation, not active typing. Updates may leave applications
using the prior loaded layout until the user refreshes their session. Report that distinction.
A rerun restores unfinished transactions before proposing new changes; preview/status only describe
them. Recovery requires the same explicit system scope and authority and refuses to overwrite
external edits. Locked new files keep the record recovery-required until safe cleanup succeeds.

No public command accepts arbitrary registry paths, custom roots, plan files, force overwrite,
or an unsupported-platform bypass. Test injection is internal only.
