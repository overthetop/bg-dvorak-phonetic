import io

from bg_dvorak_phonetic.diagnostics import Diagnostics
from bg_dvorak_phonetic.workflow import execute


def test_install_stage_order_and_actual_outcome(prepared_adapter):
    adapter, context = prepared_adapter
    output = io.StringIO()
    result = execute(adapter, context, yes=True, diagnostics=Diagnostics(stream=output))
    expected = [
        "preflight",
        "inspect",
        "plan",
        "authorize",
        "backup",
        "validate-staged",
        "apply",
        "verify-installed",
        "complete",
    ]
    stages = [line.split(" | ")[3] for line in output.getvalue().splitlines()]
    positions = [stages.index(stage) for stage in expected]
    assert positions == sorted(positions)
    assert result.action == "installed"
    assert result.activation_status == "pending"
    assert adapter.target.is_dir()
    assert "scope=user" in output.getvalue()
    assert "health=absent" in output.getvalue()


def test_dry_run_and_noop_do_not_create_backups(prepared_adapter):
    adapter, context = prepared_adapter
    assert not list(context.state_root.iterdir())
    execute(adapter, context, dry_run=True)
    assert not adapter.target.exists()
    assert not list(context.state_root.iterdir())
    execute(adapter, context, yes=True)
    before = sorted(context.state_root.iterdir())
    for _ in range(3):
        assert execute(adapter, context, yes=True).action == "unchanged"
    assert sorted(context.state_root.iterdir()) == before


def test_run_identifier_is_consistent(prepared_adapter):
    adapter, context = prepared_adapter
    stream = io.StringIO()
    result = execute(adapter, context, yes=True, diagnostics=Diagnostics(stream=stream))
    assert {line.split(" | ")[1] for line in stream.getvalue().splitlines()} == {result.run_id}
