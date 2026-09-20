# Hosted native build evidence

Status: passed for T008–T010 build and probe-entry scope; pending for desktop typing.

## Candidate

- Source revision: `095c3941f79ed4837f3e4834f58044f906283015`
- Workflow run: <https://github.com/overthetop/bg-dvorak-phonetic/actions/runs/35496313493>
- Runner: GitHub-hosted `windows-11-arm`, Windows 11 Enterprise ARM64, build 26200
- Product target: x64 Windows layout DLL, cross-built with the locked x64 MSVC/SDK/WDK inputs
- Toolchain metadata: `validation/hosted-native-build/pinned-toolchain.json`
- Environment metadata: `validation/hosted-native-build/environment.json`

## Results

The workflow built the layout twice from clean output directories. Both outputs had SHA-256
`196e0f17ae452d2d038f45bb0ba7c490984863895cf61312b108bb9632968931`.
The checked-in manifest names that content-addressed DLL and records the mapping, source, and
toolchain hashes. `tools/validate_windows_layout.py` accepted its schema, hashes, PE x64 machine,
resource metadata, and `KbdLayerDescriptor` export.

The workflow also built and executed the bounded probe `--self-test` mode:

- x64 probe SHA-256: `ca25e83392d167cd1657d8906e5a9d242dbf46a834406917fb712221b91ca43a`
- x86 probe SHA-256: `9cefad435abf28232aba76f92efe12e64050ca0bbc9175847c43c9eeae82347b`
- x64 log reports `process_bits: 64`; x86 log reports `process_bits: 32`
- Both logs contain successful `start` and `finish` events

The probe executables are test products and are not included in `windows/assets/`. Their logs and
hashes are retained under `validation/hosted-native-build/`.

## Scope and limitation

This evidence proves deterministic native asset construction, offline validation, and x64/x86
probe startup. The hosted runner is Enterprise ARM64 and has no interactive Windows desktop, so it
does not prove Windows 11 25H2 Home/Pro x64 registration, Settings discovery, Secure Boot behavior,
layout selection, or translated typing in editor, browser, and 32-bit applications. T011 remains
pending until those checks run on snapshotted Home and Pro x64 desktops and restoration is recorded.
