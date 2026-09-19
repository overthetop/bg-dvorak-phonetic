# Fixture safety

Tests copy the authoritative `linux/` and `mac-os/` assets into pytest temporary directories.
`asset_checkout` includes spaces and Cyrillic characters; `isolated_roots` provides separate
XKB, user-layout, system-layout and recovery roots. Pass these roots explicitly to adapters;
never invoke a production installer against the host to test mutations.

`command_recorder` injects deterministic subprocess outcomes. Native integration tests must
instead use actual validators with temporary destinations; recorded commands alone do not
establish native compatibility. Fault tests inject failures at filesystem/process boundaries.
