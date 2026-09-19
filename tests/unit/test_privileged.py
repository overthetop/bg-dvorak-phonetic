import pytest

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.privileged import validate_request, worker_command
from bg_dvorak_phonetic.workflow import inventory, project_root


def request():
    return {
        "schema_version": 1,
        "action": "inspect",
        "source_hashes": dict(inventory(project_root()).manifest),
    }


def test_worker_accepts_only_closed_operations():
    validate_request(request())
    for extra in ({"destination": "/etc/passwd"}, {"command": ["sh"]}, {"root": "/tmp"}):
        with pytest.raises(InstallerError):
            validate_request(request() | extra)
    with pytest.raises(InstallerError):
        validate_request(request() | {"action": "execute"})


def test_worker_checks_source_and_schema():
    with pytest.raises(InstallerError):
        validate_request(request() | {"source_hashes": {}})
    with pytest.raises(InstallerError):
        validate_request(request() | {"schema_version": 2})


def test_transport_is_not_package_manager():
    command = worker_command(interactive=False)
    assert command[0:2] == ["sudo", "-n"]
    assert "-I" in command
    assert all(part not in ("uv", "pip", "sh", "bash") for part in command)


@pytest.mark.parametrize(
    "response,returncode,expected",
    [
        ('{"pending":[]}', 0, None),
        ("denied", 1, 3),
        ("[]", 0, 4),
        ('{"error":"denied","code":3,"remedy":"authorize"}', 3, 3),
    ],
)
def test_transport_classifies_responses(monkeypatch, response, returncode, expected):
    import subprocess

    from bg_dvorak_phonetic import privileged

    monkeypatch.setattr(
        privileged.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, returncode, response, ""),
    )
    if expected is None:
        assert privileged.invoke(request(), interactive=False) == {"pending": []}
    else:
        with pytest.raises(InstallerError) as error:
            privileged.invoke(request(), interactive=False)
        assert error.value.code == expected


def test_worker_inspection_and_denial_are_read_only(prepared_adapter, monkeypatch, capsys):
    import io
    import json

    from bg_dvorak_phonetic import platforms, privileged

    adapter, context = prepared_adapter
    monkeypatch.setattr(privileged.os, "geteuid", lambda: 0)
    monkeypatch.setattr(privileged.sys, "platform", "linux")
    monkeypatch.setattr(platforms, "get_adapter", lambda name: adapter)
    monkeypatch.setattr(adapter, "probe", lambda scope: context)
    monkeypatch.setattr(privileged.sys, "stdin", io.StringIO(json.dumps(request())))
    before = list(context.state_root.iterdir())
    assert privileged.worker_main() == 0
    assert json.loads(capsys.readouterr().out) == {"pending": []}
    assert list(context.state_root.iterdir()) == before
    monkeypatch.setattr(privileged.os, "geteuid", lambda: 1000)
    assert privileged.worker_main() == 3
    assert list(context.state_root.iterdir()) == before


def test_worker_apply_and_recover_with_injected_adapter(prepared_adapter, monkeypatch, capsys):
    import io
    import json

    from bg_dvorak_phonetic import platforms, privileged
    from bg_dvorak_phonetic.models import new_id
    from bg_dvorak_phonetic.workflow import inventory

    adapter, context = prepared_adapter
    monkeypatch.setattr(privileged.os, "geteuid", lambda: 0)
    monkeypatch.setattr(privileged.sys, "platform", "linux")
    monkeypatch.setattr(platforms, "get_adapter", lambda name: adapter)
    monkeypatch.setattr(adapter, "probe", lambda scope: context)
    monkeypatch.setattr(privileged, "project_root", lambda: context.project_root)
    assets = inventory(context.project_root)
    plan = adapter.plan(adapter.inspect(context), assets)
    run_id = new_id()
    payload = {
        "schema_version": 1,
        "action": "apply",
        "source_hashes": dict(assets.manifest),
        "observed_hashes": dict(plan.observed_hashes),
        "run_id": run_id,
    }
    monkeypatch.setattr(privileged.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert privileged.worker_main() == 0
    assert json.loads(capsys.readouterr().out)["run_id"] == run_id
    assert adapter.target.exists()
    payload = {
        "schema_version": 1,
        "action": "recover",
        "source_hashes": dict(assets.manifest),
        "run_id": run_id,
        "dry_run": True,
    }
    monkeypatch.setattr(privileged.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert privileged.worker_main() == 0
    assert adapter.target.exists()
    capsys.readouterr()
    payload["dry_run"] = False
    monkeypatch.setattr(privileged.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert privileged.worker_main() == 0
    assert not adapter.target.exists()


@pytest.mark.parametrize("interruption", ["timeout", "interrupt"])
def test_unknown_worker_mutation_outcome_requires_recovery(monkeypatch, interruption):
    import subprocess

    from bg_dvorak_phonetic import privileged
    from bg_dvorak_phonetic.models import new_id

    def fail(*args, **kwargs):
        if interruption == "timeout":
            raise subprocess.TimeoutExpired("worker", 120)
        raise KeyboardInterrupt()

    monkeypatch.setattr(privileged.subprocess, "run", fail)
    payload = request() | {"action": "apply", "observed_hashes": {}, "run_id": new_id()}
    with pytest.raises(InstallerError) as error:
        privileged.invoke(payload, interactive=False)
    assert error.value.code == 5


def test_internal_worker_subprocess_rejects_unapproved_request():
    import json
    import subprocess
    import sys
    from pathlib import Path

    from bg_dvorak_phonetic import privileged

    result = subprocess.run(
        [sys.executable, "-I", str(Path(privileged.__file__).resolve())],
        input="{}",
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode in (3, 4)
    assert json.loads(result.stdout)["code"] == result.returncode
