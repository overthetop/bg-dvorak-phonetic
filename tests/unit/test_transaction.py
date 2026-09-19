from dataclasses import replace

import pytest

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.models import Action, ChangePlan, FileOperation, PlatformContext
from bg_dvorak_phonetic.transaction import Transaction, scope_lock
from bg_dvorak_phonetic.workflow import digest


@pytest.fixture
def transaction_case(tmp_path):
    destination = tmp_path / "dest"
    destination.mkdir()
    target = destination / "layout"
    target.write_bytes(b"original")
    source = tmp_path / "new"
    source.write_bytes(b"new")
    ctx = PlatformContext(
        "test", "1", "test", "none", "user", tmp_path, (destination,), tmp_path / "state"
    )
    operation = FileOperation("replace", target, digest(target), digest(source), source)
    plan = ChangePlan("test", "user", Action.UPDATE, operations=(operation,))
    return ctx, plan, target


def test_apply_backup_and_restore(transaction_case):
    ctx, plan, target = transaction_case
    engine = Transaction()
    engine.apply(ctx, plan, lambda: None)
    assert target.read_bytes() == b"new"
    assert (ctx.state_root.stat().st_mode & 0o777) == 0o700
    journal = ctx.state_root / plan.run_id / "journal.json"
    assert journal.stat().st_mode & 0o777 == 0o600
    engine.restore(ctx, plan.run_id)
    assert target.read_bytes() == b"original"


def test_verification_failure_restores(transaction_case):
    ctx, plan, target = transaction_case

    def fail():
        raise RuntimeError("validator failure")

    with pytest.raises(RuntimeError):
        Transaction().apply(ctx, plan, fail)
    assert target.read_bytes() == b"original"


def test_external_edit_blocks_recovery(transaction_case):
    ctx, plan, target = transaction_case
    engine = Transaction()
    engine.apply(ctx, plan, lambda: None)
    target.write_bytes(b"other author")
    with pytest.raises(InstallerError) as error:
        engine.restore(ctx, plan.run_id)
    assert error.value.code == 5
    assert target.read_bytes() == b"other author"


def test_changed_snapshot_and_symlink_refused(transaction_case, tmp_path):
    ctx, plan, target = transaction_case
    target.write_bytes(b"external")
    with pytest.raises(InstallerError):
        Transaction().apply(ctx, plan, lambda: None)
    target.unlink()
    target.symlink_to(tmp_path / "outside")
    with pytest.raises(InstallerError):
        Transaction().apply(ctx, plan, lambda: None)


def test_noop_creates_no_state(transaction_case):
    ctx, plan, target = transaction_case
    Transaction().apply(ctx, replace(plan, action=Action.NOOP, operations=()), lambda: None)
    assert not ctx.state_root.exists()


def test_lock_contention_and_release(transaction_case):
    ctx, _, _ = transaction_case
    with scope_lock(ctx):
        with pytest.raises(InstallerError) as error:
            with scope_lock(ctx):
                pass
        assert error.value.code == 4
    with scope_lock(ctx):
        pass


def test_pending_inspection_is_read_only(transaction_case):
    ctx, _, _ = transaction_case
    assert Transaction().pending(ctx) == ()
    assert not ctx.state_root.exists()


def test_reject_arbitrary_recovery_id(transaction_case):
    ctx, _, _ = transaction_case
    with pytest.raises((InstallerError, ValueError)):
        Transaction().restore(ctx, "../elsewhere")


@pytest.mark.parametrize(
    "stage", ["before-backup", "after-backup", "before-apply", "after-apply", "before-commit"]
)
def test_fault_boundaries_restore_original(transaction_case, stage):
    ctx, plan, target = transaction_case

    def fault(where, index):
        if where == stage:
            raise OSError("injected disk failure")

    with pytest.raises(OSError):
        Transaction(fault=fault).apply(ctx, plan, lambda: None)
    assert target.read_bytes() == b"original"
    assert Transaction().pending(ctx) == ()


def test_interruption_and_failed_rollback_returns_five(transaction_case):
    ctx, plan, target = transaction_case

    def fault(where, index):
        if where == "after-apply":
            raise KeyboardInterrupt()
        if where == "before-restore":
            raise OSError("restore denied")

    with pytest.raises(InstallerError) as error:
        Transaction(fault=fault).apply(ctx, plan, lambda: None)
    assert error.value.code == 5
    assert Transaction().pending(ctx) == (plan.run_id,)
    Transaction().restore(ctx, plan.run_id)
    assert target.read_bytes() == b"original"


def test_bundle_displacement_recovery(transaction_case, tmp_path):
    ctx, plan, target = transaction_case
    target.unlink()
    target.mkdir()
    (target / "asset").write_bytes(b"original")
    candidate = tmp_path / "bundle"
    candidate.mkdir()
    (candidate / "asset").write_bytes(b"new")
    op = FileOperation("replace", target, digest(target), digest(candidate), candidate)
    plan = replace(plan, operations=(op,))

    def fault(where, index):
        if where == "after-displace":
            raise OSError("rename interrupted")

    with pytest.raises(OSError):
        Transaction(fault=fault).apply(ctx, plan, lambda: None)
    assert (target / "asset").read_bytes() == b"original"


def test_journal_schema_and_permissions_refused(transaction_case):
    ctx, plan, target = transaction_case
    engine = Transaction()
    engine.apply(ctx, plan, lambda: None)
    journal = ctx.state_root / plan.run_id / "journal.json"
    journal.chmod(0o666)
    with pytest.raises(InstallerError):
        engine.restore(ctx, plan.run_id)
    journal.chmod(0o600)
    journal.write_text(journal.read_text().replace('"schema_version": 1', '"schema_version": 99'))
    with pytest.raises(InstallerError):
        engine.restore(ctx, plan.run_id)
    assert target.read_bytes() == b"new"


def test_injected_filesystem_write_failure_restores(transaction_case):
    from bg_dvorak_phonetic.transaction import LocalFileSystem

    ctx, plan, target = transaction_case

    class FailingFileSystem(LocalFileSystem):
        def replace(self, source, destination):
            if destination == target and source.name.endswith("-stage"):
                raise OSError("injected replacement failure")
            super().replace(source, destination)

    with pytest.raises(OSError):
        Transaction(filesystem=FailingFileSystem()).apply(ctx, plan, lambda: None)
    assert target.read_bytes() == b"original"


def test_symlink_swap_does_not_write_outside_scope(transaction_case, tmp_path):
    ctx, plan, target = transaction_case
    outside = tmp_path / "outside"
    outside.write_bytes(b"do not change")

    def swap(stage, index):
        if stage == "before-apply":
            target.unlink()
            target.symlink_to(outside)

    with pytest.raises(InstallerError) as error:
        Transaction(fault=swap).apply(ctx, plan, lambda: None)
    assert error.value.code == 5
    assert outside.read_bytes() == b"do not change"
    assert (ctx.state_root / plan.run_id / "original-0").read_bytes() == b"original"


def test_original_file_mode_is_restored(transaction_case):
    ctx, plan, target = transaction_case
    target.chmod(0o640)
    engine = Transaction()
    engine.apply(ctx, plan, lambda: None)
    assert target.stat().st_mode & 0o777 == 0o640
    engine.restore(ctx, plan.run_id)
    assert target.stat().st_mode & 0o777 == 0o640


def test_failed_initial_journal_allows_safe_retry(transaction_case):
    from bg_dvorak_phonetic.models import new_id
    from bg_dvorak_phonetic.transaction import LocalFileSystem

    ctx, plan, target = transaction_case

    class NoJournalFileSystem(LocalFileSystem):
        def replace(self, source, destination):
            if destination.name == "journal.json":
                raise OSError("journal storage full")
            super().replace(source, destination)

    with pytest.raises(OSError):
        Transaction(filesystem=NoJournalFileSystem()).apply(ctx, plan, lambda: None)
    assert target.read_bytes() == b"original"
    Transaction().apply(ctx, replace(plan, run_id=new_id()), lambda: None)
    assert target.read_bytes() == b"new"


def test_explicit_recovery_failure_is_exit_five(transaction_case):
    ctx, plan, target = transaction_case
    Transaction().apply(ctx, plan, lambda: None)

    def fail(stage, index):
        if stage == "after-remove-restore":
            raise OSError("restore disk failure")

    with pytest.raises(InstallerError) as error:
        Transaction(fault=fail).restore(ctx, plan.run_id)
    assert error.value.code == 5
    Transaction().restore(ctx, plan.run_id)
    assert target.read_bytes() == b"original"
