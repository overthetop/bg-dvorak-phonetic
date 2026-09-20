import pytest

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.models import Action, ChangePlan, FileOperation, PlatformContext
from bg_dvorak_phonetic.transaction import Transaction
from bg_dvorak_phonetic.workflow import digest


def test_recovery_after_interruption_during_restore(tmp_path):
    target_dir = tmp_path / "dest"
    target_dir.mkdir()
    target = target_dir / "file"
    target.write_bytes(b"original")
    source = tmp_path / "source"
    source.write_bytes(b"new")
    context = PlatformContext(
        "test", "1", "test", "", "user", tmp_path, (target_dir,), tmp_path / "state"
    )
    plan = ChangePlan(
        "test",
        "user",
        Action.UPDATE,
        operations=(FileOperation("replace", target, digest(target), digest(source), source),),
    )

    def fault(stage, index):
        if stage in ("after-apply", "after-remove-restore"):
            raise KeyboardInterrupt()

    with pytest.raises(InstallerError) as error:
        Transaction(fault=fault).apply(context, plan, lambda: None)
    assert error.value.code == 5
    Transaction().restore(context, plan.run_id)
    assert target.read_bytes() == b"original"


def test_source_race_has_no_mutations(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    candidate = tmp_path / "source"
    candidate.write_bytes(b"first")
    context = PlatformContext(
        "test", "1", "test", "", "user", tmp_path, (destination,), tmp_path / "state"
    )
    expected = digest(candidate)
    plan = ChangePlan(
        "test",
        "user",
        Action.INSTALL,
        operations=(FileOperation("create", destination / "file", None, expected, candidate),),
        source_hashes=(("source", expected),),
    )
    candidate.write_bytes(b"changed")
    with pytest.raises(InstallerError):
        Transaction().apply(context, plan, lambda: None)
    assert not (destination / "file").exists()
    assert not list(context.state_root.glob("*/journal.json"))
