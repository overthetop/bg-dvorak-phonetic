# Later Windows 11 phase

This repository does not yet contain a Windows keyboard layout or installer. A separate change should create a native Windows layout source, generate an installable package, and compare representative key mappings with the existing Linux and macOS layouts. Use a Windows-native layout tool or build process; the XKB and macOS files cannot be installed directly as Windows layouts.

The Windows phase should test first install, repeat install, uninstall, layout selection, and actual typing, including Shift and punctuation. Automate packaging checks on a standard GitHub `windows-2025` runner if useful, but label those as **Windows Server 2025** checks. Validate Windows 11 x64 on a Windows 11 desktop runner or a controlled self-hosted Windows 11 x64 machine before claiming support. Add Windows 11 ARM64 coverage only if an ARM64 package is shipped.
