# Feature Specification: Windows 11 Support

**Feature Branch**: `automate` (existing branch; no branch-creation hook configured)

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "add support for windows 11"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and Type on Windows 11 (Priority: P1)

A Windows 11 user follows the project instructions to install Bulgarian Dvorak phonetic,
select it in Windows, and type the intended Bulgarian characters in everyday applications.

**Why this priority**: Actual typing in Windows is the core value of adding this platform.

**Independent Test**: On a clean Windows 11 x64 desktop, follow the documented setup,
install the layout, select it, and verify typing in a text editor and a browser text field.

**Acceptance Scenarios**:

1. **Given** a supported clean machine with documented prerequisites, **When** the user runs
   the documented installation command, **Then** the project layout is installed without manual
   configuration edits, and the result includes Windows activation instructions.
2. **Given** installation needs administrator authorization or machine-wide changes, **When**
   the user previews or starts installation, **Then** the affected scope is explained, machine-wide
   scope requires explicit selection, and authorization is obtained before privileged changes.
3. **Given** the installed layout, **When** the user selects it and types the documented mapping
   cases in a text editor and browser, **Then** the expected characters and modifier behavior
   match the approved Windows mapping reference.
4. **Given** another layout is selected, **When** installation completes, **Then** the current
   selection and other input preferences remain unchanged; any required sign-out or restart is
   reported as a user action and is never initiated automatically.
5. **Given** installation and activation have completed, **When** the user signs out and back in,
   **Then** the layout remains available for selection and typing.

### User Story 2 - Inspect, Update, and Repair an Installation (Priority: P1)

A returning user uses the familiar project workflow to inspect Windows installation state,
preview changes, update the layout, or repair identifiable damage.

**Why this priority**: Windows support must remain usable after the first installation.

**Independent Test**: Prepare current, outdated, incomplete, duplicate, and conflicting installations;
check status and preview, then run installation and compare resulting state with the reported outcome.

**Acceptance Scenarios**:

1. **Given** a fresh, current, outdated, or damaged installation, **When** the user requests status,
   **Then** the result identifies the detected state and scope, or explains why inspection is incomplete.
2. **Given** any proposed installation or recovery, **When** the user requests a preview,
   **Then** intended changes and authorization requirements are displayed without changing
   installation state or creating recovery records.
3. **Given** an older or safely identifiable damaged project installation, **When** installation
   runs, **Then** it updates or repairs project components to one effective registration in the
   selected scope while preserving unrelated layouts and preferences.
4. **Given** a current installation, **When** installation runs three more times, **Then** each
   run reports no changes and creates no duplicate registrations, rewritten assets, or new backups.
5. **Given** conflicting layout identities or components whose ownership cannot be established,
   **When** repair is requested, **Then** it refuses unsafe changes and identifies the conflict and
   the next action needed.

### User Story 3 - Recover from Failure (Priority: P1)

A user receives actionable diagnostics and can restore the state affected by a failed or
interrupted installation without losing unrelated keyboard configuration.

**Why this priority**: Keyboard setup changes must be reversible and understandable.

**Independent Test**: Induce denied authorization, a write failure, and interruption during an update;
follow the reported recovery procedure and verify the restored state before retrying.

**Acceptance Scenarios**:

1. **Given** missing prerequisites, invalid arguments, an unsupported environment, or denied
   authorization, **When** installation starts, **Then** it exits unsuccessfully before mutation
   and explains the problem and remedy.
2. **Given** failure or interruption after changes begin, **When** the operation ends or is resumed,
   **Then** prior state is restored or retained recovery information identifies what remains to
   restore; partial work is never reported as successful installation.
3. **Given** a recorded transaction, **When** the user requests recovery, **Then** its verified
   changes are reversed without removing unrelated components; repeated recovery is safe.
4. **Given** configuration changed externally after an interrupted operation, **When** recovery
   would overwrite those changes, **Then** it stops and explains the conflict while retaining originals.
5. **Given** simultaneous installation or recovery requests, **When** one is changing state,
   **Then** another cannot perform conflicting writes and receives a retry instruction.

### User Story 4 - Verify and Document Windows Support (Priority: P2)

Users can follow complete Windows instructions, and maintainers can distinguish automated
checks from verified Windows 11 desktop behavior before publishing support.

**Why this priority**: A platform claim needs reproducible evidence and usable documentation.

**Independent Test**: Follow the Windows documentation without consulting source code, run the
required automated checks, and review native desktop validation records and existing-platform results.

**Acceptance Scenarios**:

1. **Given** a clean Windows account, **When** the user follows the documentation, **Then** they
   can obtain prerequisites and complete installation, status, preview, activation, update, repair,
   and recovery using the documented commands and diagnostic guidance.
2. **Given** a pull request or default-branch push, **When** repository checks run, **Then** separate
   Windows, Linux, and macOS results and failure diagnostics are available; failed required checks
   prevent the change from being accepted.
3. **Given** a candidate release, **When** support is reviewed, **Then** evidence identifies exact
   Windows 11 edition, version, architecture, runtime, scenarios, and results, including actual layout
   discovery, selection, typing, and recovery in a controlled desktop environment.
4. **Given** only mocked, headless, compatibility-environment, or non-Windows-11 results,
   **When** validation is reported, **Then** native Windows 11 desktop support remains unverified
   and blocks the Windows support release until the missing acceptance checks pass.

### Edge Cases

- Unsupported Windows version or architecture: refuse installation before changes and list the supported target.
- Missing prerequisites or invalid layout assets: report the remedy before requesting privileged writes.
- Paths containing spaces or Bulgarian characters, and launch from another working directory: all documented workflows retain their expected behavior.
- A standard user declines or cannot obtain administrator authorization: preserve existing state and report the required next step.
- Layout components are in use, storage is exhausted, or access is denied: retain recoverable state and identify any pending user action.
- A display name matches but identity or ownership differs: do not treat the other layout as project-owned.
- Existing registrations in multiple scopes or belonging to other users: report conflicts without altering other users' preferences.
- A Windows update removes identifiable project registration: rerunning installation repairs it safely.
- A noninteractive run cannot obtain required consent: fail explicitly without waiting indefinitely or bypassing authorization.
- Desktop discovery is delayed or no graphical session is available: distinguish validated installation from pending activation and typing verification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Windows 11 x64 MUST support the existing user workflows for installation, update,
  repair, status, preview, and recorded-transaction recovery with equivalent outcome and safety
  guarantees to the existing platforms (Stories 1–3).
- **FR-002**: One documented installation invocation MUST choose fresh install, update, repair,
  or no-op based on detected state after prerequisites are satisfied (Stories 1–2).
- **FR-003**: The Windows layout MUST preserve the project's Bulgarian phonetic mapping based on
  US Dvorak. A reviewable Windows mapping reference MUST specify every supported character and
  modifier combination, including letter case, punctuation, and any platform differences; layout
  redesign is excluded (Story 1).
- **FR-004**: The installed layout MUST be discoverable and selectable through Windows keyboard
  controls and usable in both a desktop text editor and a browser text field, including after a
  new sign-in (Story 1).
- **FR-005**: Preflight MUST check the declared Windows target, runtime, prerequisites, arguments,
  source layout validity, destination access, and scope before changes. Unsupported or incomplete
  environments MUST receive an actionable failure (Stories 1 and 3).
- **FR-006**: System-wide changes MUST require explicit scope selection, explain their effects,
  and request only necessary administrator authorization. User-local scope MUST be preferred
  where supported; an unavailable scope MUST be rejected clearly (Story 1).
- **FR-007**: Installation MUST preserve unrelated layouts, other users' settings, and current
  input preferences. It MUST NOT automatically select the layout, sign out, or reboot (Story 1).
- **FR-008**: Status MUST distinguish absent, current, outdated, repairable, conflicting, and
  recovery-required states, with incomplete inspection reported explicitly. Preview MUST report
  intended actions without persistent changes (Story 2).
- **FR-009**: Update and repair MUST recognize project-owned installations, fix safely identifiable
  missing or damaged components and duplicates, and leave one effective project registration in
  the selected scope. Ambiguous ownership MUST block replacement (Story 2).
- **FR-010**: Repeating installation on a current layout MUST make no persistent changes or new
  backups. Concurrent mutations MUST be prevented (Stories 2–3).
- **FR-011**: Before replacing configuration, the workflow MUST preserve recoverable prior state.
  Partial failure and interruption MUST support documented recovery and safe retry; externally
  changed state MUST NOT be silently overwritten during restoration (Story 3).
- **FR-012**: Diagnostics MUST identify platform, scope, detected state, progress, final result,
  and any activation or recovery action. Failures MUST identify the failed operation, relevant
  location, available cause, and next action, following existing documented outcome conventions
  and remaining readable when captured without color (Stories 1–3).
- **FR-013**: Windows documentation MUST identify supported editions, versions, architecture,
  native runtime and launcher requirements, prerequisite acquisition, commands, privileges,
  activation, repair boundaries, logs, recovery records, and restoration steps. Setup MUST NOT
  implicitly upgrade the runtime during installation (Story 4).
- **FR-014**: Automated checks MUST exercise successful workflows, failure and recovery scenarios,
  mapping correctness, repeated runs, preserved unrelated state, and the listed edge cases on
  native Windows, alongside existing Linux and macOS checks, using isolated test configuration
  rather than a contributor's live keyboard settings (Story 4).
- **FR-015**: Release evidence MUST include controlled Windows 11 desktop acceptance checks and
  regression evidence for Linux and macOS. Unavailable platforms MUST be recorded as unverified
  release blockers; compatibility environments and simulated results alone MUST NOT establish
  Windows host integration (Story 4).

### Key Entities

- **Windows layout definition**: The intended character mappings, modifier behavior, stable project
  identity, and display name used to recognize and select the layout.
- **Installation state**: Supported environment, scope, installed project components, registration,
  conflicts, and pending activation or recovery actions.
- **Recovery record**: Verified ownership, affected resources, retained originals, and operation
  outcome needed to restore a prior state safely.
- **Validation evidence**: Environment details, tested scenarios, actual outcomes, and limitations
  supporting or blocking the platform compatibility claim.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every declared Windows 11 target, fresh install, update, and safely repairable
  installation each complete with one documented invocation and zero manual configuration edits,
  excluding disclosed authorization and activation steps.
- **SC-002**: Native desktop checks produce the expected output for 100% of the approved Windows
  mapping cases in both a text editor and browser text field, and confirm availability after sign-in.
- **SC-003**: Three repeated installations of a current layout produce zero duplicates, zero
  unnecessary persistent changes, and zero changes to unrelated layouts or input preferences.
- **SC-004**: Every induced failure reports an unsuccessful result and next action; every failure
  after mutation either restores prior state or retains sufficient information for demonstrated
  recovery. Preview produces zero persistent changes in all tested states.
- **SC-005**: A Windows documentation walkthrough completes setup, activation, inspection, update,
  repair, and recovery without source-code consultation or undocumented steps.
- **SC-006**: Every pull request and default-branch push receives distinct results for all three
  platforms. Before release, all required automated and native desktop acceptance scenarios pass
  and no required platform evidence remains unverified.

## Assumptions

- Initial support targets Windows 11 Home and Pro on x64 PCs. ARM64, older Windows releases,
  Windows Server, managed enterprise deployment, and remote-session keyboard redirection are
  outside this feature. Planning must name the exact Windows 11 versions to validate before
  implementation and publication of compatibility claims.
- This extends the existing command-driven workflow; a new graphical installer, automatic release
  downloads, background updates, and a general keyboard manager are outside scope.
- Windows support means integration with the Windows host. A Linux compatibility environment
  alone does not satisfy this requirement. The native runtime and reproducible development setup
  follow the project constitution; exact commands and dependencies belong in planning.
- Existing Linux and macOS assets are the mapping reference. Platform-specific differences must
  be documented and reviewed before acceptance, without changing the intended Bulgarian mapping.
- Users may need administrator assistance and may manually select the layout or refresh their
  session after installation. The precise supported installation scope is determined during
  planning and must satisfy the explicit-scope and authorization requirements above.
- Recovery reverses recorded installation changes; a new general uninstall command is outside
  scope, consistent with the existing workflow.
- Controlled native Windows 11 desktop access is a release dependency. Automated runner results
  alone cannot prove desktop selection and typing. Existing Linux/macOS validation gaps are not
  waived by adding Windows support.
- The prior feature's Windows exclusion no longer applies to this feature. The current project
  constitution governs implementation, tooling, quality gates, and three-platform validation.
