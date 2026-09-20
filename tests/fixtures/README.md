# Fixture safety

Tests copy the authoritative `linux/` and `mac-os/` assets into pytest temporary directories.
`asset_checkout` includes spaces and Cyrillic characters; `isolated_roots` provides separate
XKB, user-layout, system-layout and recovery roots. Pass these roots explicitly to adapters;
never invoke a production installer against the host to test mutations.

`command_recorder` injects deterministic subprocess outcomes. Native integration tests must
instead use actual validators with temporary destinations; recorded commands alone do not
establish native compatibility. Fault tests inject failures at filesystem/process boundaries.

## Windows resources

`windows_resources()` allocates its own temporary directory and yields a context that tests
can inject internally. File snapshots preserve bytes, absence and ordinary mode bits; they
do not claim to capture Windows ACLs. Only single regular filenames are accepted, with links,
reparse files, device names and paths outside the root rejected. `checkpoint(name)` calls an
optional injected fault hook. Context exit removes the allocated resources even after a failure.

On Windows, `windows_resources(registry=True)` additionally allocates a unique test-owned
HKCU Software leaf. Value snapshots preserve names, types, empty values and absence; child
keys are unsupported by snapshots. Cleanup removes the owned tree. No HKLM keyboard root or
production installer is used. On other hosts the registry request raises instead of mocking
Windows. The dedicated native test must run on Windows before native behavior is accepted.
These helpers are test scaffolding, not a substitute for production ACL/race defenses.
