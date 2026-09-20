# Fresh-install validation

Local environment: Ubuntu 24.04 x86_64, CPython 3.14.7, uv 0.12.16.

Passed: CLI/help/version contracts, support-matrix detection, mutation-free preview, isolated
native XKB fresh installation, verified base.xml alias preservation, copied real distro inputs,
three current-state inspections, and paths with spaces/Cyrillic characters. The native compiler
is Ubuntu libxkbcommon-tools 1.6.0-1build1 extracted under /tmp; a temporary dispatcher delegates
to its actual xkbcli-compile-keymap executable. No system package or live keyboard files changed.

Commands: `uv run --locked pytest tests/contract/test_cli.py tests/contract/test_platform_adapter.py
 tests/integration/test_linux_install.py tests/integration/test_macos_install.py`.

Native macOS test exists but is explicitly skipped on Linux. Its plutil/bundle installation and
all desktop typing evidence remain pending. T026 remains open until native macOS evidence exists.
