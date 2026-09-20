# Repair and recovery validation

Passed locally: bounded XKB and XML duplicate repair; unrelated-byte preservation; malformed
shared-file refusal; real Linux update and missing-registration repair using native compilation;
portable macOS partial-bundle/duplicate/conflicting-identity/trusted-receipt checks; reverse-order
restoration; external-edit refusal; interrupted apply and interrupted restoration; symlink swaps;
lock contention; retained bytes and file modes; source/snapshot race rejection; failed rollback
returning exit 5; and read-only recovery previews.

Commands: `uv run --locked pytest tests/unit/test_transaction.py tests/unit/test_privileged.py
 tests/integration/test_linux_repair.py tests/integration/test_macos_repair.py
 tests/integration/test_recovery.py tests/integration/test_transaction_failures.py
 tests/contract/test_recover.py`.

All destinations were temporary. Native Linux transcripts and timings are in us3.md and
performance.md. Portable macOS fixtures do not establish native macOS compatibility. Native
macOS repair/recovery evidence remains pending; T036 remains open.
