from bg_dvorak_phonetic.cli import main


def test_recover_requires_id():
    import pytest

    with pytest.raises(SystemExit) as error:
        main(["recover"])
    assert error.value.code == 2


def test_workflow_recovery_preview_and_restore(prepared_adapter):
    from bg_dvorak_phonetic.workflow import execute

    adapter, context = prepared_adapter
    result = execute(adapter, context, yes=True)
    before = (context.state_root / result.run_id / "journal.json").read_bytes()
    preview = execute(adapter, context, command="recover", recovery_id=result.run_id, dry_run=True)
    assert preview.action == "unchanged"
    assert (context.state_root / result.run_id / "journal.json").read_bytes() == before
    restored = execute(adapter, context, command="recover", recovery_id=result.run_id, yes=True)
    assert restored.action == "restored"
    assert not adapter.target.exists()
