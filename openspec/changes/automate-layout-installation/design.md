# Design

## Context

The repository contains one macOS `.bundle`, one XKB symbols section, and a small XKB XML variant fragment. The README currently asks Linux users to edit `/usr/share/X11/xkb` manually and suggests restarting the display manager. No release packaging, installer, or CI workflow exists. The specs in this change cover macOS and Ubuntu GNOME on both session types; Windows 11 is a later implementation phase.

## Goals / Non-Goals

**Goals:**
- Keep end-user entry points short and implementation in small native scripts.
- Use one Ubuntu GNOME installation layout that both X11 and Wayland can discover, avoiding divergent installed versions.
- Make install, update, uninstall, and CI verification repeatable.

**Non-Goals:**
- Automate GNOME or macOS Settings clicks or forcibly replace the active input source.
- Support every Linux distribution or desktop environment in this change.
- Ship a Windows layout installer in this change.

## Decisions

### Distribution and script languages

Publish versioned release ZIP archives containing the relevant layout asset, a short installer entry point, removal entry point, and instructions. The macOS entry point is a shell script usable from Terminal or Finder; Ubuntu uses Bash plus Ubuntu's existing system tools. Ubuntu's Python 3 standard library validates XML without a third-party dependency. Avoid a cross-platform installer framework. A repository checkout remains usable for development.

### macOS installation

Copy the existing bundle into `~/Library/Keyboard Layouts` for the current user. Check the source bundle before changing the destination, replace only the project's matching bundle on updates, and remove only that bundle on uninstall. Print the Input Sources activation path and any needed sign-out/sign-in instruction. Do not write macOS preference databases to select it automatically; that is more fragile than a brief Settings step.

### Ubuntu GNOME XKB registration

Use one dedicated XKB layout file with a unique layout identifier and a matching registry entry with Bulgarian language metadata, instead of appending a variant to the distro's `bg` symbols file. Install into the system XKB root used by Ubuntu GNOME and X11 so both sessions see the same layout. The installer obtains administrator privileges only for required system writes, inserts a uniquely identifiable registry entry, detects prior installs, and checks the resulting data. Uninstall removes only the managed symbols file and registry entry. Preserve a backup of any touched system registry file and restore it if installation fails partway through. Document that an `xkeyboard-config` package update can replace registration and may require reinstalling. Do not restart the display manager; tell the user to sign out and back in if GNOME does not show the new source immediately.

The alternative user-level `~/.config/xkb` path is attractive for Wayland clients, but X11-only sessions cannot rely on it, and GNOME layout discovery may not use that registry path consistently. A single system registration is therefore simpler for the agreed Ubuntu GNOME target, despite requiring `sudo` and careful edits to a package-owned XML file. The implementation must validate actual GNOME discovery on both session types; compiling XKB alone is insufficient.

### CI and release verification

Use pinned GitHub runner labels such as `ubuntu-24.04` and `macos-15` rather than `-latest`. On Ubuntu, validate registry XML and compile the layout with XKB tooling, then start Xvfb and check representative keysyms through the installed X11 keymap. Run install, repeat install, and uninstall assertions in a disposable runner. On macOS, validate bundle metadata and layout data, then test install, repeat install, and removal in the runner's user home. Release archives should be built and exercised by these jobs so CI tests the user download contents, not only repository paths.

Headless CI does not prove that GNOME Wayland lists the source or that the macOS GUI can select it. Maintain a short release checklist with a GNOME Wayland session, a GNOME X11 session, and a logged-in macOS session. Each checks discovery, selection, and representative typing. Record the OS/session used when performing the checks.

### Later Windows 11 phase

A separate change should create a native Windows keyboard-layout source and installer, compare its mapping against the existing layout, and test install/reinstall/uninstall plus actual typing. The standard `windows-2025` GitHub runner is Windows Server 2025, so it can supply a packaging sanity check but cannot certify Windows 11. Use a Windows 11 x64 desktop runner or a controlled self-hosted Windows 11 x64 machine for release validation; `windows-11-arm` is useful additional coverage only if an ARM64 installer is built. Keep the Windows artifact and CI job out of this change until that layout exists.

## Risks / Trade-offs

- System XKB registry edits can be overwritten by Ubuntu package updates -> make reinstall idempotent, detect missing registration, and document recovery.
- Registry format or paths can differ across Ubuntu versions -> target Ubuntu 24.04 first, detect the actual installed XKB root, validate before and after changes, and test Ubuntu 26.04 separately before claiming it supported.
- Layout data differs between macOS and XKB -> maintain representative mapping checks and a manual typing checklist; a shared generated source is unnecessary unless drift becomes frequent.
- Hosted CI lacks the actual user desktop -> clearly separate automated checks from release smoke tests and avoid claiming headless checks prove GUI activation.

## Migration Plan

Ship installers and archives alongside existing layout assets, replace README instructions with the supported paths, and leave a manual recovery note for users who previously edited Ubuntu vendor files. Do not automatically delete unknown edits from earlier manual installations. A failed installation restores its own changes; users can run the documented uninstall or reinstall command to recover.
