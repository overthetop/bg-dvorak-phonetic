# Spec Delta

## Purpose

Provide repeatable evidence that distributed keyboard layout files and supported installers work, while making graphical desktop coverage visible.

## ADDED Requirements

### Requirement: Automated platform checks
The project SHALL run GitHub Actions checks on Ubuntu and macOS for install, repeat install, and removal, and SHALL fail a check when the expected layout files or registrations are absent or malformed.

#### Scenario: Pull request checks
- **WHEN** a pull request changes layout data, installers, packaging, or workflow files
- **THEN** Ubuntu and macOS checks run and report whether the install lifecycle succeeds

### Requirement: X11 mapping verification
The Ubuntu check SHALL compile or load the installed layout through an X11 server and verify representative key mappings against expected Bulgarian characters.

#### Scenario: Incorrect X11 mapping
- **WHEN** a layout edit changes a checked key to an unintended character
- **THEN** the X11 verification check fails

### Requirement: GNOME Wayland verification boundary
The project SHALL verify that installed XKB data compiles for Wayland clients and SHALL document a GNOME Wayland desktop smoke test for layout discovery, selection, and typing before release.

#### Scenario: Release review
- **WHEN** a release candidate is reviewed
- **THEN** the reviewer has a repeatable GNOME Wayland smoke test and can distinguish its result from headless CI checks

### Requirement: Windows 11 verification plan
The project SHALL document the native Windows layout artifact and Windows 11 test environment needed for a future implementation, and SHALL not describe a Windows Server runner result as Windows 11 compatibility evidence.

#### Scenario: Windows plan review
- **WHEN** a maintainer reviews the planned Windows phase
- **THEN** the plan identifies the required native installer, Windows 11 x64 validation, and the limits of standard GitHub-hosted Windows runners
