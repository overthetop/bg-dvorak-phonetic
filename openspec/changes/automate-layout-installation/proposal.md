# Proposal

## Why

Installation currently requires users to clone the repository, copy files manually, and on Linux edit vendor XKB files and restart the display manager. Small, repeatable installers and automated checks can reduce user effort while making supported environments explicit.

## What Changes

- Provide a downloadable macOS installer for the existing keyboard layout bundle and a documented way to remove it.
- Provide an Ubuntu GNOME installer covering Wayland and X11 sessions, with safe repeat installation and removal.
- Replace the current manual instructions with short installation, activation, and removal instructions; avoid requiring Git for end users.
- Add GitHub Actions checks for layout data and installer lifecycle on Ubuntu and macOS, plus X11 keymap checks.
- Define a Windows 11 native-layout packaging and verification plan for a subsequent change. This change does not claim Windows installation support or a Windows 11 CI pass.

## Capabilities

### New Capabilities

- `layout-installation`: Users can install, activate, update, and remove the layout on supported macOS and Ubuntu GNOME systems.
- `installation-verification`: Automated checks verify layout files and installer behavior, with clear limits for graphical desktop behavior.

### Modified Capabilities

None.

## Impact

Adds small platform-native scripts, distribution packaging, GitHub Actions workflows, and revised README instructions. Linux support is scoped to Ubuntu GNOME on Wayland and X11; Windows 11 remains a separately planned phase because this repository has no Windows layout artifact yet.
