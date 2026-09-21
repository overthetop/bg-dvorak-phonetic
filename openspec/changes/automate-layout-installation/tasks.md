# Tasks

## 1. Layout assets and installers

- [x] 1.1 Prepare a dedicated Ubuntu XKB layout and registry entry from the current mapping; verify both compile and retain representative Cyrillic and punctuation keys.
- [x] 1.2 Implement the macOS install and uninstall entry points for the current-user bundle; verify install, repeat install, and removal in a temporary home directory.
- [x] 1.3 Implement the Ubuntu GNOME install and uninstall entry points with ownership checks, registry validation, and recovery on partial failure; verify repeat install leaves one registration and uninstall preserves unrelated registry entries.
- [x] 1.4 Add explicit unsupported-environment and failed-write messages to both installers; verify each exits unsuccessfully when a required input or destination is unavailable.

## 2. Distribution and documentation

- [x] 2.1 Build versioned macOS and Ubuntu release archives containing the layout, install and removal entry points, and short instructions; verify installation works from extracted archives without a repository checkout.
- [x] 2.2 Replace README installation steps with download, install, activation, and removal instructions for macOS and Ubuntu GNOME; verify commands and paths against the produced archives.
- [x] 2.3 Add a release smoke-test checklist for GNOME Wayland, GNOME X11, and macOS that covers layout discovery, selection, and representative typing; verify the checklist records OS and session results and distinguishes them from CI evidence.
- [x] 2.4 Document the later Windows 11 native-layout artifact, installer lifecycle, and x64 desktop test environment; verify the document identifies Windows Server CI as a packaging check rather than Windows 11 compatibility proof.

## 3. Automated verification

- [x] 3.1 Add an Ubuntu 24.04 GitHub Actions job that builds the release archive and checks install, repeat install, uninstall, registry validity, and XKB compilation; verify the job passes and fails when the registry entry is deliberately invalidated.
- [x] 3.2 Add an Xvfb-based X11 check for representative installed key mappings; verify it passes for the intended layout and fails for an intentionally changed key.
- [x] 3.3 Add a macOS GitHub Actions job that builds the release archive, validates bundle metadata, and checks install, repeat install, and uninstall; verify the job passes and fails when the bundle is missing or malformed.
- [x] 3.4 Run the complete workflow on a pull request or test branch and verify both platform jobs and their logs clearly identify the checks performed.
