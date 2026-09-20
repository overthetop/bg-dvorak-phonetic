import shutil
import subprocess

import pytest

from bg_dvorak_phonetic import cli


@pytest.mark.parametrize("command", [["status"], ["install", "--dry-run"], ["install", "--yes"]])
def test_documented_commands_in_isolation(prepared_adapter, monkeypatch, capsys, command):
    adapter, context = prepared_adapter
    monkeypatch.setattr(cli, "get_adapter", lambda name: adapter)
    monkeypatch.setattr(adapter, "probe", lambda scope: context)
    assert cli.main(command) == 0
    assert "activation=pending" in capsys.readouterr().out
    assert adapter.target.exists() is (command == ["install", "--yes"])


def test_offline_uv_launch_from_foreign_cwd(project_root, tmp_path):
    uv = shutil.which("uv")
    assert uv is not None
    result = subprocess.run(
        [
            uv,
            "run",
            "--project",
            str(project_root),
            "--no-sync",
            "--no-python-downloads",
            "--offline",
            "bg-dvorak-phonetic",
            "--version",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0.1.0"


def test_missing_prepared_interpreter_never_creates_environment(project_root, tmp_path):
    for name in ("pyproject.toml", ".python-version", "uv.lock"):
        shutil.copy2(project_root / name, tmp_path / name)
    before = set(tmp_path.rglob("*"))
    result = subprocess.run(
        [
            shutil.which("uv"),
            "run",
            "--no-project",
            "--python",
            str(tmp_path / ".venv/bin/python"),
            "--no-python-downloads",
            "--offline",
            "bg-dvorak-phonetic",
            "status",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert set(tmp_path.rglob("*")) == before
