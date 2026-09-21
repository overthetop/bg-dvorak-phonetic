# Spec Delta

## Purpose

Provide a short, repeatable way for users to install and remove the Bulgarian Dvorak phonetic keyboard layout on the supported desktop systems.

## ADDED Requirements

### Requirement: macOS installation
The project SHALL provide a downloadable installation entry point that installs the supplied keyboard layout bundle for the current macOS user without requiring Git or administrator access, and SHALL tell the user how to enable the input source.

#### Scenario: Install on macOS
- **WHEN** a user runs the installer from the downloaded release
- **THEN** the layout bundle is available in the current user's Keyboard Layouts directory and the user receives the steps needed to select it in Input Sources

### Requirement: Ubuntu GNOME installation
The project SHALL provide a downloadable installation entry point that makes the layout selectable in Ubuntu GNOME on both Wayland and X11, without requiring the user to edit XKB files manually or restart the display manager.

#### Scenario: Install on GNOME Wayland
- **WHEN** a user installs the layout on a supported Ubuntu GNOME Wayland system and follows the reported session refresh steps
- **THEN** the layout is listed in GNOME Input Sources and produces the documented key mapping when selected

#### Scenario: Install on GNOME X11
- **WHEN** a user installs the layout on a supported Ubuntu GNOME X11 system and follows the reported session refresh steps
- **THEN** the layout is listed in GNOME Input Sources and produces the documented key mapping when selected

### Requirement: Safe repeat installation and removal
Installers SHALL be safe to rerun, SHALL avoid duplicate layout registrations, and SHALL provide a removal path that preserves unrelated user and system configuration.

#### Scenario: Repeat install
- **WHEN** a user runs an installer twice
- **THEN** one working copy and one registration of the layout remain

#### Scenario: Remove layout
- **WHEN** a user invokes the documented removal path
- **THEN** files and registration owned by this project are removed and unrelated layouts remain available

### Requirement: Clear failure behavior
Installers SHALL report unsupported environments, missing prerequisites, or unsuccessful writes without claiming installation succeeded.

#### Scenario: Failed install
- **WHEN** an installer cannot complete a required file or registration change
- **THEN** it exits unsuccessfully and identifies the failed step and any required recovery action
