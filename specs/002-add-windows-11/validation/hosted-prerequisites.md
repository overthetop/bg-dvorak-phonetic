# Hosted Windows prerequisites — passed fixture checks

Run: https://github.com/overthetop/bg-dvorak-phonetic/actions/runs/35467757790
Commit: `c6c8cbb54b2559682b700a822abe5108b327a125` on `windows-prerequisites-ci`.
Date: 2026-09-19. Workflow conclusion: success. Only the workflow and two fixture/test files
were committed to the isolated branch; the remaining feature work stays in the local worktree.

| Runner | Observed OS | Result |
|---|---|---|
| windows-2025 | Windows Server 2025 Datacenter, build 26100, x64 | 12 passed, 1 skipped |
| windows-11-arm | Windows 11 Enterprise, build 26200, ARM64 | 12 passed, 1 skipped |

Both jobs ran locked Python 3.14.7/uv 0.12.16 and
`uv run --locked pytest -v tests/unit/test_windows_resources.py --junitxml=evidence/resources.xml`.
The skip is the non-Windows refusal test. Actual native registry restoration and cleanup passed
on both hosts. This supersedes the pending native fixture result in setup.md.

Raw environment records and JUnit reports are retained in hosted-prerequisites/ with SHA-256
checksums. Each environment record contains the runner image version, UTC timestamp, source
commit, installed Visual Studio and SDK inventory, and measured compiler/header hashes.
Workflow validation with actionlint 1.7.12 passed before publication.

The ARM runner has VS 2022 17.14.40; the x64 runner has VS 2026 18.9.2 with several installed
MSVC toolsets. Both expose MSVC 19.44.35228.0 and SDK include directory 10.0.26100.0.
An include directory name does not establish SDK/WDK servicing package version 26100.6584.
Acquisition provenance, package versions, linker/MSBuild lock and sample licensing are still
incomplete, so T002 remains pending and build_ready remains false.

These are resource fixture tests, not layout builds, installed-layout typing, UAC/recovery
acceptance or the five-job release aggregate. Windows 11 Enterprise ARM64 does not establish
Home/Pro x64 compatibility or expand the product architecture scope. No layout was registered.
