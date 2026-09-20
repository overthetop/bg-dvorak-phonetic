import os
from pathlib import Path

import pytest

from bg_dvorak_phonetic.models import RegistrySnapshot
from bg_dvorak_phonetic.resources import (
    Observation,
    PosixResourceBackend,
    Reconciliation,
)


def test_posix_backend_snapshot_stage_apply_verify_restore(tmp_path):
    backend = PosixResourceBackend()
    destination = tmp_path / "installed"
    staged = tmp_path / "staged"
    staged.write_bytes(b"new")

    before = backend.snapshot_file(destination)
    assert before.exists is False

    prepared = backend.stage_file(staged, tmp_path / "work")
    assert prepared.read_bytes() == b"new"
    backend.apply_file(prepared, destination)
    after = backend.snapshot_file(destination)
    assert after.exists is True
    assert backend.verify_file(destination, after)

    backend.restore_file(destination, before)
    assert not destination.exists()


def test_reconciliation_distinguishes_before_after_and_third_state():
    before = Observation(False, None, None)
    after = Observation(True, "a" * 64, None)
    assert Reconciliation.classify(before, before, after) == Reconciliation.BEFORE
    assert Reconciliation.classify(after, before, after) == Reconciliation.AFTER
    third = Observation(True, "b" * 64, None)
    assert Reconciliation.classify(third, before, after) == Reconciliation.THIRD


def test_registry_resources_remain_typed():
    snapshot = RegistrySnapshot(exists=True, values=())
    assert snapshot.exists
    with pytest.raises(TypeError):
        PosixResourceBackend().snapshot_registry(Path("/registry/is/not/a/path"))


@pytest.mark.skipif(os.name == "nt", reason="POSIX native lock")
def test_lock_and_storage_are_injected_boundaries(tmp_path):
    backend = PosixResourceBackend()
    state = tmp_path / "state"
    state.mkdir()
    with backend.acquire_lock(state):
        backend.store_record(state, "journal", b"record")
    assert backend.load_record(state, "journal") == b"record"


def test_restore_refuses_third_state(tmp_path):
    backend = PosixResourceBackend()
    destination = tmp_path / "installed"
    destination.write_bytes(b"before")
    before = backend.snapshot_file(destination)
    destination.write_bytes(b"after")
    after = backend.snapshot_file(destination)
    destination.write_bytes(b"external")
    with pytest.raises(ValueError, match="third"):
        backend.reconcile_file(destination, before, after)
