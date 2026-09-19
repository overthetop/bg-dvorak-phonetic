<!--
Sync Impact Report (temporary review material; remove before committing)
Version change: 1.0.0 -> 1.1.0 (new Python principle and expanded validation gates)
Modified principles:
- II. Linux, macOS, and Windows 11 Compatibility (native Python runtime clarified)
- V. Evidence-Based Validation (Python checks and strict coverage gate added)
Added sections: VI. Modern Python and Reproducible Tooling
Other updates: Development Workflow and Quality Gates
Removed sections: none
Package manager: uv, explicitly confirmed by the user.
Deferred TODOs: none
-->
# Bulgarian Dvorak Phonetic Keyboard Layout Constitution

## Core Principles

### I. Safe and Predictable Shell Scripts

Scripts MUST declare their interpreter and supported minimum version, validate arguments and
prerequisites before mutation, and return nonzero on failure. Diagnostics MUST go to stderr;
stdout MUST remain suitable for the script's documented output. Shell expansions MUST be
quoted unless splitting or globbing is intentional and documented. Scripts MUST avoid eval,
parsing ls output, and constructing executable command strings from input. Bash-specific
features MUST NOT appear in scripts declared as POSIX sh.

Failures of commands and pipelines MUST be handled explicitly; strict shell options MAY be
used when their behavior is compatible with the declared interpreter, but MUST NOT replace
error handling. Temporary files MUST be created securely and cleaned up on exit or interruption.
Paths MUST be resolved independently of the caller's working directory. Scripts MUST handle
spaces and non-ASCII characters in paths, including Bulgarian text. These rules make automation
predictable and protect user files and keyboard configuration.

### II. Linux, macOS, and Windows 11 Compatibility

Every user-facing scripted workflow MUST have a documented and validated execution path on
Linux, macOS, and Windows 11. A single portable implementation is preferred; platform-specific
entry points MUST provide equivalent workflow outcomes through documented interfaces. An
OS-specific script MUST detect unsupported environments and exit before making changes.

Each workflow MUST document the supported OS versions or Linux distributions, interpreter,
minimum runtime version, dependencies, and invocation for each platform. Windows 11 support
MUST explicitly identify the native Python runtime and any launcher requirements, or a required
compatibility runtime such as Git Bash or WSL. A WSL run alone MUST NOT count as evidence that a workflow integrates with the Windows
host's keyboard settings. GNU/BSD utility differences, path conventions, permissions, encoding,
and line endings MUST be addressed through portable operations or isolated platform adapters.
Undocumented preinstalled tools MUST NOT be assumed.

### III. SOLID Responsibilities and Interfaces

SOLID MUST be applied to script functions and modules without requiring object-oriented code:

- Single responsibility: argument parsing, layout transformation, and OS installation MUST be
  separate responsibilities, with filesystem side effects isolated from reusable logic.
- Open/closed: platform differences MUST be confined to adapters behind stable contracts;
  adding a platform MUST NOT require duplicating shared workflow logic.
- Liskov substitution: interchangeable adapters MUST honor the same documented inputs,
  outputs, exit-status semantics, and side-effect guarantees.
- Interface segregation: functions and commands MUST accept only the inputs needed for their
  responsibility rather than unrelated modes or global configuration.
- Dependency inversion: shared workflow logic MUST use explicit adapter contracts for OS
  operations; external commands and destination paths MUST be replaceable during testing.

Abstractions MUST serve an existing variation or a concrete testing need. SOLID MUST NOT be
used to justify speculative frameworks or unnecessary indirection.

### IV. Keep It Simple (KISS)

Implementations MUST use the smallest readable design that satisfies the documented behavior.
Straightforward control flow and named functions MUST take precedence over dense one-liners,
metaprogramming, or unnecessary dependencies. New dependencies and abstraction layers MUST
have a documented benefit that cannot be met adequately by the existing runtime and tools.
Shared behavior MUST have one authoritative implementation; small platform-specific details
MAY remain local when sharing them would obscure their purpose. Comments MUST explain
non-obvious intent or portability constraints, and obsolete paths MUST be removed when replaced.

### V. Evidence-Based Validation

Changes to script behavior MUST pass syntax checks for each declared interpreter and relevant
static analysis: formatting, linting, and type checking for Python; ShellCheck for sh/Bash; and
PSScriptAnalyzer for PowerShell. Suppressions MUST be narrow and explain the reason. Behavioral checks MUST cover success, invalid input, missing
dependencies, command failure, paths containing spaces and Cyrillic characters, and repeated
execution where a workflow changes state.

Automated tests MUST maintain overall line coverage strictly greater than 80% across all
first-party Python production code, including shared modules and platform adapters. CI MUST
fail when the unrounded coverage value is 80% or lower; a rounded display of 80% MUST NOT
satisfy the gate. Coverage MUST include unexecuted production modules in its denominator and
combine native-platform test results so OS-specific code is measured on its applicable OS.
Reports MUST show line and branch coverage and identify uncovered code. Tests, generated code,
and vendored dependencies MAY be excluded; production exclusions require a documented review
justification and MUST NOT be used to hide untested behavior. Passing coverage MUST NOT replace
the required failure, recovery, idempotency, and native-platform acceptance checks.

Before release, each affected workflow MUST be exercised on Linux, macOS, and Windows 11
using its documented runtime. Validation records MUST identify the OS, runtime, commands,
and outcomes. Tests involving system keyboard configuration MUST use disposable environments
or a controlled manual procedure with restoration steps. Mocked adapter tests MUST be
supplemented by actual platform execution. An unavailable platform MUST be reported as an
unverified release blocker for the affected workflow; compatibility MUST NOT be inferred
solely from code inspection.

### VI. Modern Python and Reproducible Tooling

Product installation, update, and repair logic MUST use Python; platform launchers MAY remain
minimal wrappers. Shared behavior MUST be reusable, with OS-specific operations isolated behind
the SOLID interfaces above.

The project MUST target the latest stable Python release available when establishing or updating
its runtime baseline. Prereleases MUST NOT be the default. The exact Python version MUST be
pinned for local development and CI, and the supported runtime range MUST be declared in project
metadata and documentation. Before each project release, maintainers MUST check the official
Python releases, update the pin to the latest stable release, and rerun required checks. A blocked
upgrade MUST follow the documented governance exception process rather than silently using an
older baseline. Installed environments MUST NOT be upgraded implicitly during layout installation.

Python code MUST follow PEP 8 naming and style conventions and use an automated formatter,
linter, and static type checker. Functions and module interfaces MUST have type annotations;
public interfaces MUST document their purpose, inputs, outcomes, and relevant failures. Code
MUST use small cohesive functions, explicit dependencies, and context managers for resources.
Mutable default arguments, wildcard imports, swallowed exceptions, and import-time installation
side effects are prohibited. Exceptions MUST be handled at the appropriate boundary with
actionable diagnostics and preserved causes.

Filesystem operations MUST use portable path handling and explicit text encodings. External
commands MUST receive argument lists without shell interpolation, have their results checked,
and use timeouts where they could otherwise wait indefinitely. OS-specific APIs MUST stay in
platform adapters. Tests MUST verify behavior and recovery, with isolated filesystem effects
and no dependence on a developer's live keyboard configuration.

uv MUST manage project dependencies, isolated environments, and development/test execution.
Dependencies MUST be declared in pyproject.toml and resolved in a committed uv.lock. Local
validation and CI MUST use the same locked dependency set; CI MUST reject a stale lockfile
rather than silently re-resolving it. Dependency and Python pin updates MUST be reviewed and
validated together. Setup documentation MUST explain how to obtain the required Python and uv
versions, and automation MUST NOT modify the system Python environment.

## Platform and Installation Constraints

The project provides a Bulgarian Cyrillic phonetic layout mapped to US Dvorak. Scripts MUST
preserve the intended mappings and platform layout metadata unless a specification explicitly
changes them. Platform-specific capabilities and limitations MUST be documented.

Install and uninstall operations MUST be idempotent, preserve unrelated layouts and settings,
and provide a documented recovery procedure. Before overwriting existing configuration, scripts
MUST preserve the original or use an equivalent reversible mechanism. Partial failures MUST
leave recoverable state and explain recovery steps. Privilege elevation MUST be limited to
operations that require it and explained before execution. System-wide changes MUST be
explicitly selected. Scripts MUST NOT restart a desktop session, reboot, or remove unrelated
files without explicit user consent. Dependencies MUST be checked before privileged writes.

## Development Workflow and Quality Gates

Specifications and plans MUST identify affected workflows, platform/runtime support, interfaces,
installation side effects, and acceptance checks. Implementation tasks MUST include required
platform adapters and validation work. Reviews MUST check all six principles and identify any
remaining portability gaps before approval.

Script changes MUST include updated usage documentation when invocation, dependencies,
behavior, or recovery changes. Required syntax, formatting, linting, type, behavioral, and
coverage checks MUST pass before merging behavior changes. CI MUST enforce the locked
dependency set and publish the combined coverage report. Release approval MUST include the three-platform
validation evidence required above. Existing scripts MUST be assessed when changed; adopting
this constitution alone does not establish that existing code passes these requirements.

## Governance

This constitution is the authoritative project engineering policy. Specifications, plans, tasks,
and reviews MUST comply with it. Amendments MUST document the proposed text, rationale,
compatibility impact, and any migration work, and MUST receive maintainer approval before
adoption. Exceptions MUST name the affected rule, explain the need, record mitigation and a
removal milestone, and receive maintainer approval; undocumented exceptions are prohibited.

Constitution versions MUST follow semantic versioning: MAJOR for incompatible principle
removals or redefinitions, MINOR for new principles or materially expanded guidance, and PATCH
for non-semantic clarification. Amendments MUST preserve the original ratification date and
update the last-amended date. Each review MUST record compliance or approved exceptions;
release reviews MUST verify that outstanding exceptions remain valid and have not passed
their removal milestone.

**Version**: 1.1.0 | **Ratified**: 2026-09-18 | **Last Amended**: 2026-09-18
