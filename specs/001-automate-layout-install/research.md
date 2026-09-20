# Research: Automated Layout Installation

**Date**: 2026-09-18
**Scope**: Design decisions for spec.md; these are not executed compatibility tests.

## Runtime and tooling

**Decision**: Pin CPython 3.14.7 in .python-version, declare >=3.14.7,<3.15, and use
uv 0.12.16. Use a src-layout package with a console entry point. Runtime code uses the
standard library; development dependencies are pytest, coverage.py, Ruff, and mypy.
Resolve and commit their exact versions in uv.lock during implementation. Use
uv sync --locked --dev only for explicit setup, and
uv run --no-sync --no-python-downloads --offline for prepared product invocations. A read-only
preflight must check environment identity, interpreter pin and runtime dependencies; --no-sync
alone skips freshness checks. Missing/stale prerequisites fail with setup instructions; product
commands must never provision, update or fall back to another Python environment. Do not run
dependency installation elevated.
Ruff checks formatting/lint, mypy checks production code in strict mode.

**Rationale**: Python 3.14.7 is the latest stable release verified today; 3.15 is prerelease.
A single pinned interpreter and lockfile provide reproducible local/CI checks.

**Alternatives considered**: Latest/prerelease aliases drift; multiple scripting languages
duplicate policy; a runtime framework is unnecessary. Recheck stable Python before release.

Sources: [Python releases](https://www.python.org/downloads/),
[uv 0.12.16](https://github.com/astral-sh/uv/releases/tag/0.12.16),
[uv synchronization](https://docs.astral.sh/uv/concepts/projects/sync/),
[uv command flags](https://docs.astral.sh/uv/reference/cli/),
[uv CI](https://docs.astral.sh/uv/guides/integration/github/),
[pytest structure](https://docs.pytest.org/en/stable/explanation/goodpractices.html),
[Ruff](https://docs.astral.sh/ruff/),
[mypy](https://mypy.readthedocs.io/en/stable/existing_code.html).

## Supported environments and scope

**Decision**: Initial support is Ubuntu Desktop 24.04 LTS x86_64 (GNOME X11/Wayland),
macOS 15 on Intel/Apple Silicon, and macOS 26 on Apple Silicon. Required native CI labels:
ubuntu-24.04, macos-15-intel, macos-15, macos-26. Linux requires system scope explicitly;
macOS defaults to user scope and initially supports only that scope. Unsupported versions,
architectures, platforms, and requested scopes fail without installation changes.

**Rationale**: This bounds the compatibility claim to a concrete validation matrix while
covering both requested OS families and legacy installation paths. Desktop smoke evidence
is required for each declared OS/architecture and Linux session type before release.
Windows remains future work under the user's explicit feature scope.

**Alternatives considered**: All Linux distributions/desktop environments is not a testable
initial claim. Ubuntu 26.04 is outside initial support because its runner is currently preview.
Moving latest runner labels could change behavior without a project decision.

Sources: [Ubuntu lifecycle](https://ubuntu.com/about/release-cycle),
[GitHub runner inventory](https://github.com/actions/runner-images/blob/main/README.md).

## Linux integration and safe repair

**Decision**: Preserve layout bg and variant bg-dvorak-phonetic. Read the existing
/usr/share/X11/xkb/symbols/bg and /usr/share/X11/xkb/rules/evdev.xml. Also update the same
variant in rules/base.xml when it exists as a distinct file; resolve a distro-provided
base.xml alias to evdev.xml once rather than writing twice. A bounded parser identifies the
named XKB definition with string/comment-aware brace matching. XML is parsed for structure
and edited only at verified project-variant byte spans under the unique Bulgarian layout.
Preserve unrelated bytes. Duplicate complete project blocks/entries are replaced with one
canonical entry. Unbalanced shared XKB or malformed shared XML is refused.

Stage a complete candidate and validate using:
xkbcli compile-keymap --include STAGING --include-defaults --layout bg --variant bg-dvorak-phonetic.
Use the baseline-compatible compiler invocation without --test. Install prerequisites through
the documented distro package manager, not automatically from the installer.

**Rationale**: This repairs the README's existing installation model. Whole-file regex
replacement could damage unrelated layouts; blindly appending causes duplicates.
The README's current setxkbmap layout argument must be corrected in implementation.
The installed identity is bg with a variant, not a separate layout file name.

**Alternatives considered**: A new standalone symbols name changes legacy identity.
User-local XKB paths do not offer uniform X11 and Wayland behavior. No display-manager restart
and no automatic input-source preference changes; report supported desktop activation steps.

Sources: [XKB custom configuration](https://xkbcommon.org/doc/current/custom-configuration.html),
[XKB debugging](https://xkbcommon.org/doc/current/debugging.html),
[XKB release notes](https://xkbcommon.org/doc/1.13.0/release-notes.html).

## macOS integration

**Decision**: Install the existing bundle at
~/Library/Keyboard Layouts/bg-dvorak-phonetic.bundle. Preserve the repository's bundle identifier
org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic and its input-source ID.
Use plistlib, XML structural validation without external entity fetching, manifest comparison,
and native plutil validation for plists. Verify keylayout references and preserve every supplied
resource, including icons/localization. A missing/damaged canonical bundle can be repaired when
its remaining identity or a prior trusted receipt establishes ownership. An empty canonical
directory is repairable; a populated bundle with conflicting/unidentifiable identity is refused.

Detect matching input-source identities in both user and system Keyboard Layouts directories.
Repair duplicates only within the selected user scope and only with verified identity; report
system conflicts with manual recovery instructions. Do not edit com.apple.HIToolbox preferences.
Show Input Sources instructions and leave activation pending until the user verifies it.

**Rationale**: Matches legacy instructions and avoids permission escalation on macOS.
Ukelele reports removal of its former all-user installation method; that does not prove all
manual system-wide installation is impossible, but no such feature is needed here.

**Alternatives considered**: macOS system-scope installation and automatic preference editing
add platform behavior outside the initial support contract.

Sources: [Apple input sources](https://support.apple.com/en-sg/guide/mac-help/mchlp1406/mac),
[Ukelele history](https://software.sil.org/ukelele/ukelele-version-history/).
Repository evidence: README.md and mac-os/bg-dvorak-phonetic.bundle/Contents/Info.plist.

## Transactions, privilege, and recovery

**Decision**: Separate read-only inspection/planning from transactional writes. Use immutable
change plans, per-scope exclusive locks, before/after hashes, secure backups and durable JSON
journals. Recheck destination content under the lock before writes. Stage replacements on the
destination filesystem, validate, then replace individual files. Bundle directory replacement
uses journaled rename steps; do not claim atomic replacement of multiple files or nonempty
directories. Reverse completed operations on failure; retain originals until explicit recovery
or cleanup. A later run detects incomplete transactions before planning new changes.

Only Linux's restricted worker runs elevated after explained scope consent and sudo authorization.
It supports read-only protected-journal inspection in addition to apply/recovery. Status and dry-run
may request inspection authorization but cannot change installation/recovery state. Unavailable
authorization must report incomplete inspection rather than an assumed clean state. Installation
checks pending recovery before planning new writes or reporting no-op; previews never restore it. The worker validates the plan, allowed destinations, identities,
ownership, symlinks, hashes, and source assets independently. It cannot execute arbitrary
commands supplied in the plan. Use the trusted checkout's resolved interpreter/worker paths;
never run uv, fetch dependencies, or use shell command strings as root.
No public arbitrary target-root option; tests inject filesystem roots in-process.

**Rationale**: A failure between registration and asset writes must remain recoverable.
Platform locking and privilege operations are behind adapters so a future Windows adapter
can supply different primitives without changing common workflow policy.

**Alternatives considered**: Running the full installer/uv as root grants unnecessary scope.
Backups alone without a journal cannot identify which partial changes need restoration.
No-op runs do not create backups or rewrite layout files. If interruption leaves recovery required,
exit 5 overrides exit 130; exit 130 means no mutation or successful restoration.

Sources: [Python filesystem operations](https://docs.python.org/3/library/os.html),
[Expat parsing](https://docs.python.org/3/library/pyexpat.html).
The transaction design and byte-preservation policy are project decisions.

## Test evidence and exact coverage threshold

**Decision**: Each required matrix job runs common unit/contract tests and its native integration
tests against temporary destinations using actual OS validators. All jobs must pass separately.
Collect branch-enabled coverage for the entire src package, including unimported files, with
relative paths and distinct data files. Combine all required platform artifacts from the same
commit, fail on missing artifacts, and gate line counts with:
covered_lines * 100 > num_statements * 80 and num_statements > 0.
Local single-platform runs publish reports without a threshold gate. The complete same-commit
native aggregate alone enforces the threshold and publishes line/branch reports plus test logs.
Do not apply fail_under=80 as the constitutional
gate: exactly 80% must fail, and branch-inclusive percentages are a different measurement.

Measure subprocess workers too, using coverage's supported subprocess instrumentation in
isolated tests. Test the coverage gate at zero statements, below 80%, exactly 80%, and above 80%.
Do not make native validators or critical platform tests optional silent skips on their own OS.

**Rationale**: Native tests prove file/API behavior; desktop discovery and actual typing need a
separate manual release check. Aggregation measures platform-specific code without pretending
each OS can exercise every native API.

**Alternatives considered**: Mock-only integration, a single Linux runner, rounded threshold
checks, or missing-report success would provide misleading evidence.

Sources: [Combining coverage](https://coverage.readthedocs.io/en/latest/commands/cmd_combine.html),
[JSON coverage](https://coverage.readthedocs.io/en/latest/commands/cmd_json.html),
[Coverage reporting](https://coverage.readthedocs.io/en/latest/commands/cmd_report.html).
