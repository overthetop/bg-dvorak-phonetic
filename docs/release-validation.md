# Release validation

Release readiness is pending until every row has actual evidence. Headless fixture tests do
not establish desktop discovery or typing.

| Environment | Native CI | Discovery, selection, typing | Repair/no-op/recovery |
|---|---|---|---|
| Ubuntu 24.04 x86_64 GNOME X11 | Pending hosted run | Pending | Pending desktop run |
| Ubuntu 24.04 x86_64 GNOME Wayland | Same Ubuntu job | Pending | Pending desktop run |
| macOS 15 Intel | Pending | Pending | Pending |
| macOS 15 ARM64 | Pending | Pending | Pending |
| macOS 26 ARM64 | Pending | Pending | Pending |

Use disposable accounts/VMs with recorded pre-install settings and restoration access. Record
commit, OS version, architecture, Python version, session type, commands, outcomes, diagnostics,
and screenshots or typed text where appropriate. Follow the README and installation guide
without consulting source code.

1. Check the [official Python releases](https://www.python.org/downloads/) for the latest stable
   release before publishing. Review runtime pin and lock changes together; rerun the full matrix.
   A blocked upgrade needs the constitution's documented maintainer-approved exception.
2. Run the four native jobs and confirm all same-commit artifacts and strict combined line
   coverage above 80%. Exercise a deliberately failed test and missing artifact in a controlled
   CI run; confirm aggregation fails and retain the run URLs.
3. Fresh install, select the discovered layout, and compare expected Bulgarian letters and
   shifted/modifier symbols against the supplied layout images and native assets.
4. Exercise an existing installation, supported missing-component repair, and three repeated
   current-state invocations. Verify unrelated input sources and preferences remain unchanged.
5. Capture preview, normal logs, denied authorization, a safe induced failure, and recovery.
   Confirm originals are restored and external edits are refused. Save work before any manual
   logout used for discovery; no automated session restart is allowed.
6. Record actual inspection/no-op and apply timings, excluding setup, authorization, and desktop
   refresh. Targets: inspection/no-op under 5 seconds and apply under 30 seconds. Validators
   have a 30-second timeout.
7. Review all findings and unresolved exceptions. Windows remains deferred by explicit feature
   scope; no Windows support may be claimed. Missing native or desktop evidence blocks release.

Store evidence under `specs/001-automate-layout-install/validation/`; leave task checkboxes open
when their required evidence is unavailable.
