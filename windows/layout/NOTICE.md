# Native layout ABI reference and licensing

The ABI reference is Microsoft's Windows-driver-samples at immutable revision
`3c3fb49073c047c4cc8e6c203c6331f62b426507`, directory `input/layout/kbdus`.
The files were acquired and inspected on 2026-09-19. Exact raw acquisition URLs and SHA-256
hashes for kbdus.c, kbdus.h, kbdus.def, kbdus.rc and kbdus.vcxproj are recorded under
`upstream_reference.files` in `windows/toolchain.lock.json`.

The repository license is Microsoft Public License (MS-PL), copyright (c) 2015 Microsoft.
The complete original license is retained as [LICENSE.Microsoft](LICENSE.Microsoft).
The sample C/header files additionally retain copyright (c) 1985-2000, Microsoft Corporation.
The unmodified sample `kbdus.c` is retained in `reference/` with its locked hash. The generated
`bgdv.c` adapts its scan/navigation and key-name tables; changes are Dvorak virtual-key positions,
Bulgarian modifier/Caps levels, control-character handling and dead composition tables. Copyright
notices are retained in both the reference and generated source. Native typing proof is separate.

SDK/WDK packages are build inputs under their respective Microsoft terms, not redistributed
project source. The lock records exact NuGet IDs, versions, acquisition URLs, byte sizes and
SHA-256 values for SDK CPP, SDK CPP x64 and WDK x64 version 10.0.26100.6584. Their nuspec
metadata was checked against the requested version. Tool acquisition is a maintainer/CI step;
product install/status/recover must never download or compile assets.
