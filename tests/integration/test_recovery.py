import pytest

from bg_dvorak_phonetic.models import Action, ChangePlan, FileOperation, PlatformContext
from bg_dvorak_phonetic.transaction import Transaction
from bg_dvorak_phonetic.workflow import digest


def test_two_file_failure_restores_in_reverse_order(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    candidate = tmp_path / "new"
    candidate.write_bytes(b"new")
    files = [target / "one", target / "two"]
    for path in files:
        path.write_bytes(path.name.encode())
    context = PlatformContext(
        "test", "1", "test", "", "user", tmp_path, (target,), tmp_path / "state"
    )
    operations = tuple(
        FileOperation("replace", path, digest(path), digest(candidate), candidate) for path in files
    )
    plan = ChangePlan("test", "user", Action.UPDATE, operations=operations)
    seen = []

    def fail(stage, index):
        if stage == "after-apply" and index == 1:
            raise OSError("disk full")
        if stage == "before-restore":
            seen.append(index)

    with pytest.raises(OSError):
        Transaction(fault=fail).apply(context, plan, lambda: None)
    assert seen == [1, 0]
    assert all(path.read_bytes() == path.name.encode() for path in files)
