# Feature Specification: Automated Linux and macOS Layout Installation

**Feature Branch**: `main` (existing branch; no branch-creation hook configured)

**Created**: 2026-09-18

**Status**: Draft

**Input**: User description: "improve the scripts for linux and macos; aim for automation so that it's a one click install/update script; the scripts should work with already installed bg-dvorak-phonetic keyboard layout (fixing setup in case of a broken configuration) and with a machine that is not yet setup; add tests so that all scripts are verified that are working properly for linux and macos; improve docs; add github action that run the tests on these Operation systems. Add good logging so that the user can follow on the installation and see errors in case of some;"

## Clarifications

### Session 2026-09-18

- Q: Which language must implement installation automation? → A: Python, so common scripting
  logic can be reused across operating systems (user-provided clarification).
- Q: How must the system accommodate additional operating systems? → A: Keep shared workflow
  logic reusable and isolate OS-specific operations behind a common interface, enabling future
  Windows 11 support without implementing Windows support in this feature (user-provided clarification).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install on a Fresh Machine (Priority: P1)

A Linux or macOS user starts one documented installer invocation and obtains the Bulgarian
Dvorak phonetic layout without copying files or editing system configuration by hand.

**Why this priority**: A reliable fresh installation is the foundation of the requested automation.

**Independent Test**: On each supported OS, start with no project layout installed, follow only
the quick-start instructions, and verify the installed layout and any required activation steps.

**Acceptance Scenarios**:

1. **Given** a supported clean machine with documented prerequisites, **When** the user starts
   the installer, **Then** it installs and validates the supplied layout and reports the outcome.
2. **Given** installation requires elevated privileges or system-wide changes, **When** the
   installer reaches that boundary, **Then** it explains the scope and requests authorization
   before those changes, using user-local installation where supported.
3. **Given** layout selection or session refresh remains necessary, **When** installation finishes,
   **Then** it distinguishes installed files from active input and supplies exact next steps without
   restarting the session or rebooting automatically.
4. **Given** the repository is in a path containing spaces or Bulgarian characters, **When** the
   installer is invoked from a different working directory, **Then** installation still succeeds.

### User Story 2 - Update or Repair an Existing Installation (Priority: P1)

An existing user runs the same installer to update an older layout, repair a partial installation,
or confirm that a healthy installation is already current.

**Why this priority**: Existing manual installations and broken setup must be supported as fully
as new machines, without damaging other keyboard layouts.

**Independent Test**: Prepare healthy, outdated, missing-component, duplicate-entry, and damaged
project-layout installations on both platforms and verify the same invocation converges to the
intended state for every safely repairable case.

**Acceptance Scenarios**:

1. **Given** a layout installed using the existing README instructions, **When** the installer
   runs with newer supplied project assets, **Then** it recognizes and updates that installation
   while preserving unrelated layouts and user input preferences.
2. **Given** project files or registration are missing, stale, duplicated, or damaged but safely
   identifiable, **When** the installer runs, **Then** it repairs them to one effective project
   layout registration in the selected scope and reports what changed.
3. **Given** an installation is already current, **When** the installer runs twice more, **Then**
   it reports no changes and leaves layout content, unrelated settings, and registrations unchanged.
4. **Given** shared configuration is malformed or a conflict cannot safely be attributed to this
   project, **When** repair is attempted, **Then** the installer stops before unsafe changes and
   explains the affected location and recovery steps.
5. **Given** a write fails or execution is interrupted during mutation, **When** the user resumes,
   **Then** the previous state is restored or recoverable from preserved originals, and a subsequent
   invocation can complete without duplicate entries or loss of unrelated data.

### User Story 3 - Understand Progress and Recover from Errors (Priority: P1)

A user can follow installation progress and identify both the cause of a failure and the next
useful action without reading the script source.

**Why this priority**: Automated changes must be understandable, especially when privileges or
existing configuration prevent completion.

**Independent Test**: Capture successful runs and induced prerequisite, permission, validation,
and write failures on each OS; check the messages and reported result against the actual state.

**Acceptance Scenarios**:

1. **Given** any install, update, or repair run, **When** it progresses, **Then** the output names
   the detected platform, selected scope, detected installation state, current stage, and final result.
2. **Given** a missing dependency, unsupported environment, or invalid input, **When** preflight
   runs, **Then** it reports the problem and remedy, exits unsuccessfully, and changes no installation files.
3. **Given** a command or validation fails, **When** the installer reports it, **Then** the message
   identifies the failed operation, relevant destination, available cause, and recovery action;
   it does not claim success or expose credentials.
4. **Given** installation completes but activation remains pending, **When** the final summary
   appears, **Then** it identifies that pending action explicitly rather than claiming active input.

### User Story 4 - Verify Changes on Both Operating Systems (Priority: P2)

A maintainer receives repeatable evidence that all delivered installation scripts work on Linux
and macOS before accepting changes.

**Why this priority**: Native OS checks detect regressions that a single development machine misses.

**Independent Test**: Run the documented test command on each OS and trigger repository automation;
verify that a deliberately failing assertion causes the relevant automated check to fail.

**Acceptance Scenarios**:

1. **Given** a proposed change, **When** a pull request or a push to the default branch occurs,
   **Then** GitHub Actions runs the applicable tests separately on Linux and macOS and reports
   each platform's pass/fail result.
2. **Given** the test suite runs on either OS, **When** it exercises installation scenarios,
   **Then** it covers fresh installation, update, repair, repeated execution, preservation of
   unrelated data, and failures without modifying the maintainer's live keyboard configuration.
3. **Given** a failed test, **When** a maintainer opens the automation results, **Then** the failing
   scenario, platform, and relevant installer diagnostics are available.
4. **Given** a headless test environment cannot demonstrate desktop selection and actual typing,
   **When** results are published, **Then** that limitation and the required manual verification
   are explicit, and native desktop validation is recorded before release.
5. **Given** the shared Python workflow and Linux/macOS platform adapters, **When** their common
   interface tests run, **Then** both adapters satisfy the same input, outcome, error, and recovery
   guarantees, and shared logic can be tested without changing the host's keyboard configuration.
6. **Given** a minimal test-only adapter for another OS, **When** it is connected through the
   documented extension interface, **Then** it participates in the existing workflow without
   modifying Linux/macOS adapters or duplicating shared workflow logic. This test does not
   demonstrate actual Windows installation support.

### User Story 5 - Follow Complete Installation and Recovery Documentation (Priority: P2)

A new or returning user can find the correct command and understand supported environments,
update behavior, repair limitations, activation, and recovery from the project documentation.

**Why this priority**: Automation is useful only when users can discover and trust its entry point.

**Independent Test**: Follow the documentation on a clean and an existing installation on each OS
without consulting source code; follow the contributor instructions to run tests locally.

**Acceptance Scenarios**:

1. **Given** a new user, **When** they follow the quick start for their OS, **Then** they can obtain
   the project, meet prerequisites, launch installation once, and complete any activation steps.
2. **Given** an existing or damaged installation, **When** the user follows update or repair guidance,
   **Then** they use the supported invocation and can locate backups and recovery instructions.
3. **Given** a contributor, **When** they follow testing instructions, **Then** they can run applicable
   checks locally and understand automated coverage and remaining manual desktop checks.

### Edge Cases

- Missing dependencies, invalid options, unsupported OS/runtime, or absent platform layout assets:
  fail before installation changes and identify the remedy.
- Denied privilege requests, read-only destinations, or exhausted disk space: report failure and
  preserve recoverable originals rather than reporting partial work as complete.
- Broken shared configuration or ambiguous project ownership: stop safely; do not overwrite
  unrelated data to force a repair.
- Existing user-local and system-wide installations: identify scope conflicts and require explicit
  scope selection before changing anything outside the selected scope.
- Multiple simultaneous installer runs: prevent conflicting writes and explain how to retry.
- Interrupted updates and stale temporary state: preserve recovery information and allow safe retry.
- Paths with spaces or Cyrillic characters, different working directories, and supported runtimes
  with different default utilities: produce the same documented outcome.
- Missing graphical session or delayed desktop discovery: validate what can be checked and report
  activation as pending; do not disrupt the running desktop.
- A system update removes project registration: rerunning the installer restores safely identifiable
  project configuration using the same repair workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each supported OS MUST provide one documented invocation that automatically chooses
  fresh installation, update, repair, or no-op based on current state (Stories 1–2).
- **FR-002**: The installer MUST use the layout assets supplied with the obtained project version
  and preserve its intended mappings and metadata (Stories 1–2).
- **FR-003**: Preflight MUST validate platform, runtime, required tools, input, source assets,
  destination access, and installation scope before mutation (Stories 1 and 3).
- **FR-004**: The workflow MUST recognize installations created by the current README procedures
  and repair missing, outdated, duplicated, or damaged project-owned components when safe (Story 2).
- **FR-005**: Successful installation MUST leave one effective project registration in the selected
  scope. Repeated runs MUST preserve that state without duplicate entries or unnecessary changes (Story 2).
- **FR-006**: Changes MUST preserve unrelated layouts and preferences, retain recoverable originals
  before overwrites, and explain restoration after partial failure (Story 2).
- **FR-007**: The installer MUST stop on ambiguous ownership or unsafe shared-configuration damage;
  it MUST prevent concurrent conflicting writes and support retry after interruption (Story 2; Edge Cases).
- **FR-008**: Privileged and system-wide changes MUST be explained and explicitly authorized.
  User-local installation MUST be preferred where supported (Story 1).
- **FR-009**: The installer MUST validate the resulting installation before reporting success and
  distinguish installed, unchanged, activation-pending, and failed outcomes (Stories 1–3).
- **FR-010**: The workflow MUST automate all supported non-disruptive setup steps and document any
  remaining user activation steps. It MUST NOT automatically restart a desktop session or reboot (Story 1).
- **FR-011**: Logs MUST present ordered progress stages and distinguish informational messages,
  warnings, and errors. Failure diagnostics MUST include the operation, relevant location, known
  cause, and next action; diagnostics MUST go to stderr and failures return nonzero (Story 3).
- **FR-012**: Logs MUST remain understandable without color or an interactive terminal, be
  capturable with documented instructions, and exclude credentials or unrelated personal data (Story 3).
- **FR-013**: Automated tests MUST cover every delivered or modified installer, launcher, and helper
  applicable to each OS, including all scenarios in Stories 1–3 and the listed edge cases (Story 4).
- **FR-014**: Tests MUST include interpreter syntax and applicable static-analysis checks, run actual
  installation operations in isolated destinations, verify resulting state, and exercise failure
  recovery. Python code MUST receive Python-appropriate checks; any retained shell launchers
  MUST receive their applicable checks. Shared workflow tests and platform adapter contract tests
  MUST run on both Linux and macOS. Mock-only tests MUST NOT be the sole integration evidence (Story 4).
- **FR-015**: GitHub Actions MUST run the applicable suite on native Linux and macOS runners for
  pull requests and default-branch pushes, expose separate results and failure diagnostics, and
  fail the relevant job on a failed required check (Story 4).
- **FR-016**: Documentation MUST cover acquisition, supported OS/runtime versions, prerequisites,
  one-invocation installation/update/repair, scope and privileges, activation, logs, backups,
  recovery, local tests, automated checks, and manual desktop verification. Documentation MUST
  identify the supported Python versions and explain how users obtain Python when it is absent;
  Python availability MUST NOT be assumed merely from OS support (Story 5).
- **FR-017**: Before release, validation evidence MUST identify tested environments and results;
  manual checks MUST verify layout discovery, selection, and expected Bulgarian typing on both
  platforms where automated desktop verification is unavailable (Story 4).

- **FR-018**: Installation, update, and repair logic MUST be implemented in Python. Any OS-specific
  launchers MUST delegate to that implementation rather than duplicate its workflow. The supported
  Python version range MUST be documented and verified in automated checks (Stories 1 and 4).
- **FR-019**: Common state handling, workflow coordination, logging, and recovery policy MUST be
  reusable across platforms. OS-specific discovery, paths, permissions, registration, and activation
  MUST be isolated behind a documented platform adapter interface with consistent inputs, outcomes,
  errors, and recovery guarantees. Shared code MUST NOT require OS-specific dependencies merely
  to load on another platform (Story 4).
- **FR-020**: Adding a future OS such as Windows 11 MUST be possible by providing its adapter,
  assets, adapter registration, tests, and documentation without rewriting shared workflow logic or
  changing existing platform adapters. A test-only adapter MUST demonstrate the extension contract;
  dynamic plugin loading or a general plugin framework is not required (Story 4).

### Key Entities *(include if feature involves data)*

- **Layout assets**: The project version's authoritative keyboard mappings and platform metadata.
- **Installation state**: Platform, selected scope, installed assets, registration, detected damage,
  and activation status used to determine the necessary action.
- **Recovery record**: Preserved pre-change content and locations needed to restore affected state.
- **Run diagnostics**: Ordered progress and outcome information for users and automated checks.
- **Validation evidence**: Environment, scenario, result, and limitations from automated and manual checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every declared supported environment, fresh installation, update, and safely
  repairable setup each complete with one documented installer invocation and zero manual file edits,
  excluding disclosed authorization and desktop activation steps.
- **SC-002**: All defined repair fixtures converge to the expected valid state or an explicitly
  justified safe refusal; three consecutive successful invocations introduce zero duplicates
  and zero changes to unrelated configuration.
- **SC-003**: Every induced failure scenario reports unsuccessful completion, names the failed step,
  and provides a next action; all mutation-failure scenarios retain recoverable prior state.
- **SC-004**: Every pull request and default-branch push receives separate Linux and macOS test
  results, with all required scenarios passing before the feature is accepted.
- **SC-005**: A documentation walkthrough on each OS completes fresh setup and existing-installation
  repair without source-code consultation; expected Bulgarian typing is verified before release.
- **SC-006**: Every run reports its action and final state, and every activation-pending case tells
  the user exactly what remains to be done without an unsolicited session restart.

- **SC-007**: Linux and macOS pass the same shared behavior and adapter-contract acceptance checks;
  a test-only additional OS adapter demonstrates extension without changes to existing adapters
  or duplication of common install/update/repair behavior.

## Assumptions

- The repository currently supplies Linux and macOS layout assets and manual installation guidance;
  this feature introduces the missing installation automation as well as improving that guidance.
- "One click" means one documented launch or command after obtaining the project, with no manual
  configuration-file edits. A new graphical installer is not required. OS authorization and input
  source selection may still require interaction, which must be explained.
- Updating installs the assets in the obtained project version; downloading future releases and
  unattended background updates are outside this feature.
- Python is an explicit user-required implementation constraint. Planning must select the supported
  Python versions and prerequisite guidance; the one-invocation promise begins after documented
  prerequisites are met. Python portability alone does not establish OS installation compatibility.
- Reuse and extensibility follow SOLID and KISS: extract behavior shared by Linux and macOS and
  define a small platform adapter interface. Windows-specific behavior remains future work.
- Initial Linux support targets environments compatible with the supplied keyboard layout assets;
  the exact supported distributions, desktop sessions, macOS versions, and runtimes must be listed
  during planning and backed by validation. Unsupported environments must fail without mutation.
- The user's explicit Linux/macOS scope takes precedence for this feature over the constitution's
  broader Windows 11 workflow and release-validation requirements (Principles II and V). Windows
  implementation and CI are outside this feature; no Windows compatibility is claimed. This scoped
  deviation lasts through this feature and must be revisited before any Windows-support release;
  the constitution itself remains unchanged and its other principles continue to apply.
- Tests cover product installation scripts and their helpers. Spec Kit's internal workflow scripts
  are tooling outside this feature's script inventory.
- Automated environments may lack interactive desktop sessions; isolated native-OS tests and
  recorded manual desktop checks together supply the required installation and usability evidence.
- Layout redesign, new mappings, a general keyboard manager, and a new uninstall workflow are out
  of scope. Restoration of state affected by installation is required.
