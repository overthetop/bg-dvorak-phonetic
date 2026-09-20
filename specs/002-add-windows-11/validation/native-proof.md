# Native desktop proof

Status: waived for implementation sequencing; Windows 11 Home/Pro compatibility remains unverified.

On 2026-09-20, the project owner explicitly accepted proceeding without the T011 interactive
Windows 11 25H2 Home/Pro x64 proof. The decision relies on the successful hosted Windows build and
probe-entry evidence in `native-build.md`, with the expectation that Windows Enterprise/Server
behavior is representative enough to continue implementation.

No Home/Pro desktop was exercised. Registration, Settings discovery, selection, Secure Boot policy,
x64 editor/browser input, 32-bit translated input, identity collision behavior, and restoration were
not observed. This waiver unblocks dependent implementation tasks; it is not positive compatibility
evidence and must remain visible in support and release documentation.
