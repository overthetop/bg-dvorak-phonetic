# Windows validation evidence protocol — T004

Evidence status is **pending**, **passed**, or **failed**. Unavailable environments, missing
logs and unexecuted scenarios are pending; an executed failed assertion is failed. Only
observed successful checks with the required artifacts are passed. Mocks and Windows Server
cannot establish Windows 11 desktop compatibility. Current native Windows evidence is pending.

Each record must contain: task/scenario identifiers; UTC execution time; exact Git commit;
clean/dirty status and SHA-256 manifest of all changed inputs for a dirty worktree; Windows
edition, full OS build/update, architecture, Python/uv/compiler/SDK/WDK versions; security and
Secure Boot state; shell and working directory; exact commands and exit codes; expected and
observed results; log/artifact paths and hashes; operator; cleanup/restoration result; limitations
and next steps. Keep sensitive account identifiers out of public logs. Record CI run URLs
and artifact hashes for hosted runs. A missing field prevents the corresponding gate passing.

## Environment access and containment

Arrange interactive access to disposable native Windows 11 25H2 x64 Home **and** Pro VMs;
record each VM identity and access method without credentials. This session has neither.
Hosted `windows-2025` is a separate build/native-API environment. Also retain Ubuntu 24.04
GNOME X11/Wayland and macOS 15 Intel/ARM64 and 26 ARM64 acceptance environments.

Before manual registration, snapshot the VM and capture existing layout identities, values,
security descriptors, project-file absence/presence and input preferences. Keep normal Windows
protections enabled. Refuse identity collisions. Use only project-specific files/registration;
never overwrite built-in layouts. Record the complete manual registration and inverse procedure
before executing it. After each scenario, restore captured state, compare files/registry/input
preferences, and revert the snapshot if cleanup cannot be verified. A locked DLL or failed
cleanup is an explicit failure/pending recovery result, never silently discarded evidence.
Isolated API tests use temporary files and test-owned registry keys, not live keyboard roots.

## Gates and scenarios

| Gate | Required evidence |
|---|---|
| T011 first native asset proof | Quickstart prerequisites/manual proof: locked build, identity collision check, Settings discovery, manual selection, all mapping/modifier/dead-key cases in x64 editor/browser and 32-bit probe, Home and Pro, verified restoration |
| T021 shared foundation | Native resource/schema/rollback checks and unchanged POSIX/v1 recovery behavior |
| T033 fresh installation | Quickstart A/B/E: read-only preview, bounded elevation, install, typing, offline/Unicode paths, sign-out persistence |
| T040 repeated install/repair | Quickstart C: three no-op runs, update/repair, unrelated state preservation and conflicts |
| T049 recovery | Quickstart D: faults, crashes, transport loss, rollback, retry, loaded files and third-state refusal |
| T059–T061 initial evidence | Five hosted native jobs, source-plus-tools coverage strictly greater than 80%, Home/Pro A–E and existing Unix desktops |
| T065 final release gate | Repeat T059–T061 after T062–T064 against the frozen final candidate; all five CI jobs and all required desktops must reference that candidate |

See [quickstart](../quickstart.md) for scenario details and [tasks](../tasks.md) for dependencies.
T011 blocks installer expansion. A failed proof requires measured contract/plan corrections
and a fresh proof. Unavailable native evidence remains unchecked. T059–T061 are preliminary:
code, dependency, configuration, fixture or substantive documentation changes invalidate affected
results. Freeze again and rerun T065 after corrections; no stale evidence or partial aggregate
may establish release readiness. Do not publish as part of evidence collection.
